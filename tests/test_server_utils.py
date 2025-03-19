"""
Tests for server utilities and error handling
"""
import os
import pytest
import platform
import subprocess
import time
import signal
import psutil
from unittest.mock import patch, MagicMock

from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.process import (
    ProcessError, 
    ProcessNotFoundError,
    ProcessKillError,
    ProcessAccessDeniedError,
    ProcessTimeoutError
)
from management.server_utils import find_server_pid, kill_process
from management.pid_utils import save_pid, get_pid


@pytest.fixture
def error_context():
    """Create test error context"""
    return ErrorContext(
        operation="server_management",
        severity=ErrorSeverity.ERROR
    )


@pytest.fixture
def setup_pid_env(temp_dir, monkeypatch):
    """Setup environment for PID-related tests"""
    # Save original working directory
    original_cwd = os.getcwd()
    
    # Change to the temporary directory
    os.chdir(temp_dir)
    
    # Create .pids directory
    os.makedirs('.pids', exist_ok=True)
    
    # Return control after test setup
    yield
    
    # Restore original working directory
    os.chdir(original_cwd)


@pytest.mark.usefixtures("setup_pid_env")
def test_find_server_pid_no_process(monkeypatch, error_context):
    """Test finding server PID when no process is running"""
    def mock_check_output(*args, **kwargs):
        error_context.additional_data = {"command": args[0]}
        raise subprocess.CalledProcessError(1, 'netstat')
    
    monkeypatch.setattr('management.server_utils.subprocess.check_output', mock_check_output)
    
    with pytest.raises(ProcessNotFoundError) as exc_info:
        pid = find_server_pid('backend')
        
    assert exc_info.value.error_context.operation == "server_management"
    assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
    assert "command" in exc_info.value.error_context.additional_data


@pytest.mark.usefixtures("setup_pid_env")
def test_find_server_pid_from_pid_file(monkeypatch, error_context):
    """Test finding server PID from PID file"""
    def mock_check_output(*args, **kwargs):
        error_context.additional_data = {"command": args[0]}
        raise subprocess.CalledProcessError(1, 'netstat')
    
    monkeypatch.setattr('management.server_utils.subprocess.check_output', mock_check_output)
    monkeypatch.setattr('management.server_utils.is_process_running', lambda pid: True)
    monkeypatch.setattr('management.server_utils.get_pid', lambda server_type: 12345)
    
    try:
        pid = find_server_pid('backend')
        assert pid == 12345
    except ProcessError as e:
        assert e.error_context.operation == "server_management"
        assert e.error_context.severity == ErrorSeverity.ERROR
        pytest.fail("Should not raise ProcessError when PID file exists")


@pytest.mark.parametrize("server_type,port", [
    ("backend", 8080),
    ("frontend", 3000),
])
def test_find_server_pid_by_port(monkeypatch, server_type, port, error_context):
    """Test finding server PID by port for different server types"""
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    
    def mock_check_output(*args, **kwargs):
        error_context.additional_data = {
            "server_type": server_type,
            "port": port,
            "command": args[0]
        }
        return f"  TCP    0.0.0.0:{port}           0.0.0.0:0              LISTENING       54321\n".encode()
    
    monkeypatch.setattr('management.server_utils.subprocess.check_output', mock_check_output)
    monkeypatch.setattr('management.server_utils.is_process_running', lambda pid: True)
    
    try:
        pid = find_server_pid(server_type)
        assert pid == 54321
    except ProcessError as e:
        assert e.error_context.operation == "server_management"
        assert e.error_context.severity == ErrorSeverity.ERROR
        pytest.fail(f"Should not raise ProcessError when finding PID for {server_type}")


@pytest.mark.parametrize("marker_pid,server_type", [
    (99999, "frontend"),
    (88888, "backend"),
])
def test_find_server_pid_marker(monkeypatch, marker_pid, server_type):
    """Test handling of marker PIDs for external windows"""
    monkeypatch.setattr('management.server_utils.get_pid', lambda s: marker_pid)
    monkeypatch.setattr('management.server_utils.is_process_running', lambda pid: True)
    
    pid = find_server_pid(server_type)
    assert pid == marker_pid


def test_kill_process(monkeypatch, error_context):
    """Test killing a process"""
    process_mock = MagicMock()
    
    class MockProcess:
        def __init__(self, pid):
            error_context.additional_data = {"pid": pid}
            
        def terminate(self):
            process_mock.terminate()
            
        def wait(self, timeout=None):
            process_mock.wait(timeout)
            return True
            
        def kill(self):
            process_mock.kill()
    
    monkeypatch.setattr('management.server_utils.psutil.Process', MockProcess)
    monkeypatch.setattr('management.server_utils.psutil.pid_exists', lambda pid: True)
    
    try:
        result = kill_process(12345)
        assert result is True
        process_mock.terminate.assert_called_once()
        process_mock.wait.assert_called_once()
    except ProcessKillError as e:
        assert e.error_context.operation == "server_management"
        assert e.error_context.severity == ErrorSeverity.ERROR
        pytest.fail("Should not raise ProcessKillError on successful termination")


def test_kill_process_marker_pid():
    """Test attempting to kill marker PIDs"""
    # Test frontend marker PID
    assert kill_process(99999) is False
    
    # Test backend marker PID
    assert kill_process(88888) is False


def test_kill_process_force(monkeypatch, error_context):
    """Test force killing a process that doesn't terminate gracefully"""
    process_mock = MagicMock()
    
    class MockProcess:
        def __init__(self, pid):
            error_context.additional_data = {"pid": pid}
            
        def terminate(self):
            process_mock.terminate()
            
        def wait(self, timeout=None):
            process_mock.wait(timeout)
            raise psutil.TimeoutExpired(1)
            
        def kill(self):
            process_mock.kill()
    
    monkeypatch.setattr('management.server_utils.psutil.Process', MockProcess)
    monkeypatch.setattr('management.server_utils.psutil.pid_exists', lambda pid: True)
    
    try:
        result = kill_process(12345)
        assert result is True
        process_mock.terminate.assert_called_once()
        process_mock.kill.assert_called_once()
    except ProcessTimeoutError as e:
        assert e.error_context.operation == "server_management"
        assert e.error_context.severity == ErrorSeverity.ERROR
        pytest.fail("Should not raise ProcessTimeoutError when force kill succeeds")


@pytest.mark.parametrize("platform_name", ["Windows", "Linux", "Darwin"])
def test_kill_process_platform_specific(monkeypatch, platform_name, error_context):
    """Test platform-specific process killing"""
    monkeypatch.setattr(platform, "system", lambda: platform_name)
    
    def mock_access_denied(*args, **kwargs):
        error_context.additional_data = {
            "platform": platform_name,
            "pid": args[0] if args else None
        }
        raise psutil.AccessDenied()
    
    monkeypatch.setattr('management.server_utils.psutil.Process', mock_access_denied)
    monkeypatch.setattr('management.server_utils.psutil.pid_exists', lambda pid: True)
    
    try:
        if platform_name == "Windows":
            mock_run = MagicMock()
            monkeypatch.setattr('management.server_utils.subprocess.run', mock_run)
            result = kill_process(12345)
            assert result is True
            mock_run.assert_called_once_with(
                ["taskkill", "/F", "/PID", "12345"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            mock_kill = MagicMock()
            monkeypatch.setattr('os.kill', mock_kill)
            result = kill_process(12345)
            assert result is True
            mock_kill.assert_called_once_with(12345, signal.SIGKILL)
    except ProcessAccessDeniedError as e:
        assert e.error_context.operation == "server_management"
        assert e.error_context.severity == ErrorSeverity.ERROR
        assert "platform" in e.error_context.additional_data
        pytest.fail(f"Should not raise ProcessAccessDeniedError on {platform_name}")


def test_kill_process_cleanup_failure(monkeypatch, error_context):
    """Test handling of process cleanup failures"""
    def mock_process(*args, **kwargs):
        error_context.additional_data = {"pid": args[0] if args else None}
        raise psutil.NoSuchProcess(12345)
    
    monkeypatch.setattr('management.server_utils.psutil.Process', mock_process)
    
    try:
        assert kill_process(12345) is True
    except ProcessNotFoundError as e:
        assert e.error_context.operation == "server_management"
        assert e.error_context.severity == ErrorSeverity.ERROR
        pytest.fail("Should not raise ProcessNotFoundError when process is already gone")


def test_kill_process_unexpected_error(monkeypatch, error_context):
    """Test handling of unexpected errors during process termination"""
    def mock_process(*args, **kwargs):
        error_context.additional_data = {"pid": args[0] if args else None}
        raise RuntimeError("Unexpected error")
    
    monkeypatch.setattr('management.server_utils.psutil.Process', mock_process)
    monkeypatch.setattr('management.server_utils.psutil.pid_exists', lambda pid: True)
    
    with pytest.raises(ProcessError) as exc_info:
        kill_process(12345)
    
    assert exc_info.value.error_context.operation == "server_management"
    assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
    assert "pid" in exc_info.value.error_context.additional_data


@pytest.mark.asyncio
async def test_concurrent_process_operations(monkeypatch, error_context):
    """Test concurrent process operations"""
    import asyncio
    
    process_mock = MagicMock()
    
    class MockProcess:
        def __init__(self, pid):
            error_context.additional_data = {"pid": pid}
            
        def terminate(self):
            process_mock.terminate()
            
        def wait(self, timeout=None):
            process_mock.wait(timeout)
            return True
            
        def kill(self):
            process_mock.kill()
    
    monkeypatch.setattr('management.server_utils.psutil.Process', MockProcess)
    monkeypatch.setattr('management.server_utils.psutil.pid_exists', lambda pid: True)
    
    async def kill_concurrent():
        try:
            result = kill_process(12345)
            assert result is True
        except ProcessError as e:
            assert e.error_context.operation == "server_management"
            assert e.error_context.severity == ErrorSeverity.ERROR
            pytest.fail("Should not raise ProcessError during concurrent operations")
    
    await asyncio.gather(*[kill_concurrent() for _ in range(5)])
    assert process_mock.terminate.call_count == 5 
"""
Tests for server utilities
"""
import os
import pytest
import platform
import subprocess
import time
import signal
from unittest.mock import patch, MagicMock

# Import is handled by conftest.py, so we don't need the sys.path modification

from management.server_utils import find_server_pid, kill_process
from management.pid_utils import save_pid, get_pid


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
def test_find_server_pid_no_process(monkeypatch):
    """Test finding server PID when no process is running"""
    # Mock subprocess.check_output to raise an exception (no process found)
    def mock_check_output(*args, **kwargs):
        raise subprocess.CalledProcessError(1, 'netstat')
    
    monkeypatch.setattr('management.server_utils.subprocess.check_output', mock_check_output)
    
    # Try to find a server PID
    pid = find_server_pid('backend')
    
    # Should return None since no process is running
    assert pid is None


@pytest.mark.usefixtures("setup_pid_env")
def test_find_server_pid_from_pid_file(monkeypatch):
    """Test finding server PID from PID file"""
    # Mock subprocess.check_output to raise an exception (no process found)
    def mock_check_output(*args, **kwargs):
        raise subprocess.CalledProcessError(1, 'netstat')
    
    monkeypatch.setattr('management.server_utils.subprocess.check_output', mock_check_output)
    
    # Mock is_process_running to return True
    monkeypatch.setattr('management.server_utils.is_process_running', lambda pid: True)
    
    # Mock get_pid to return our fake PID
    monkeypatch.setattr('management.server_utils.get_pid', lambda server_type: 12345)
    
    # Try to find a server PID
    pid = find_server_pid('backend')
    
    # Should return the PID from the file
    assert pid == 12345


def test_kill_process(monkeypatch):
    """Test killing a process"""
    # Mock psutil.Process
    process_mock = MagicMock()
    
    # Create a mock class that can be called with a PID
    class MockProcess:
        def __init__(self, pid):
            pass
            
        def terminate(self):
            process_mock.terminate()
            
        def wait(self, timeout=None):
            # Simulate successful termination
            process_mock.wait(timeout)
            
        def kill(self):
            process_mock.kill()
    
    monkeypatch.setattr('management.server_utils.psutil.Process', MockProcess)
    monkeypatch.setattr('management.server_utils.psutil.pid_exists', lambda pid: False)
    
    # Try to kill a process
    result = kill_process(12345)
    
    # Should return True (process killed successfully)
    assert result is True
    
    # Verify process.terminate was called
    process_mock.terminate.assert_called_once()
    
    # Verify wait was called
    process_mock.wait.assert_called_once() 
"""
Tests for management command functionality.
"""
import os
import sys
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import pytest

from app.core.errors.base import BaseError, ErrorContext, ErrorSeverity
from app.core.errors.database import DatabaseError
from app.core.errors.management import ProcessError
from app.core.logging import setup_logger

from management.commands import (
    run_db_init,
    run_migrations,
    check_db_structure,
    explore_db_contents,
    dump_db_to_file,
    check_characters,
    check_images,
    start_frontend,
    start_backend,
    stop_server
)
from app.database.models import User, Character, Story
from app.core.security import get_password_hash

# Import test_user fixture from test_api
@pytest.fixture
def test_user(test_db_session):
    """Create a test user for API tests."""
    from app.database.models import User
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$1234567890123456789012.1234567890123456789012345678901234",
        first_name="Test",
        last_name="User"
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


class TestBackendCommands:
    @patch('management.commands.get_pid')
    @patch('management.commands.subprocess.Popen')
    @patch('management.commands.save_pid')
    def test_start_backend_interactive(self, mock_save_pid, mock_popen, mock_get_pid):
        """Test starting the backend server in interactive mode."""
        # Mock get_pid to return None (server not running)
        mock_get_pid.return_value = None
        
        # Mock subprocess.Popen
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        # Run the command
        class Args:
            backend_port = 8000
            detach = False
            frontend = False
            use_ide_terminal = False
        
        # Run the command
        start_backend(Args())
        
        # Verify expectations
        mock_popen.assert_called_once_with([
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
        mock_save_pid.assert_called_once_with("backend", 12345)
    
    @patch('management.commands.get_pid')
    @patch('management.commands.subprocess.Popen')
    @patch('management.commands.save_pid')
    @patch('management.commands.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_start_backend_detached(self, mock_file, mock_makedirs, mock_save_pid, mock_popen, mock_get_pid):
        """Test starting the backend server in detached mode."""
        # Mock get_pid to return None (server not running)
        mock_get_pid.return_value = None
        
        # Set up mock process
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        mock_process.pid = 12345
        
        # Create args object
        class Args:
            backend_port = 8000
            detach = True
            frontend = False
        
        # Run the command
        with patch('builtins.print') as mock_print:
            start_backend(Args())
        
        # Verify expectations
        mock_makedirs.assert_called_once_with("logs", exist_ok=True)
        mock_file.assert_called_once()
        mock_popen.assert_called_once()
        mock_save_pid.assert_called_once_with("backend", 12345)
    
    @patch('management.commands.get_pid')
    def test_start_backend_already_running(self, mock_get_pid):
        """Test starting the backend server when it's already running."""
        # Mock get_pid to return a valid PID (server already running)
        mock_get_pid.return_value = 12345
        
        # Create args object
        class Args:
            backend_port = 8000
            detach = False
            frontend = False
        
        # Capture logger output
        with patch('app.core.logging.setup_logger') as mock_logger:
            start_backend(Args())
            mock_logger.info.assert_called_once_with("Backend server is already running.")


class TestFrontendCommands:
    @patch('management.commands.get_pid')
    @patch('management.commands.Path.exists')
    @patch('management.commands.os.path.exists')
    @patch('management.commands.os.chdir')
    @patch('management.commands.subprocess.check_output')
    @patch('management.commands.subprocess.Popen')
    @patch('management.commands.save_pid')
    @patch('builtins.open', new_callable=mock_open)
    def test_start_frontend_interactive(self, mock_file, mock_save_pid, mock_popen,
                                      mock_check_output, mock_chdir, mock_path_exists,
                                      mock_dir_exists, mock_get_pid):
        """Test starting the frontend server in interactive mode."""
        # Mock get_pid to return None (server not running)
        mock_get_pid.return_value = None
        
        # Mock directory checks
        mock_dir_exists.return_value = True
        mock_path_exists.side_effect = lambda x: x != "yarn.lock"  # No yarn.lock = use npm
        
        # Mock npm version check
        mock_check_output.return_value = b"8.0.0\n"
        
        # Mock package.json content
        mock_json_content = '{"scripts": {"dev": "next dev"}}'
        mock_file.return_value.read.return_value = mock_json_content
        
        # Mock subprocess.Popen
        mock_process = MagicMock()
        mock_process.pid = 99999
        mock_popen.return_value = mock_process
        
        # Create args object
        class Args:
            frontend_port = 3000
            detach = False
            use_ide_terminal = False
            backend = False
        
        # Run the command
        with patch('json.load') as mock_json:
            mock_json.return_value = {"scripts": {"dev": "next dev"}}
            start_frontend(Args())
        
        # Verify expectations
        mock_popen.assert_called_once_with(["npm", "run", "dev"])
        mock_save_pid.assert_called_once_with("frontend", 99999)
    
    @patch('management.commands.get_pid')
    def test_start_frontend_already_running(self, mock_get_pid):
        """Test starting the frontend server when it's already running."""
        # Mock get_pid to return a valid PID (server already running)
        mock_get_pid.return_value = 54321
        
        # Create args object
        class Args:
            frontend_port = 3000
            detach = False
        
        # Capture logger output instead of print
        with patch('management.commands.logger') as mock_logger:
            start_frontend(Args())
            mock_logger.info.assert_called_once_with("Frontend server is already running.")


class TestStopCommands:
    @patch('management.commands.find_server_pid')
    @patch('management.commands.kill_process')
    @patch('management.commands.get_pid_file')
    @patch('management.commands.os.path.exists')
    @patch('management.commands.os.remove')
    def test_stop_server_success(self, mock_remove, mock_exists, mock_get_pid_file, 
                                mock_kill, mock_find_pid):
        """Test stopping a server successfully."""
        # Mock find_server_pid to return a valid PID
        mock_find_pid.return_value = 12345
        
        # Mock successful process kill
        mock_kill.return_value = True
        
        # Mock PID file exists
        mock_exists.return_value = True
        mock_get_pid_file.return_value = "/tmp/test_server.pid"
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            stop_server("backend")
            
            # Verify expectations
            mock_find_pid.assert_called_once_with("backend")
            mock_kill.assert_called_once_with(12345)
            mock_get_pid_file.assert_called_once_with("backend")
            mock_remove.assert_called_once_with("/tmp/test_server.pid")
    
    @patch('management.commands.find_server_pid')
    def test_stop_server_not_running(self, mock_find_pid):
        """Test stopping a server that is not running."""
        # Mock find_server_pid to return None (server not running)
        mock_find_pid.return_value = None
        
        # Capture logger output
        with patch('app.core.logging.setup_logger') as mock_logger:
            stop_server("backend")
            mock_logger.info.assert_called_once_with("Backend server is not running.")
    
    @patch('management.commands.find_server_pid')
    @patch('management.commands.kill_process')
    def test_stop_server_failure(self, mock_kill, mock_find_pid):
        """Test failure when stopping a server."""
        # Mock find_server_pid to return a valid PID
        mock_find_pid.return_value = 12345
        
        # Mock failed process kill
        mock_kill.return_value = False
        
        # We need to patch the with_error_handling decorator to prevent sys.exit
        # We'll patch the handle_error function instead to prevent the sys.exit call
        with patch('app.core.errors.base.handle_error') as mock_handle_error, \
             patch('app.core.logging.setup_logger') as mock_logger:
            
            # Call the function - it will raise an error but our mock will catch it
            try:
                stop_server("backend")
            except Exception:
                pass  # We expect an exception


class TestDatabaseCommands:
    @patch('management.commands.init_db')
    def test_run_db_init_success(self, mock_init_db):
        """Test successful database initialization."""
        mock_init_db.return_value = "/path/to/db.sqlite"
        
        result = run_db_init()
        assert result is True
        mock_init_db.assert_called_once()
    
    @patch('management.commands.init_db')
    def test_run_db_init_failure(self, mock_init_db):
        """Test database initialization failure."""
        mock_init_db.side_effect = Exception("DB init error")
        
        with patch('app.core.logging.setup_logger') as mock_logger:
            mock_log = MagicMock()
            mock_logger.return_value = mock_log
            
            try:
                result = run_db_init()
                assert False, "Should have raised DatabaseError"
            except DatabaseError as e:
                assert str(e) == "Failed to initialize database"
                assert e.details == "DB init error"
                assert e.severity.value == "ERROR"
    
    @patch('management.commands.run_db_migrations')
    def test_run_migrations_success(self, mock_run_migrations):
        """Test successful database migrations."""
        mock_run_migrations.return_value = True
        
        result = run_migrations()
        assert result is True
        mock_run_migrations.assert_called_once()
    
    @patch('management.commands.run_db_migrations')
    def test_run_migrations_failure(self, mock_run_migrations):
        """Test database migrations failure."""
        mock_run_migrations.side_effect = Exception("Migration error")
        
        with patch('app.core.logging.setup_logger') as mock_logger:
            mock_log = MagicMock()
            mock_logger.return_value = mock_log
            
            try:
                result = run_migrations()
                assert False, "Should have raised DatabaseError"
            except DatabaseError as e:
                assert str(e) == "Failed to run database migrations"
                assert e.details == "Migration error"
                assert e.severity.value == "ERROR"


class TestDatabaseInspectionCommands:
    @patch('management.db_inspection.check_db_structure')
    def test_check_db_structure_success(self, mock_check_structure):
        """Test successful database structure check."""
        mock_check_structure.return_value = True
        
        result = check_db_structure()
        assert result is True
        mock_check_structure.assert_called_once_with(None)
    
    @patch('management.db_inspection.check_db_structure')
    def test_check_db_structure_failure(self, mock_check_structure):
        """Test failure when checking database structure."""
        # Mock check_db_structure to raise an error
        mock_check_structure.side_effect = DatabaseError("Test error")
        
        # Capture logger output
        with patch('app.core.logging.setup_logger') as mock_logger:
            with pytest.raises(DatabaseError):
                check_db_structure()
            mock_logger.error.assert_called()
    
    @patch('management.db_inspection.explore_db_contents')
    def test_explore_db_contents_success(self, mock_explore_contents):
        """Test successful database contents exploration."""
        mock_explore_contents.return_value = True
        
        result = explore_db_contents()
        assert result is True
        mock_explore_contents.assert_called_once_with(None)
    
    @patch('management.db_inspection.explore_db_contents')
    def test_explore_db_contents_failure(self, mock_explore_contents):
        """Test failure when exploring database contents."""
        # Mock explore_db_contents to raise an error
        mock_explore_contents.side_effect = DatabaseError("Test error")
        
        # Capture logger output
        with patch('app.core.logging.setup_logger') as mock_logger:
            with pytest.raises(DatabaseError):
                explore_db_contents()
            mock_logger.error.assert_called()
    
    @patch('management.db_inspection.dump_db_to_file')
    def test_dump_db_to_file_success(self, mock_dump_db):
        """Test successful database dump to file."""
        mock_dump_db.return_value = True
        
        result = dump_db_to_file()
        assert result is True
        mock_dump_db.assert_called_once_with(None, "db_dump.txt")
    
    @patch('management.db_inspection.dump_db_to_file')
    def test_dump_db_to_file_failure(self, mock_dump_db):
        """Test failure when dumping database to file."""
        # Mock dump_db_to_file to raise an error
        mock_dump_db.side_effect = DatabaseError("Test error")
        
        # Capture logger output
        with patch('app.core.logging.setup_logger') as mock_logger:
            with pytest.raises(DatabaseError):
                dump_db_to_file("test.json")
            mock_logger.error.assert_called()


class TestContentInspectionCommands:
    @patch('management.content_inspection.check_characters')
    def test_check_characters_success(self, mock_inspect_characters):
        """Test successful character check."""
        mock_inspect_characters.return_value = True
        
        result = check_characters()
        assert result is True
        mock_inspect_characters.assert_called_once_with(None)
    
    @patch('management.content_inspection.check_characters')
    def test_check_characters_failure(self, mock_inspect_characters):
        """Test failure when checking characters."""
        # Mock check_characters to raise an error
        mock_inspect_characters.side_effect = DatabaseError("Test error")
        
        # Capture logger output
        with patch('app.core.logging.setup_logger') as mock_logger:
            with pytest.raises(DatabaseError):
                check_characters()
            mock_logger.error.assert_called()
    
    @patch('management.content_inspection.check_images')
    def test_check_images_success(self, mock_inspect_images):
        """Test successful image check."""
        mock_inspect_images.return_value = True
        
        result = check_images()
        assert result is True
        mock_inspect_images.assert_called_once_with(None)
    
    @patch('management.content_inspection.check_images')
    def test_check_images_failure(self, mock_inspect_images):
        """Test failure when checking images."""
        # Mock check_images to raise an error
        mock_inspect_images.side_effect = DatabaseError("Test error")
        
        # Capture logger output
        with patch('app.core.logging.setup_logger') as mock_logger:
            with pytest.raises(DatabaseError):
                check_images()
            mock_logger.error.assert_called()


# Define the integration marker for pytest
def pytest_configure(config):
    """Add integration marker to pytest configuration."""
    config.addinivalue_line("markers", "integration: mark test as integration test")


@pytest.mark.integration
class TestCommandsIntegration:
    """Integration tests for management commands with API endpoints."""
    
    def test_api_endpoints_available_after_start(self, test_client):
        """Test that API endpoints are available."""
        # Test a few key endpoints are reachable
        endpoints = [
            "/api/characters/",
            "/api/stories/",
            "/api/auth/login"
        ]
        
        for endpoint in endpoints:
            method = test_client.get if "login" not in endpoint else test_client.post
            response = method(endpoint)
            assert response.status_code != 404, f"Endpoint {endpoint} should exist"
    
    @patch('management.commands.get_pid')
    @patch('management.commands.subprocess.Popen')
    @patch('management.commands.save_pid')
    def test_backend_startup_exposes_api(self, mock_save_pid, mock_popen, mock_get_pid, test_client):
        """Test that starting the backend server makes API endpoints available."""
        # Mock server startup
        mock_get_pid.return_value = None
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        mock_process.pid = 12345
        
        # Create args object
        class Args:
            backend_port = 8000
            detach = True
            frontend = False
        
        # Start the server
        start_backend(Args())
        
        # Verify API endpoints are available
        response = test_client.get("/api/characters/")
        assert response.status_code != 404, "Characters endpoint should be available"
        
        # Test authentication endpoint
        auth_response = test_client.post("/api/auth/login", json={"username": "test", "password": "test"})
        assert auth_response.status_code != 404, "Auth endpoint should be available"
    
    @pytest.mark.parametrize("endpoint,method,test_data", [
        ("/api/characters/", "GET", None),
        ("/api/stories/", "GET", None),
        ("/api/auth/login", "POST", {"username": "test", "password": "test"}),
        ("/api/auth/register", "POST", {"username": "newuser", "email": "new@example.com",
                                       "password": "password123", "first_name": "New", "last_name": "User"})
    ])
    def test_api_endpoints_with_data(self, endpoint, method, test_data, test_client, test_db_session):
        """Test that API endpoints are accessible with data."""
        # Create a test user for authentication
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()

        # Make the request
        if method == "GET":
            response = test_client.get(endpoint)
        elif method == "POST":
            response = test_client.post(endpoint, json=test_data)
        else:
            pytest.fail(f"Unsupported method: {method}")

        # Check response
        assert response.status_code in [200, 201, 401, 422]  # Valid response codes
    
    @patch('management.db_utils.init_db')
    @patch('management.db_utils.run_migrations')
    def test_database_initialization_before_api(self, mock_migrations, mock_db_init, test_client):
        """Test database initialization before API becomes available."""
        # Mock successful DB initialization and migrations
        mock_db_init.return_value = True
        mock_migrations.return_value = True
        
        # Run DB initialization
        assert run_db_init() is True
        assert run_migrations() is True
        
        # Verify API endpoints are available after DB setup
        response = test_client.get("/api/characters/")
        assert response.status_code != 404, "Characters endpoint should be available after DB setup"


@pytest.mark.parametrize("command_function,module_path,expected_result", [
    (run_db_init, 'management.commands.init_db', True),
    (run_migrations, 'management.commands.run_db_migrations', True),
    (check_db_structure, 'management.db_inspection.check_db_structure', True),
    (explore_db_contents, 'management.db_inspection.explore_db_contents', True)
])
def test_command_returns_success(command_function, module_path, expected_result, monkeypatch):
    """Test that command functions return success values when operations succeed."""
    # Create a mock function that returns the expected result
    mock_func = MagicMock(return_value=expected_result)
    
    # Patch the imported function
    with patch(module_path, mock_func):
        # Call the command function
        result = command_function()
        
        # Verify the result
        assert result == expected_result, f"{command_function.__name__} should return {expected_result} on success"


class TestRunTestsScript:
    """Tests for the run_tests.py script that runs the test suite."""
    
    @patch('subprocess.run')
    def test_run_tests_basic(self, mock_subprocess_run, monkeypatch):
        """Test basic functionality of run_tests.py script."""
        # Import the run_tests module
        sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
        import run_tests
        
        # Mock successful subprocess run
        mock_subprocess_run.return_value.returncode = 0
        
        # Create arguments for basic test run
        class Args:
            verbose = True
            quiet = False
            keyword = None
            xvs = False
            show_locals = False
            fail_fast = False
            disable_warnings = True
            coverage = False
            html_cov = False
            test_path = None
            pytest_args = []
        
        # Run the tests function
        result = run_tests.run_tests(Args())
        
        # Verify subprocess.run was called with the correct command
        mock_subprocess_run.assert_called_once()
        cmd = mock_subprocess_run.call_args[0][0]
        assert 'pytest' in cmd
        assert '-v' in cmd
        assert '-p no:warnings' in cmd
        assert 'tests/' in cmd
        
        # Verify environment variables were set
        env = mock_subprocess_run.call_args[1]['env']
        assert env['TESTING'] == '1'
        assert env['SECRET_KEY'] == 'test_secret_key'
        
        # Verify the return code
        assert result == 0
    
    @patch('subprocess.run')
    def test_run_tests_with_coverage(self, mock_subprocess_run, monkeypatch):
        """Test run_tests.py script with coverage options."""
        # Import the run_tests module
        sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
        import run_tests
        
        # Mock successful subprocess run
        mock_subprocess_run.return_value.returncode = 0
        
        # Create arguments for coverage test run
        class Args:
            verbose = False
            quiet = False
            keyword = None
            xvs = False
            show_locals = False
            fail_fast = False
            disable_warnings = False
            coverage = True
            html_cov = True
            test_path = 'tests/test_api.py'
            pytest_args = []
        
        # Run the tests function
        result = run_tests.run_tests(Args())
        
        # Verify subprocess.run was called with the correct command
        mock_subprocess_run.assert_called_once()
        cmd = mock_subprocess_run.call_args[0][0]
        assert 'pytest' in cmd
        assert '--cov=management' in cmd
        assert '--cov=app' in cmd
        assert '--cov-report=html' in cmd
        assert 'tests/test_api.py' in cmd
        
        # Verify the return code
        assert result == 0
    
    @patch('subprocess.run')
    def test_run_tests_with_keyword(self, mock_subprocess_run, monkeypatch):
        """Test run_tests.py script with keyword filtering."""
        # Import the run_tests module
        sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
        import run_tests
        
        # Mock successful subprocess run
        mock_subprocess_run.return_value.returncode = 0
        
        # Create arguments for keyword filtered test run
        class Args:
            verbose = False
            quiet = False
            keyword = 'api'
            xvs = False
            show_locals = False
            fail_fast = False
            disable_warnings = False
            coverage = False
            html_cov = False
            test_path = None
            pytest_args = ['--no-header']
        
        # Run the tests function
        result = run_tests.run_tests(Args())
        
        # Verify subprocess.run was called with the correct command
        mock_subprocess_run.assert_called_once()
        cmd = mock_subprocess_run.call_args[0][0]
        assert 'pytest' in cmd
        assert '-k' in cmd
        assert 'api' in cmd
        assert '--no-header' in cmd
        
        # Verify the return code
        assert result == 0 
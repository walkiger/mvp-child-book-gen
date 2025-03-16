# Test Suite Documentation

This directory contains all tests for the Child Book Generator application.

## Test Structure

The tests are organized by functionality:

- `test_commands.py`: Tests for management CLI commands
- `test_server_utils.py`: Tests for server utility functions
- `test_api.py`: Tests for API endpoints
- `test_models.py`: Tests for database models
- `test_error_handling.py`: Comprehensive tests for the error handling framework
- `test_error_simple.py`: Simple tests for error classes without mocking
- `test_standalone.py`: Standalone tests with visual feedback

## Error Handling Tests

The error handling tests validate the functionality of our custom error handling framework:

1. **Error Class Hierarchy**:
   - Base error class functionality
   - Inheritance and specialization
   - Severity levels (INFO, WARNING, ERROR, CRITICAL)
   - Message formatting

2. **Error Handling Decorators**:
   - Function wrapping
   - Error catching and logging
   - Exit behavior on critical errors
   - Context information preservation

3. **Error Recovery Mechanisms**:
   - Retry functionality
   - Fallback mechanisms
   - Graceful degradation

## Test Coverage

Current test coverage:
- Management package: 34%
- Utils package: 34%
- App package: 12%

Target coverage:
- Management package: 70%
- Utils package: 70%
- App package: 50%

## Running Tests

You can run tests using the `run_tests.py` script in the project root:

```bash
# Run all tests
python run_tests.py

# Run with verbose output
python run_tests.py -v

# Run with coverage report
python run_tests.py --coverage

# Run a specific test file
python run_tests.py tests/test_db_utils.py

# Run tests matching a keyword
python run_tests.py -k "db"

# Generate HTML coverage report
python run_tests.py --coverage --html-cov

# Disable warnings
python run_tests.py --disable-warnings
```

Alternatively, you can run pytest directly:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v tests/

# Run with coverage
pytest --cov=management --cov=app tests/
```

## Running Error Handling Tests

The test suite includes dedicated test files for the error handling framework:

```bash
# Run all error handling tests
pytest tests/test_error_*.py

# Run the comprehensive error handling tests (with mocking)
pytest tests/test_error_handling.py

# Run simple error handling tests (without mocking)
pytest tests/test_error_simple.py

# Run standalone test with visual output
pytest tests/test_standalone.py
```

Each error handling test file serves a different purpose:

- `test_error_handling.py`: Comprehensive tests using mocks and patches to fully test the error framework
- `test_error_simple.py`: Basic tests that verify core functionality without complex mocking
- `test_standalone.py`: Visual tests that demonstrate error handling with detailed console output

### Error Handling Test Coverage

The error handling tests provide comprehensive coverage of the error handling framework:

1. **Error Class Hierarchy**:
   - Base error class functionality and inheritance
   - Specialized error types (ServerError, DatabaseError, etc.)
   - Error severity levels and formatting
   - Error context and additional information

2. **Error Handling Decorator**:
   - Exception catching and logging
   - Return value handling for different scenarios
   - Exit behavior when critical errors occur
   - Custom error transformation

3. **Recovery Mechanisms**:
   - Retry functionality with configurable attempts and backoff
   - Circuit breaker pattern implementation
   - Resource management with automatic cleanup

4. **Logging and Reporting**:
   - Logger setup and configuration
   - Error message formatting
   - Log level selection based on severity
   - Context inclusion in log messages

All tests are designed to work with the shared error handling utilities in the `utils.error_handling` module.

## Test Structure

The test suite uses pytest and follows these conventions:

1. **Test Files**: Named with the pattern `test_*.py`
2. **Test Functions**: Named with the pattern `test_*`
3. **Fixtures**: Defined in `conftest.py` for reuse across tests

## Pytest Configuration

The `pytest.ini` file in the project root configures the test environment:

```ini
[pytest]
markers =
    integration: marks tests as integration tests (may require external services)
asyncio_mode = strict
```

You can mark integration tests with `@pytest.mark.integration` to distinguish them from unit tests.

## Available Fixtures

Common test fixtures are defined in `conftest.py`:

- `temp_db_path`: Creates a temporary database file
- `temp_dir`: Creates a temporary directory
- `empty_db`: Creates an empty SQLite database
- `sqlite_memory_db`: Creates an in-memory SQLite database
- `mock_logger`: Provides a mock logger instance
- `disable_logging`: Temporarily disables logging
- `run_in_temp_dir`: Runs a test in a temporary directory
- `test_app`: Creates a FastAPI test application with CORS middleware
- `error_factory`: Creates instances of different error types for testing
- `test_error_handling_function`: Provides a function decorated with error handling

## Current Test Coverage

Current test coverage is at 47% across the codebase. Some highlights:

- 100% coverage for `app/core/image_generation.py`
- 85% coverage for `app/api/auth.py`
- 88% coverage for `app/core/rate_limiter.py`
- 68% coverage for `management/commands.py`
- 64% coverage for `app/api/stories.py`

Areas for improvement include:

- `management/content_inspection.py` (7%)
- `management/db_inspection.py` (6%)
- Database migrations modules (0%)
- `app/api/characters.py` (38%)

## Test Coverage Components

The test suite covers the following components:

### Backend API
- `test_api.py`: Tests API endpoints existence and CORS headers
- `test_main.py`: Tests the main FastAPI application, including root endpoint and middleware
- `test_auth.py`: Tests authentication and user management
- `test_characters.py`: Tests character creation and retrieval
- `test_stories.py`: Tests story generation and management

### Database
- `test_models.py`: Tests SQLAlchemy model creation, constraints, and relationships
- `test_db_utils.py`: Tests database initialization and migration utilities

### Configuration
- `test_config.py`: Tests settings initialization and database path construction

### Core Functionality
- `test_rate_limiter.py`: Tests rate limiting functionality for API requests
- `test_server_utils.py`: Tests server process management utilities
- `test_image_generation.py`: Tests DALL-E image generation for characters and stories

### Management Commands
- `test_commands.py`: Tests command-line management utilities for starting/stopping servers and database operations

### Error Handling Framework
- `test_error_handling.py`: Comprehensive tests for the error handling framework with mocking
  - Tests error class hierarchy and inheritance
  - Tests the error handling decorator with various parameters
  - Tests error handling utilities like `handle_error` and `setup_logger`
  - Tests error recovery mechanisms
- `test_error_simple.py`: Simple tests for basic error handling functionality without mocking
  - Basic tests of error classes and inheritance
  - Simple tests of the decorator's behavior with different exception types
- `test_standalone.py`: Tests standalone error handling functions with visual output
  - Tests error handling utilities independently
  - Includes detailed console output for test progress
  - Tests exit behavior and logging configuration

## Important Notes for Test Development

### Story Schema Validation

When writing tests for story creation, be aware of these validation requirements:

- `age_group`: Must match pattern `^(1-2|3-6|6-9|10-12)$`
- `story_tone`: Must match pattern `^(whimsical|educational|adventurous|calming)$`
- `moral_lesson`: Must match pattern `^(kindness|courage|friendship|honesty|perseverance)$`

Example of valid `StoryCreate` in tests:

```python
story_data = StoryCreate(
    title="Test Story",
    age_group="6-9",  # Valid value
    character_id=1,
    page_count=2,
    moral_lesson="kindness",  # Valid value
    story_tone="adventurous",  # Valid value
    temperature=1.2
)
```

### Known Warnings

The test suite currently shows warnings related to Pydantic's deprecated features:

- Pydantic V2.0 deprecation warnings for class-based `config` (will be removed in V3.0)
- You can run with `--disable-warnings` to hide these if needed

## Writing Tests

Here's an example of writing a test using pytest:

```python
def test_example(temp_db_path):
    # Use the temp_db_path fixture
    assert os.path.exists(temp_db_path)
    
    # Use plain assert statements (not unittest.TestCase methods)
    result = my_function()
    assert result == expected_value
```

For mocking dependencies, use pytest's `monkeypatch` fixture:

```python
def test_with_mocking(monkeypatch):
    # Replace a function or method
    monkeypatch.setattr('package.module.function', lambda: 'mocked result')
    
    # Test code that uses the mocked function
    result = code_that_calls_function()
    assert result == 'expected with mock'
```

For testing async functions, use the `pytest.mark.asyncio` decorator:

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await my_async_function()
    assert result == expected_value
```

### Testing Error Handling

When testing error handling, consider these approaches:

```python
# Testing exception class properties
def test_error_class():
    error = ManagementError("Test message", severity=ErrorSeverity.WARNING)
    assert error.severity == ErrorSeverity.WARNING
    assert "WARNING: Test message" in str(error)

# Testing decorator functionality
@with_error_handling
def function_that_raises():
    raise ValueError("Test error")
    
def test_decorator():
    # Should return False when exception is caught
    result = function_that_raises()
    assert result is False
    
# Testing with mocking
with patch('module.handle_error') as mock_handle_error:
    result = function_with_error_handling()
    mock_handle_error.assert_called_once()
``` 
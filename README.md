# Child Book Generator MVP

This application generates personalized children's books using AI.

## Management Commands

The application includes a comprehensive management CLI for various tasks:

### Server Management

- `python manage.py start` - Start both backend and frontend servers
  - `--backend` - Start only the backend server
  - `--frontend` - Start only the frontend server
  - `--backend-port PORT` - Specify backend port (default: 8080)
  - `--frontend-port PORT` - Specify frontend port (default: 3000)
  - `--detach` - Run in detached mode
  - `--use-ide-terminal` - Show commands for running in separate IDE terminals
  - `--unified-mode` - Run all servers in a unified terminal with color-coded output
  - `--with-dashboard` - Start the web dashboard alongside the servers

- `python manage.py stop` - Stop both servers
  - `--backend-only` - Stop only the backend server
  - `--frontend-only` - Stop only the frontend server
  - `--force` - Force kill the processes

- `python manage.py restart` - Restart both backend and frontend servers
  - `--backend` - Restart only the backend server
  - `--frontend` - Restart only the frontend server
  - `--backend-port PORT` - Specify backend port (default: 8080)
  - `--frontend-port PORT` - Specify frontend port (default: 3000)
  - `--use-ide-terminal` - Show commands for running in separate IDE terminals
  - `--unified-mode` - Run all servers in a unified terminal with color-coded output
  - `--with-dashboard` - Start the web dashboard alongside the servers

- `python manage.py status` - Show server status
- `python manage.py cleanup` - Clean up stale PID files

- `python manage.py dashboard` - Start a web dashboard for managing servers
  - `--port PORT` - Specify dashboard port (default: 3001)
  - `--backend-port PORT` - Specify backend port (default: 8080)
  - `--frontend-port PORT` - Specify frontend port (default: 3000)

### Environment Management

- `python manage.py env setup` - Setup or update environment variables
- `python manage.py env show` - Display current environment variables

### Project Setup

- `python manage.py setup-project` - Setup the project environment:
  - Create virtual environment
  - Install dependencies
  - Configure Alembic for migrations

### Database Management

- `python manage.py init-db` - Initialize the database
- `python manage.py migrate` - Run database migrations
- `python manage.py integrate-migrations` - Integrate existing migrations with Alembic

### Database Inspection

- `python manage.py db-check` - Check database structure
  - `--db-path PATH` - Path to database file
  - `--verbose, -v` - Show verbose output

- `python manage.py db-explore` - Explore database contents
  - `--db-path PATH` - Path to database file

- `python manage.py db-dump` - Dump database structure and contents to a file
  - `--db-path PATH` - Path to database file
  - `--output PATH` - Path to output file (default: db_dump.txt)

### Content Inspection

- `python manage.py check-characters` - Check character information in the database
  - `--db-path PATH` - Path to database file

- `python manage.py check-images` - Check image information in the database
  - `--db-path PATH` - Path to database file

## Getting Started

1. Clone the repository
2. Run `python manage.py setup-project` to set up the environment
3. Run `python manage.py env setup` to configure environment variables
4. Run `python manage.py init-db` to initialize the database
5. Run `python manage.py migrate` to apply migrations
6. Run `python manage.py start` to start the application

## Error Handling Framework

The application uses a robust error handling framework that provides standardized error management across all components:

### Key Components

1. **Error Class Hierarchy**:
   - `BaseError`: Foundation for all custom errors
   - Specialized error types for different scenarios (ServerError, DatabaseError, etc.)
   - Severity levels (INFO, WARNING, ERROR, CRITICAL)

2. **Error Handling Decorators**:
   - `with_error_handling`: Core decorator for standardized error handling
   - `db_error_handler`: Specialized decorator for database operations

3. **Recovery Mechanisms**:
   - Retry functionality with configurable attempts
   - Resource management with automatic cleanup
   - Graceful degradation

### Usage Example

```python
from utils.error_handling import with_error_handling, DatabaseError, ErrorSeverity

@with_error_handling(context="Database Operation", exit_on_error=False)
def process_data(db_path):
    try:
        # Database operations here
        return True
    except Exception as e:
        raise DatabaseError("Failed to process data", 
                          db_path=db_path, 
                          severity=ErrorSeverity.ERROR,
                          details=str(e))
        return False
```

## Testing

Run the test suite using pytest:

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test files
python -m pytest tests/test_error_handling.py

# Run with coverage report
python -m pytest --cov=app --cov=management --cov=utils
```

Current test coverage is at 44% with all error handling tests passing. The target is to reach at least 70% coverage.

## Project Structure

- `app/` - Main application code
  - `api/` - API routes and endpoints
  - `database/` - Database models and migrations
  - `schemas/` - Pydantic data models
  - `core/` - Core business logic
- `frontend/` - Frontend React application
- `management/` - Management CLI package
- `utils/` - Shared utilities and error handling framework
- `tests/` - Test modules for all components

## Development Roadmap

### Immediate Priorities

- Fix API test failures related to FastAPI mock configuration
- Address Pydantic V2 deprecation warnings in schema files
- Improve command test mocking

### Future Enhancements

- Increase test coverage to 70%+
- Standardize logging across all modules
- Enhance error handling documentation
- Implement comprehensive monitoring 
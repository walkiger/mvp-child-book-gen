# Child Book Generator MVP

This application generates personalized children's books using AI.

## Getting Started

1. Clone the repository
2. Run `python manage.py setup-project` to set up the environment
   - Creates virtual environment
   - Installs backend dependencies
   - Installs frontend dependencies
   - Configures Alembic for migrations
3. Run `python manage.py env setup` to configure environment variables
4. Run `python manage.py init-db` to initialize the database
5. Run `python manage.py migrate` to apply migrations
6. Run `python manage.py start` to start the application

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

### Environment Management

- `python manage.py env setup` - Setup or update environment variables
- `python manage.py env show` - Display current environment variables

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

Run the test suite using Jest:

```bash
# Run all tests
npm test

# Run with verbose output
npm test -- --verbose

# Run specific test files
npm test src/tests/ErrorDisplay.test.tsx

# Run with coverage report
npm test -- --coverage
```

### Test Coverage Status

#### Frontend Tests
- ✅ Error Display Component (100% coverage)
  - Error message rendering
  - Retry functionality
  - Close button behavior
  - Full page mode
  - Error details display

- ✅ Loading State Component (100% coverage)
  - Spinner variant
  - Skeleton variant
  - Custom styling
  - Text display
  - Multiple skeleton items

- ✅ Error Handling Utilities (95% coverage)
  - Error formatting
  - Retryable error detection
  - API error conversion
  - Network error handling
  - Rate limit handling

- ⚠️ Retry Operation (90% coverage)
  - Success scenarios
  - Network error retries
  - Non-retryable errors
  - Default max attempts
  - Exponential backoff
  - Known issue with maxAttempts test

#### Areas for Testing Focus
1. Error Handling Edge Cases
   - Rate limiting scenarios
   - Network timeouts
   - Server errors
   - Invalid response formats

2. Component Integration Tests
   - Character creation workflow
   - Story generation process
   - Image generation error handling
   - Form validation feedback

3. API Integration Tests
   - Authentication flows
   - Data fetching
   - Error recovery
   - Retry mechanisms

### Current Test Coverage
- Frontend Components: 44% coverage
- Error Handling: 95% coverage
- Loading States: 100% coverage
- API Integration: 35% coverage

### Testing Priorities
1. Fix retry operation maxAttempts test
2. Add rate limiting and timeout tests
3. Implement API integration tests
4. Add end-to-end workflow tests

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

### Immediate Priorities (1-2 days)
- Fix API test failures related to FastAPI mock configuration
- Address Pydantic V2 deprecation warnings in schema files
- Fix CORS headers configuration

### Short-term Goals (3-5 days)
- Fix command test mocking issues
- Fix configuration test environment validation
- Standardize logging across all modules

### Medium-term Goals (1-2 weeks)
- Improve error handling documentation
- Implement environment variable validation
- Add diagnostic tooling for troubleshooting

### Long-term Goals (2-4 weeks)
- Increase test coverage to 70%+
- Implement comprehensive monitoring dashboard
- Add automated recovery actions for common failures

## Frontend Improvements

### Immediate Focus
- Complete character creation API integration
- Fix image generation error handling
- Implement form validation

### Short-term Goals
- Convert character creation to step-by-step wizard
- Enhance state management
- Implement dashboard improvements

### Medium-term Goals
- Add visual trait selection interface
- Improve story generation workflow
- Implement PWA features

### Long-term Goals
- Add print-ready export functionality
- Implement advanced storytelling features
- Create character relationships system 
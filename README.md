# Child Book Generator MVP

## Overview
An AI-powered application that generates personalized children's stories with illustrations.

## Features
- Story generation with age-appropriate content
- Character creation with AI-generated illustrations
- User authentication and authorization
- Cost tracking for story generation
- Timezone-aware datetime handling
- Proper API response formatting
- Comprehensive test coverage

## Technical Stack
- Python FastAPI backend
- SQLAlchemy ORM
- OpenAI API integration
- JWT authentication
- Pydantic data validation
- Pytest testing framework
- SQLite database (development)
- Timezone-aware datetime handling

## Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables:
   ```
   OPENAI_API_KEY=your_key_here
   SECRET_KEY=your_secret_here
   ```
4. Run tests: `python -m pytest`
5. Start server: `uvicorn app.main:app --reload`

## API Documentation
- `/docs` - Swagger UI documentation
- `/redoc` - ReDoc documentation

### Key Endpoints
- POST `/api/auth/login` - User authentication
- POST `/api/stories/` - Generate new story
- POST `/api/characters/` - Create character
- POST `/api/images/generate` - Generate character image

## Testing
- Run tests: `python -m pytest`
- Run specific tests: `python -m pytest tests/test_api.py -v`
- Generate coverage report: `pytest --cov=app`

### Test Coverage
- API endpoints
- Authentication
- Story generation
- Image generation
- Character creation
- Error handling
- Timezone handling
- Data serialization

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make changes
4. Run tests
5. Submit pull request

## License
MIT License

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

### Server Management Commands

The following commands are available for managing the servers:

### Start Commands
- Start both servers in unified mode (recommended):
  ```bash
  python3 -m management.main start --unified-mode
  ```

- Start backend only:
  ```bash
  python3 -m management.main start --backend
  ```

- Start frontend only:
  ```bash
  python3 -m management.main start --frontend
  ```

- Start with custom ports:
  ```bash
  python3 -m management.main start --backend --frontend --backend-port 8000 --frontend-port 3001
  ```

### Stop Commands
- Stop all servers:
  ```bash
  python3 -m management.main stop --all
  ```

- Stop backend only:
  ```bash
  python3 -m management.main stop --backend
  ```

- Stop frontend only:
  ```bash
  python3 -m management.main stop --frontend
  ```

### Status Command
Check server status:
```bash
python3 -m management.main status
```

### Restart Commands
- Restart both servers:
  ```bash
  python3 -m management.main restart --all
  ```

- Restart backend only:
  ```bash
  python3 -m management.main restart --backend
  ```

- Restart frontend only:
  ```bash
  python3 -m management.main restart --frontend
  ```

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

## Project Structure

- `app/` - Main application code
  - `api/` - API routes and endpoints
  - `database/` - Database models and migrations
  - `schemas/` - Pydantic data models
  - `core/` - Core business logic
  - `errors/` - Error handling framework
- `frontend/` - Frontend React application
- `management/` - Management CLI package
- `utils/` - Shared utilities and error handling framework
- `tests/` - Test modules for all components

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
   - Retry logic for transient failures
   - Circuit breakers for external services
   - Rate limiting with backoff
   - Session recovery after authentication failures
   - Automatic cleanup of incomplete operations

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

## Development Roadmap

### Completed
- Basic API endpoints for character and story management
- Initial database models and schemas
- Authentication system with JWT
- Comprehensive error handling framework
- Frontend routing and basic components
- Image generation integration

### Immediate Priorities (1-2 days)
- Fix API test failures in FastAPI mock configuration
- Complete Pydantic V2 migration in schema files
- Fix CORS headers configuration for development
- Implement basic response caching
- Complete remaining error handling for story endpoints

### Short-term Goals (3-5 days)
- Enhance monitoring system with Prometheus metrics
- Implement Redis caching layer
- Increase test coverage to 80%
- Add comprehensive API documentation
- Complete dashboard implementation

### Medium-term Goals (1-2 weeks)
- Implement visual trait selection interface
- Add story templates and presets
- Create comprehensive monitoring dashboard
- Add automated error recovery actions
- Implement bulk operations for performance

### Long-term Goals (2-4 weeks)
- Add print-ready export functionality
- Implement PWA features for offline access
- Create character relationships system
- Add advanced storytelling features
- Implement microservices architecture

## Frontend Improvements

### Immediate Focus
- Complete story creation UI with preview
- Implement comprehensive form validation
- Add loading states for all async operations
- Fix image generation error handling
- Complete dashboard components

### Short-term Goals
- Convert character creation to step-by-step wizard
- Enhance state management with Zustand
- Implement comprehensive error recovery
- Add bulk operations interface
- Create visual trait selection

### Medium-term Goals
- Add advanced story customization
- Implement story preview system
- Add character relationship visualization
- Create print preview interface
- Implement offline capabilities

### Long-term Goals
- Add collaborative editing features
- Implement advanced animation effects
- Create story sharing platform
- Add accessibility improvements
- Implement advanced search and filtering
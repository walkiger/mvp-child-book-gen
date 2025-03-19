# Integration Testing Guide

## Overview

This guide covers integration testing strategies for the application, focusing on testing interactions between different components, services, and external dependencies.

## Integration Test Categories

### 1. API Integration Tests

#### Error Handling Integration
```python
@pytest.mark.asyncio
async def test_api_error_handling():
    """Test API error handling integration"""
    app = FastAPI()
    
    @app.get("/test-error")
    @with_api_error_handling
    async def test_endpoint():
        raise ValidationError(
            "Test error",
            error_context=ErrorContext(
                source="test.api",
                operation="test_endpoint",
                error_code="TEST-API-001",
                severity=ErrorSeverity.ERROR
            )
        )
    
    async with AsyncClient(app=app) as client:
        response = await client.get("/test-error")
        assert response.status_code == 400
        assert "TEST-API-001" in response.json()["error"]["code"]
        assert "Test error" in response.json()["error"]["message"]
```

#### Rate Limiting Integration
```python
@pytest.mark.asyncio
async def test_rate_limit_integration():
    """Test rate limiting integration with API"""
    app = FastAPI()
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    
    @app.get("/test-limit")
    @with_rate_limit(limiter)
    async def limited_endpoint():
        return {"status": "ok"}
    
    async with AsyncClient(app=app) as client:
        # First two requests should succeed
        response1 = await client.get("/test-limit")
        assert response1.status_code == 200
        
        response2 = await client.get("/test-limit")
        assert response2.status_code == 200
        
        # Third request should fail with rate limit error
        response3 = await client.get("/test-limit")
        assert response3.status_code == 429
        assert "RATE-LIM-001" in response3.json()["error"]["code"]
```

### 2. Database Integration Tests

#### Error Handling with Database
```python
def test_database_error_handling():
    """Test database error handling integration"""
    @with_db_error_handling
    def db_operation():
        raise sqlite3.OperationalError("Database locked")
    
    with pytest.raises(DatabaseError) as exc_info:
        db_operation()
    
    assert exc_info.value.error_code == "DB-OP-001"
    assert "Database locked" in str(exc_info.value)
    assert exc_info.value.error_context.source == "database"
```

#### Transaction Management
```python
def test_transaction_integration():
    """Test transaction management with error handling"""
    @with_db_error_handling
    def transactional_operation(session):
        with session.begin():
            # Perform database operations
            session.execute("INSERT INTO test_table VALUES (1, 'test')")
            raise ValueError("Trigger rollback")
    
    with pytest.raises(DatabaseError) as exc_info:
        transactional_operation(db.session)
    
    # Verify transaction was rolled back
    result = db.session.execute("SELECT COUNT(*) FROM test_table").scalar()
    assert result == 0
```

### 3. Authentication Integration

#### User Authentication Flow
```python
@pytest.mark.asyncio
async def test_auth_integration():
    """Test authentication integration"""
    app = FastAPI()
    
    @app.post("/login")
    @with_api_error_handling
    async def login(credentials: dict):
        if credentials["username"] != "test" or credentials["password"] != "test":
            raise AuthenticationError(
                "Invalid credentials",
                error_context=ErrorContext(
                    source="auth",
                    operation="login",
                    error_code="AUTH-001",
                    severity=ErrorSeverity.ERROR
                )
            )
        return {"token": "test_token"}
    
    async with AsyncClient(app=app) as client:
        # Test invalid credentials
        response = await client.post("/login", json={
            "username": "wrong",
            "password": "wrong"
        })
        assert response.status_code == 401
        assert "AUTH-001" in response.json()["error"]["code"]
        
        # Test valid credentials
        response = await client.post("/login", json={
            "username": "test",
            "password": "test"
        })
        assert response.status_code == 200
        assert "token" in response.json()
```

### 4. External Service Integration

#### API Client Integration
```python
def test_external_api_integration():
    """Test external API client integration"""
    @with_api_error_handling
    def call_external_api():
        try:
            response = requests.get("https://api.example.com/test")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise APIError(
                "External API error",
                error_context=ErrorContext(
                    source="external.api",
                    operation="test_call",
                    error_code="EXT-API-001",
                    severity=ErrorSeverity.ERROR,
                    additional_data={"status_code": e.response.status_code}
                )
            )
    
    with pytest.raises(APIError) as exc_info:
        call_external_api()
    
    assert exc_info.value.error_code == "EXT-API-001"
    assert exc_info.value.error_context.source == "external.api"
```

## Best Practices

### Test Organization
1. Group related integration tests
2. Use meaningful test names
3. Follow arrange-act-assert pattern
4. Use appropriate fixtures
5. Clean up test data

### Error Handling
1. Test error propagation
2. Verify error context
3. Check error responses
4. Test recovery flows
5. Validate error codes

### Database Testing
1. Use test database
2. Clean up after tests
3. Test transactions
4. Verify constraints
5. Check error states

### API Testing
1. Test endpoints
2. Verify responses
3. Check error handling
4. Test rate limiting
5. Validate payloads

## Common Integration Points

### Internal Services
1. API endpoints
2. Database operations
3. Authentication flows
4. Background tasks
5. Event handlers

### External Dependencies
1. Third-party APIs
2. Database systems
3. Message queues
4. Cache services
5. File storage

## Test Environment Setup

### Database Setup
```python
@pytest.fixture
def test_db():
    """Set up test database"""
    # Create test database
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    
    # Create test session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)
```

### API Client Setup
```python
@pytest.fixture
async def test_client():
    """Set up test API client"""
    app = create_test_app()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

## Error Scenarios

### Common Error Cases
1. Invalid input data
2. Authentication failures
3. Authorization errors
4. Resource not found
5. Rate limit exceeded
6. External service errors
7. Database constraints
8. Timeout errors

### Error Response Validation
```python
def validate_error_response(response: Response, expected_code: str):
    """Validate error response format"""
    assert response.status_code >= 400
    error_data = response.json()["error"]
    assert "code" in error_data
    assert "message" in error_data
    assert error_data["code"] == expected_code
```

## Monitoring and Logging

### Test Logging
```python
def test_error_logging_integration():
    """Test error logging integration"""
    logger = logging.getLogger("test.integration")
    handler = MemoryHandler(capacity=1000)
    logger.addHandler(handler)
    
    try:
        raise ValidationError(
            "Test error",
            error_context=ErrorContext(
                source="test.logging",
                operation="log_test",
                error_code="LOG-001",
                severity=ErrorSeverity.ERROR
            )
        )
    except BaseError as e:
        logger.error(str(e), extra={"error_context": e.error_context.to_dict()})
    
    assert len(handler.buffer) == 1
    record = handler.buffer[0]
    assert "LOG-001" in record.message
    assert record.error_context["source"] == "test.logging"
```

## Integration Test Coverage

### Coverage Areas
1. API endpoints
2. Database operations
3. Authentication flows
4. External services
5. Error handling
6. Rate limiting
7. Transactions
8. Event handling

### Coverage Requirements
1. All API endpoints
2. All database operations
3. All error scenarios
4. All external integrations
5. All authentication flows 
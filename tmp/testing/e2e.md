# End-to-End Testing Guide

## Overview

This guide covers end-to-end testing strategies for the application, focusing on testing complete user flows and system integration from start to finish.

## Test Categories

### 1. User Flow Tests

#### Complete Authentication Flow
```python
@pytest.mark.asyncio
async def test_complete_auth_flow():
    """Test complete user authentication flow"""
    app = create_test_app()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register new user
        register_response = await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test123!"
        })
        assert register_response.status_code == 201
        
        # Login
        login_response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "Test123!"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Access protected resource
        headers = {"Authorization": f"Bearer {token}"}
        profile_response = await client.get("/users/me", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["username"] == "testuser"
```

#### Story Generation Flow
```python
@pytest.mark.asyncio
async def test_story_generation_flow():
    """Test complete story generation flow"""
    app = create_test_app()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create story request
        story_request = {
            "theme": "adventure",
            "age_range": "6-8",
            "characters": ["hero", "sidekick"],
            "settings": ["forest", "castle"]
        }
        
        # Generate story
        response = await client.post("/stories/generate", json=story_request)
        assert response.status_code == 200
        story_id = response.json()["story_id"]
        
        # Check generation status
        status_response = await client.get(f"/stories/{story_id}/status")
        assert status_response.status_code == 200
        
        # Get generated story
        story_response = await client.get(f"/stories/{story_id}")
        assert story_response.status_code == 200
        story_data = story_response.json()
        assert "content" in story_data
        assert "images" in story_data
```

### 2. Error Handling Flows

#### Rate Limiting Flow
```python
@pytest.mark.asyncio
async def test_rate_limiting_flow():
    """Test rate limiting across multiple endpoints"""
    app = create_test_app()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        responses = []
        
        # Make requests until rate limited
        for _ in range(10):
            response = await client.post("/stories/generate", json={
                "theme": "quick_test"
            })
            responses.append(response)
            
            if response.status_code == 429:
                error_data = response.json()["error"]
                assert error_data["code"] == "RATE-LIM-001"
                assert "retry_after" in error_data
                break
        
        assert any(r.status_code == 429 for r in responses)
```

#### Error Recovery Flow
```python
@pytest.mark.asyncio
async def test_error_recovery_flow():
    """Test error recovery in story generation"""
    app = create_test_app()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Request with known error trigger
        response = await client.post("/stories/generate", json={
            "theme": "error_trigger",
            "retry_strategy": "automatic"
        })
        assert response.status_code == 200
        story_id = response.json()["story_id"]
        
        # Monitor recovery
        max_attempts = 5
        for _ in range(max_attempts):
            status_response = await client.get(f"/stories/{story_id}/status")
            status_data = status_response.json()
            
            if status_data["status"] == "completed":
                break
            elif status_data["status"] == "failed":
                assert status_data["error"]["code"] in ["STORY-GEN-001", "STORY-GEN-002"]
            
            await asyncio.sleep(1)
        
        final_response = await client.get(f"/stories/{story_id}")
        assert final_response.status_code == 200
```

### 3. Integration Flows

#### Database Integration Flow
```python
@pytest.mark.asyncio
async def test_database_integration_flow():
    """Test complete database integration flow"""
    app = create_test_app()
    db = get_test_db()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create test data
        test_data = {
            "name": "Test Story",
            "content": "Test content",
            "metadata": {"theme": "test"}
        }
        
        # Save to database
        response = await client.post("/stories", json=test_data)
        assert response.status_code == 201
        story_id = response.json()["id"]
        
        # Verify in database
        story = await db.stories.get(story_id)
        assert story.name == test_data["name"]
        
        # Update story
        update_response = await client.put(
            f"/stories/{story_id}",
            json={"name": "Updated Story"}
        )
        assert update_response.status_code == 200
        
        # Verify update
        updated_story = await db.stories.get(story_id)
        assert updated_story.name == "Updated Story"
```

#### External Service Integration Flow
```python
@pytest.mark.asyncio
async def test_external_service_integration():
    """Test integration with external services"""
    app = create_test_app()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Generate story with images
        response = await client.post("/stories/generate", json={
            "theme": "test",
            "include_images": True
        })
        assert response.status_code == 200
        story_id = response.json()["story_id"]
        
        # Wait for image generation
        max_attempts = 5
        for _ in range(max_attempts):
            status_response = await client.get(f"/stories/{story_id}/status")
            if status_response.json()["status"] == "completed":
                break
            await asyncio.sleep(2)
        
        # Verify images
        story_response = await client.get(f"/stories/{story_id}")
        assert story_response.status_code == 200
        assert "images" in story_response.json()
        assert len(story_response.json()["images"]) > 0
```

## Test Environment Setup

### Application Setup
```python
def create_test_app():
    """Create test application instance"""
    app = FastAPI()
    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[get_story_generator] = get_test_story_generator
    app.dependency_overrides[get_image_generator] = get_test_image_generator
    return app
```

### Database Setup
```python
@pytest.fixture
async def test_db():
    """Set up test database"""
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

## Best Practices

### Test Organization
1. Group by user flows
2. Test complete scenarios
3. Include error cases
4. Test recovery paths
5. Verify all integrations

### Test Environment
1. Use isolated database
2. Mock external services
3. Reset state between tests
4. Control test timing
5. Clean up resources

### Error Handling
1. Test rate limiting
2. Verify error responses
3. Test recovery flows
4. Check error logging
5. Monitor performance

### Data Management
1. Clean test data
2. Verify data integrity
3. Test constraints
4. Check audit trails
5. Monitor storage

## Common Scenarios

### User Flows
1. Registration
2. Authentication
3. Resource creation
4. Resource updates
5. Resource deletion

### Error Scenarios
1. Rate limiting
2. Service outages
3. Data validation
4. Authorization
5. Resource conflicts

### Integration Points
1. Database operations
2. External APIs
3. File storage
4. Message queues
5. Cache systems

## Test Coverage Requirements

### User Flows
1. All authentication paths
2. All resource operations
3. All user interactions
4. All error scenarios
5. All recovery paths

### Integration Points
1. Database operations
2. External services
3. File operations
4. Message handling
5. Cache management

### Error Handling
1. Input validation
2. Rate limiting
3. Service errors
4. Recovery flows
5. Error reporting

## Monitoring and Logging

### Test Logging
```python
def setup_test_logging():
    """Configure test logging"""
    logger = logging.getLogger("test.e2e")
    handler = MemoryHandler(capacity=1000)
    logger.addHandler(handler)
    return logger

def test_error_logging_e2e():
    """Test end-to-end error logging"""
    logger = setup_test_logging()
    
    try:
        raise ValidationError(
            "Test error",
            error_context=ErrorContext(
                source="test.e2e",
                operation="test_operation",
                error_code="E2E-001",
                severity=ErrorSeverity.ERROR
            )
        )
    except BaseError as e:
        logger.error(str(e), extra={"error_context": e.error_context.to_dict()})
    
    assert len(logger.handlers[0].buffer) == 1
    record = logger.handlers[0].buffer[0]
    assert "E2E-001" in record.message
```

## Performance Considerations

### Response Times
1. Monitor API latency
2. Track database times
3. Measure service calls
4. Check error handling
5. Verify timeouts

### Resource Usage
1. Memory consumption
2. CPU utilization
3. Database connections
4. Network bandwidth
5. Storage usage 
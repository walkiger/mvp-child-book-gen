# Error Handling Testing Guide

## Overview

This guide covers testing strategies for the unified error handling system, including error context validation, error propagation, and performance testing.

## Test Categories

### 1. Basic Error Handling Tests

#### Error Context Creation
```python
def test_error_context_basics():
    context = ErrorContext(
        source="test.module",
        operation="test_operation",
        error_code="TEST-OP-001",
        severity=ErrorSeverity.ERROR
    )
    assert context.source == "test.module"
    assert context.error_code == "TEST-OP-001"
```

#### Error Severity Levels
```python
def test_error_severity_levels():
    for severity in ErrorSeverity:
        context = ErrorContext(
            source="test.severity",
            operation="test_severity",
            error_code=f"SEV-TEST-{severity.name}",
            severity=severity
        )
        assert context.severity == severity
```

### 2. Error Context Validation

#### Format Validation
```python
def test_error_context_validation():
    # Valid formats
    ErrorContext(
        source="test.module",
        operation="test_operation",
        error_code="TEST-OP-001",
        severity=ErrorSeverity.ERROR
    )
    
    # Invalid formats should raise ValidationError
    with pytest.raises(ValidationError):
        ErrorContext(
            source="invalid source",
            operation="test",
            error_code="invalid-code",
            severity=ErrorSeverity.ERROR
        )
```

#### Immutability Testing
```python
def test_error_context_immutability():
    context = ErrorContext(
        source="test.module",
        operation="test_operation",
        error_code="TEST-OP-001",
        severity=ErrorSeverity.ERROR,
        additional_data={"key": "value"}
    )
    
    # Attempt modifications should raise
    with pytest.raises(AttributeError):
        context.source = "new.source"
    with pytest.raises(AttributeError):
        context.additional_data["new_key"] = "value"
```

### 3. Error Propagation Tests

#### Error Chaining
```python
def test_error_chaining():
    try:
        try:
            raise ValueError("Original error")
        except ValueError as e:
            context = ErrorContext(
                source="test.chain",
                operation="inner_operation",
                error_code="CHAIN-001",
                severity=ErrorSeverity.ERROR
            )
            raise DatabaseError("Database error", error_context=context) from e
    except DatabaseError as e:
        assert isinstance(e.__cause__, ValueError)
        assert e.error_context.error_code == "CHAIN-001"
```

#### Decorator Testing
```python
def test_error_handling_decorator():
    @with_api_error_handling
    def api_function():
        raise ValueError("Test error")
    
    with pytest.raises(APIError) as exc_info:
        api_function()
    
    assert exc_info.value.error_context.source == "api"
    assert "Test error" in str(exc_info.value)
```

### 4. Performance Testing

#### Error Creation Performance
```python
def test_error_context_creation_performance():
    start_time = time.time()
    contexts = []
    
    # Create 10,000 error contexts
    for i in range(10000):
        context = ErrorContext(
            source="test.performance",
            operation=f"operation_{i}",
            error_code=f"PERF-TEST-{i:03d}",
            severity=ErrorSeverity.ERROR
        )
        contexts.append(context)
    
    end_time = time.time()
    assert end_time - start_time < 1.0  # Should complete in under 1 second
```

#### Memory Usage
```python
def test_error_context_memory_usage():
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Create 100,000 error contexts
    contexts = [
        ErrorContext(
            source="test.memory",
            operation=f"operation_{i}",
            error_code=f"MEM-TEST-{i:03d}",
            severity=ErrorSeverity.ERROR,
            additional_data={"index": i}
        )
        for i in range(100000)
    ]
    
    final_memory = process.memory_info().rss
    memory_increase = (final_memory - initial_memory) / (1024 * 1024)
    assert memory_increase < 100  # Should use less than 100MB
```

### 5. Concurrent Testing

#### Thread Safety
```python
def test_error_context_thread_safety():
    error_counts = {}
    lock = threading.Lock()
    
    def worker(worker_id: int):
        for i in range(1000):
            try:
                if i % 2 == 0:
                    raise ValidationError(
                        "Test error",
                        error_context=ErrorContext(
                            source="test.thread",
                            operation=f"worker_{worker_id}",
                            error_code=f"THREAD-{worker_id:02d}",
                            severity=ErrorSeverity.ERROR
                        )
                    )
            except BaseError as e:
                with lock:
                    error_type = type(e).__name__
                    error_counts[error_type] = error_counts.get(error_type, 0) + 1
    
    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(10)
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]
```

### 6. Integration Testing

#### API Error Integration
```python
@pytest.mark.asyncio
async def test_api_error_handling():
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
```

#### Database Error Integration
```python
def test_database_error_handling():
    @with_db_error_handling
    def db_operation():
        raise sqlite3.OperationalError("Database locked")
    
    with pytest.raises(DatabaseError) as exc_info:
        db_operation()
    
    assert exc_info.value.error_code == "DB-OP-001"
    assert "Database locked" in str(exc_info.value)
```

## Best Practices

### Test Organization
1. Group related tests
2. Use descriptive names
3. Follow AAA pattern (Arrange, Act, Assert)
4. Use appropriate fixtures
5. Mock external dependencies

### Error Testing
1. Test both success and failure paths
2. Verify error context data
3. Check error code formats
4. Validate error messages
5. Test error chaining

### Performance Testing
1. Set clear benchmarks
2. Use appropriate sample sizes
3. Monitor resource usage
4. Test under load
5. Verify cleanup

### Integration Testing
1. Test real-world scenarios
2. Verify error propagation
3. Check error formatting
4. Test recovery mechanisms
5. Validate error responses

## Common Pitfalls

1. Not testing error context immutability
2. Missing edge cases
3. Inadequate performance testing
4. Poor cleanup in tests
5. Incomplete error chain testing

## Test Coverage

Ensure tests cover:
1. All error types
2. All severity levels
3. Error context creation
4. Error propagation
5. Performance characteristics
6. Integration points
7. Recovery mechanisms
8. Edge cases 
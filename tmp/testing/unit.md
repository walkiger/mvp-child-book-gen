# Unit Testing Guide

## Overview

This guide covers unit testing strategies for the application, focusing on testing individual components and functions in isolation.

## Test Categories

### 1. Error Context Tests

#### Basic Error Context
```python
def test_error_context_creation():
    """Test basic error context creation"""
    context = ErrorContext(
        source="test.unit",
        operation="test_operation",
        error_code="TEST-001",
        severity=ErrorSeverity.ERROR
    )
    
    assert context.source == "test.unit"
    assert context.operation == "test_operation"
    assert context.error_code == "TEST-001"
    assert context.severity == ErrorSeverity.ERROR
    assert context.timestamp is not None
```

#### Error Context Validation
```python
def test_error_context_validation():
    """Test error context validation"""
    # Valid formats
    ErrorContext(
        source="test.module",
        operation="test_operation",
        error_code="TEST-001",
        severity=ErrorSeverity.ERROR
    )
    
    # Invalid source format
    with pytest.raises(ValidationError):
        ErrorContext(
            source="invalid source",
            operation="test",
            error_code="TEST-001",
            severity=ErrorSeverity.ERROR
        )
    
    # Invalid error code format
    with pytest.raises(ValidationError):
        ErrorContext(
            source="test.module",
            operation="test",
            error_code="invalid-code",
            severity=ErrorSeverity.ERROR
        )
```

#### Additional Data Handling
```python
def test_error_context_additional_data():
    """Test error context additional data handling"""
    data = {"key": "value", "nested": {"inner": "data"}}
    context = ErrorContext(
        source="test.unit",
        operation="test_operation",
        error_code="TEST-001",
        severity=ErrorSeverity.ERROR,
        additional_data=data
    )
    
    assert context.additional_data == data
    assert context.additional_data["key"] == "value"
    assert context.additional_data["nested"]["inner"] == "data"
    
    # Test immutability
    with pytest.raises(AttributeError):
        context.additional_data["new_key"] = "value"
```

### 2. Error Type Tests

#### Base Error
```python
def test_base_error():
    """Test base error functionality"""
    context = ErrorContext(
        source="test.unit",
        operation="test_operation",
        error_code="TEST-001",
        severity=ErrorSeverity.ERROR
    )
    
    error = BaseError("Test error", error_context=context)
    assert str(error) == "Test error"
    assert error.error_context == context
    assert error.error_code == "TEST-001"
```

#### Validation Error
```python
def test_validation_error():
    """Test validation error functionality"""
    context = ErrorContext(
        source="test.validation",
        operation="validate_input",
        error_code="VAL-001",
        severity=ErrorSeverity.ERROR
    )
    
    error = ValidationError(
        "Invalid input",
        error_context=context,
        validation_errors=["Field 'name' is required"]
    )
    
    assert isinstance(error, BaseError)
    assert error.validation_errors == ["Field 'name' is required"]
    assert "Invalid input" in str(error)
```

#### Database Error
```python
def test_database_error():
    """Test database error functionality"""
    context = ErrorContext(
        source="test.database",
        operation="insert_record",
        error_code="DB-001",
        severity=ErrorSeverity.ERROR
    )
    
    error = DatabaseError(
        "Database connection failed",
        error_context=context,
        sql_state="08001"
    )
    
    assert isinstance(error, BaseError)
    assert error.sql_state == "08001"
    assert "Database connection failed" in str(error)
```

### 3. Error Handling Tests

#### Error Decorator
```python
def test_error_handling_decorator():
    """Test error handling decorator"""
    @with_error_handling
    def problematic_function():
        raise ValueError("Test error")
    
    with pytest.raises(BaseError) as exc_info:
        problematic_function()
    
    error = exc_info.value
    assert isinstance(error, BaseError)
    assert error.error_context is not None
    assert "Test error" in str(error)
```

#### Retry Decorator
```python
def test_retry_decorator():
    """Test retry decorator functionality"""
    attempt_count = 0
    
    @with_retry(max_retries=3, delay=0.1)
    def retryable_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise RetryableError("Temporary failure")
        return "success"
    
    result = retryable_function()
    assert result == "success"
    assert attempt_count == 3
```

### 4. Utility Tests

#### Error Code Generation
```python
def test_error_code_generation():
    """Test error code generation utility"""
    code = generate_error_code(
        domain="TEST",
        category="VAL",
        type="INV",
        number=1
    )
    
    assert code == "TEST-VAL-INV-001"
    assert is_valid_error_code(code)
```

#### Error Context Serialization
```python
def test_error_context_serialization():
    """Test error context serialization"""
    context = ErrorContext(
        source="test.unit",
        operation="test_operation",
        error_code="TEST-001",
        severity=ErrorSeverity.ERROR,
        additional_data={"key": "value"}
    )
    
    serialized = context.to_dict()
    assert serialized["source"] == "test.unit"
    assert serialized["operation"] == "test_operation"
    assert serialized["error_code"] == "TEST-001"
    assert serialized["severity"] == "ERROR"
    assert serialized["additional_data"]["key"] == "value"
```

## Best Practices

### Test Organization
1. Group related tests
2. Use descriptive names
3. Follow AAA pattern
4. Keep tests focused
5. Use appropriate fixtures

### Test Coverage
1. Test happy paths
2. Test edge cases
3. Test error conditions
4. Test input validation
5. Test error recovery

### Error Testing
1. Verify error types
2. Check error messages
3. Validate error codes
4. Test error context
5. Test error chaining

### Code Quality
1. DRY test code
2. Clear assertions
3. Meaningful setup
4. Proper cleanup
5. Good documentation

## Common Test Scenarios

### Input Validation
1. Required fields
2. Field formats
3. Data types
4. Value ranges
5. Dependencies

### Error Handling
1. Expected errors
2. Unexpected errors
3. Error recovery
4. Error propagation
5. Error logging

### Edge Cases
1. Empty inputs
2. Boundary values
3. Invalid formats
4. Resource limits
5. Timeout conditions

## Test Fixtures

### Error Context Fixture
```python
@pytest.fixture
def error_context():
    """Create a test error context"""
    return ErrorContext(
        source="test.fixture",
        operation="test_operation",
        error_code="TEST-001",
        severity=ErrorSeverity.ERROR
    )
```

### Mock Database Fixture
```python
@pytest.fixture
def mock_db():
    """Create a mock database"""
    class MockDB:
        def __init__(self):
            self.connected = True
        
        def query(self, sql):
            if not self.connected:
                raise DatabaseError(
                    "Database not connected",
                    error_context=ErrorContext(
                        source="test.db",
                        operation="query",
                        error_code="DB-001",
                        severity=ErrorSeverity.ERROR
                    )
                )
            return []
    
    return MockDB()
```

## Test Coverage Requirements

### Error Types
1. BaseError
2. ValidationError
3. DatabaseError
4. APIError
5. RetryableError

### Error Context
1. Creation
2. Validation
3. Serialization
4. Immutability
5. Chaining

### Error Handling
1. Decorators
2. Recovery
3. Retries
4. Logging
5. Monitoring

### Utilities
1. Code generation
2. Validation
3. Serialization
4. Formatting
5. Helpers 
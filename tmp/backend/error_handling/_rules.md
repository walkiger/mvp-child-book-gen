# Error Handling Rules

## Error Code Structure

### Format
```
[DOMAIN]-[CATEGORY]-[SPECIFIC]-[NUMBER]
```

### Domains
- `AUTH`: Authentication/Authorization
- `API`: API-related
- `DB`: Database
- `STORY`: Story Generation
- `IMG`: Image Processing
- `CFG`: Configuration
- `SYS`: System
- `VAL`: Validation
- `PROC`: Process

### Categories
- `VAL`: Validation
- `PERM`: Permissions
- `CONN`: Connection
- `PROC`: Processing
- `STATE`: State
- `LIMIT`: Rate Limiting
- `DATA`: Data
- `IO`: Input/Output

### Specific Codes
- `PWD`: Password
- `TOKEN`: Token
- `USER`: User
- `SESS`: Session
- `QUERY`: Query
- `TRANS`: Transaction
- `GEN`: Generation
- `SAVE`: Save
- `LOAD`: Load

### Numbers
- 001-099: General errors
- 100-199: Input validation errors
- 200-299: Processing errors
- 300-399: State errors
- 400-499: Connection errors
- 500-599: System errors

## Error Severity Levels

### Critical
- System is unusable
- Data corruption risk
- Security breach
- Required immediate action
- Must trigger alerts

### Error
- Operation failed
- Cannot proceed
- Requires intervention
- Should trigger notification
- Must be logged

### Warning
- Operation succeeded with issues
- Can proceed with caution
- Should be investigated
- Must be logged
- May trigger notification

### Info
- Expected errors
- Handled gracefully
- No immediate action needed
- Should be logged
- No notifications

## Error Handling Requirements

### Base Requirements
1. All errors must extend BaseError
2. All errors must have a unique error code
3. All errors must specify severity
4. All errors must provide clear messages
5. All errors must be logged

### Recovery Requirements
1. All external calls must use circuit breaker
2. Critical operations must implement retry
3. All retries must use exponential backoff
4. All retries must have maximum attempts
5. All retries must log attempts

### Monitoring Requirements
1. All errors must be tracked
2. Critical errors must trigger alerts
3. Error patterns must be detected
4. Error rates must be monitored
5. Recovery rates must be tracked

### Documentation Requirements
1. All error codes must be documented
2. All errors must have examples
3. All errors must have recovery steps
4. All errors must link to docs
5. All errors must have context

## Implementation Guidelines

### Error Creation
```python
def create_error(domain, category, specific, number, message, severity):
    code = f"{domain}-{category}-{specific}-{number}"
    return BaseError(
        message=message,
        error_code=code,
        severity=severity
    )
```

### Error Handling
```python
@with_error_handling
def process_operation():
    try:
        # Operation code
        pass
    except SpecificError as e:
        # Handle specific error
        raise
    except Exception as e:
        # Convert to appropriate error
        raise
```

### Recovery Pattern
```python
@retry_with_backoff(max_retries=3)
@circuit_breaker(failure_threshold=5)
def external_operation():
    try:
        # External operation code
        pass
    except ConnectionError as e:
        # Handle connection error
        raise
```

## Testing Requirements

### Unit Tests
1. Test all error creation
2. Test all error handling
3. Test all recovery mechanisms
4. Test all severity levels
5. Test all error codes

### Integration Tests
1. Test error propagation
2. Test recovery flows
3. Test monitoring integration
4. Test alert triggers
5. Test logging system

### Performance Tests
1. Test error handling overhead
2. Test recovery impact
3. Test monitoring impact
4. Test logging impact
5. Test alert impact

## Monitoring Setup

### Metrics to Track
1. Error rates by type
2. Recovery success rates
3. Circuit breaker states
4. Retry attempts
5. Response time impact

### Alerts
1. Critical error occurrence
2. High error rate
3. Low recovery rate
4. Circuit breaker trips
5. Performance degradation

## Documentation Requirements

### Error Catalog
1. List all error codes
2. Provide error examples
3. Include recovery steps
4. Link to relevant docs
5. Show error context

### Troubleshooting Guides
1. Common error patterns
2. Recovery procedures
3. Debug strategies
4. Performance impact
5. Monitoring guide

## Review Process

### Daily Review
1. Check error rates
2. Review critical errors
3. Check recovery rates
4. Monitor performance
5. Review alerts

### Weekly Review
1. Analyze error patterns
2. Review documentation
3. Check test coverage
4. Review monitoring
5. Plan improvements

### Monthly Review
1. Update error catalog
2. Review error codes
3. Update documentation
4. Review performance
5. Plan enhancements 
# Performance Testing Guide

## Overview

This guide covers performance testing strategies for the application, focusing on error handling, rate limiting, and API performance.

## Performance Test Categories

### 1. Error Handling Performance

#### Error Context Creation
```python
def test_error_context_creation_benchmark():
    """Benchmark error context creation performance"""
    N = 10000
    start_time = time.time()
    
    for i in range(N):
        ErrorContext(
            source="test.benchmark",
            operation=f"operation_{i}",
            error_code=f"BENCH-{i:04d}",
            severity=ErrorSeverity.ERROR,
            additional_data={"index": i}
        )
    
    end_time = time.time()
    creation_rate = N / (end_time - start_time)
    assert creation_rate > 5000  # At least 5000 contexts per second
```

#### Error Chain Performance
```python
def test_error_chain_performance():
    """Test performance of error chaining"""
    N = 1000
    start_time = time.time()
    
    for i in range(N):
        try:
            try:
                raise ValueError("Inner error")
            except ValueError as e:
                context = ErrorContext(
                    source="test.chain",
                    operation="inner_op",
                    error_code=f"CHAIN-{i:03d}",
                    severity=ErrorSeverity.ERROR
                )
                raise DatabaseError("Outer error", error_context=context) from e
        except DatabaseError:
            pass
    
    end_time = time.time()
    chains_per_second = N / (end_time - start_time)
    assert chains_per_second > 1000  # At least 1000 chains per second
```

### 2. Rate Limiter Performance

#### Window Calculation
- Benchmark window start/end calculations
- Test performance under high concurrency
- Measure memory usage for window tracking
- Test sliding window performance

#### Key Generation
- Benchmark key generation performance
- Test key collision handling
- Measure memory usage for key storage
- Test key cleanup performance

### 3. API Performance

#### Request Handling
- Measure request processing time
- Test concurrent request handling
- Monitor memory usage during peak load
- Benchmark response serialization

#### Error Response Generation
- Test error response creation time
- Measure error context serialization
- Benchmark error logging performance
- Test error recovery impact

## Performance Benchmarks

### Error Handling Benchmarks

### Rate Limiter Benchmarks

```python
def test_rate_limiter_performance():
    """Benchmark rate limiter performance"""
    limiter = RateLimiter(max_requests=1000, window_seconds=60)
    N = 10000
    start_time = time.time()
    
    for i in range(N):
        key = f"client_{i % 100}"
        limiter.check_limit(key)
    
    end_time = time.time()
    checks_per_second = N / (end_time - start_time)
    assert checks_per_second > 10000  # At least 10K checks per second
```

### API Benchmarks

```python
@pytest.mark.asyncio
async def test_api_performance():
    """Benchmark API request handling"""
    app = FastAPI()
    N = 1000
    
    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}
    
    async with AsyncClient(app=app) as client:
        start_time = time.time()
        
        tasks = [
            client.get("/test")
            for _ in range(N)
        ]
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        requests_per_second = N / (end_time - start_time)
        assert requests_per_second > 500  # At least 500 requests per second
```

## Memory Usage Testing

### Error Context Memory

```python
def test_error_context_memory():
    """Test error context memory usage"""
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    contexts = []
    
    # Create 100K error contexts
    for i in range(100000):
        context = ErrorContext(
            source="test.memory",
            operation=f"operation_{i}",
            error_code=f"MEM-{i:05d}",
            severity=ErrorSeverity.ERROR
        )
        contexts.append(context)
    
    final_memory = process.memory_info().rss
    memory_per_context = (final_memory - initial_memory) / len(contexts)
    assert memory_per_context < 1024  # Less than 1KB per context
```

### Rate Limiter Memory

```python
def test_rate_limiter_memory():
    """Test rate limiter memory usage"""
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    limiter = RateLimiter(max_requests=1000, window_seconds=60)
    
    # Test with 10K unique clients
    for i in range(10000):
        key = f"client_{i}"
        limiter.check_limit(key)
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    assert memory_increase < 10 * 1024 * 1024  # Less than 10MB total
```

## Concurrency Testing

### Thread Safety

```python
def test_thread_safety():
    """Test thread safety under load"""
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
    
    start_time = time.time()
    [t.start() for t in threads]
    [t.join() for t in threads]
    end_time = time.time()
    
    total_time = end_time - start_time
    assert total_time < 5.0  # Complete in under 5 seconds
    assert error_counts["ValidationError"] == 5000  # Correct error count
```

### Async Performance

```python
@pytest.mark.asyncio
async def test_async_error_handling():
    """Test async error handling performance"""
    app = FastAPI()
    
    @app.get("/test-error")
    @with_api_error_handling
    async def test_endpoint():
        raise ValidationError(
            "Test error",
            error_context=ErrorContext(
                source="test.async",
                operation="async_test",
                error_code="ASYNC-001",
                severity=ErrorSeverity.ERROR
            )
        )
    
    async with AsyncClient(app=app) as client:
        start_time = time.time()
        
        tasks = [
            client.get("/test-error")
            for _ in range(100)
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        assert total_time < 2.0  # Complete 100 requests in under 2 seconds
```

## Best Practices

### Performance Testing
1. Set clear performance targets
2. Use realistic data volumes
3. Test under various loads
4. Monitor resource usage
5. Measure latency distributions

### Memory Management
1. Track memory leaks
2. Monitor garbage collection
3. Test memory cleanup
4. Set memory budgets
5. Profile memory usage

### Concurrency
1. Test thread safety
2. Measure contention
3. Profile lock usage
4. Test scaling behavior
5. Monitor deadlocks

### Monitoring
1. Track key metrics
2. Set up alerts
3. Monitor trends
4. Log performance data
5. Analyze bottlenecks

## Performance Requirements

### Error Handling
1. Error context creation: > 5000/sec
2. Error chain creation: > 1000/sec
3. Memory per context: < 1KB
4. Cleanup efficiency: < 5MB retained after 50K errors
5. Log processing: > 500/sec

### Concurrency
1. Thread safety: 10 threads x 1000 operations < 5s
2. Async handling: 100 concurrent errors < 2s
3. No memory leaks under load
4. Consistent performance under contention
5. Efficient lock usage

### Monitoring
1. Real-time metric collection
2. Performance trend analysis
3. Resource usage tracking
4. Alert thresholds
5. Performance degradation detection

## Common Issues and Solutions

### Memory Leaks
1. Error context retention
2. Unclosed resources
3. Circular references
4. Cache growth
5. Thread locals

### Performance Bottlenecks
1. Lock contention
2. Excessive logging
3. Slow error serialization
4. Resource exhaustion
5. GC pressure

### Solutions
1. Regular cleanup
2. Resource pooling
3. Efficient serialization
4. Lock optimization
5. Monitoring and alerts 
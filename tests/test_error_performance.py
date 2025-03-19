"""
Performance tests for unified error handling framework.

Tests the performance characteristics of the ErrorContext-based error handling system
including error creation, formatting, concurrent handling, circuit breaking, and memory usage.
"""

import time
import pytest
import psutil
import gc
from typing import List, Optional, Dict
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime
import threading
import multiprocessing
import asyncio
import logging

from app.core.errors.base import (
    ErrorContext, ErrorSeverity, BaseError, 
    APIError, ValidationError, DatabaseError,
    RetryableError, CriticalError, WarningError,
    ErrorCode, ErrorSource
)
from app.core.errors.api import with_api_error_handling
from app.core.errors.validation import with_validation_error_handling
from app.core.errors.db import with_db_error_handling
from app.core.utils.retry import with_retry
from app.core.utils.circuit_breaker import CircuitBreaker
from app.core.utils.datetime import get_utc_now


def test_error_context_creation_performance():
    """Test performance of error context creation."""
    start_time = time.time()
    contexts: List[ErrorContext] = []
    
    # Create 10,000 error contexts
    for i in range(10000):
        context = ErrorContext(
            source="test.performance",
            operation=f"operation_{i}",
            error_code=f"PERF-TEST-{i:03d}",
            severity=ErrorSeverity.ERROR,
            additional_data={"index": i}
        )
        contexts.append(context)
    
    end_time = time.time()
    creation_time = end_time - start_time
    
    # Should create 10,000 contexts in less than 1 second
    assert creation_time < 1.0
    assert len(contexts) == 10000
    assert all(isinstance(ctx.timestamp, datetime) for ctx in contexts)


def test_error_serialization_performance():
    """Test performance of error context serialization."""
    context = ErrorContext(
        source="test.performance",
        operation="test_operation",
        error_code="PERF-SER-001",
        severity=ErrorSeverity.ERROR,
        additional_data={"test": "value"}
    )
    error = ValidationError(
        "Test error",
        error_context=context
    )
    
    start_time = time.time()
    
    # Serialize error 100,000 times
    for _ in range(100000):
        str(error)
        error.error_context.to_dict()
        error.to_dict()
    
    end_time = time.time()
    serialization_time = end_time - start_time
    
    # Should serialize 100,000 times in less than 1 second
    assert serialization_time < 1.0


def test_error_handling_concurrent():
    """Test error handling under concurrent load."""
    @with_api_error_handling
    def worker(i: int) -> Optional[str]:
        if i % 2 == 0:
            ctx = ErrorContext(
                source="test.concurrent",
                operation="worker_operation",
                error_code=f"PERF-CONC-{i:03d}",
                severity=ErrorSeverity.ERROR,
                additional_data={"worker_id": i}
            )
            raise APIError(f"Error in worker {i}", error_context=ctx)
        return f"Success {i}"
    
    start_time = time.time()
    results = []
    errors = []
    
    # Test with thread pool
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(worker, i) for i in range(100)]
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                if result:
                    results.append(result)
            except APIError as e:
                errors.append(e)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Should complete 100 operations in less than 1 second
    assert execution_time < 1.0
    assert len(results) == 50  # Half should succeed
    assert len(errors) == 50   # Half should fail
    assert all(isinstance(e.error_context, ErrorContext) for e in errors)


def test_retry_performance():
    """Test performance of retry mechanism."""
    attempts = []
    
    @with_retry(max_attempts=3, retry_delay=0.001)
    @with_api_error_handling
    def flaky_function(succeed_after: int) -> str:
        attempts.append(1)
        if len(attempts) < succeed_after:
            ctx = ErrorContext(
                source="test.retry",
                operation="flaky_operation",
                error_code="PERF-RETRY-001",
                severity=ErrorSeverity.ERROR,
                additional_data={"attempt": len(attempts)}
            )
            raise APIError("Temporary error", error_context=ctx)
        return "Success"
    
    start_time = time.time()
    
    # Test 100 retries
    for i in range(100):
        attempts.clear()
        try:
            if i % 2 == 0:
                # Will succeed on second attempt
                result = flaky_function(2)
                assert result == "Success"
                assert len(attempts) == 2
            else:
                # Will fail all attempts
                with pytest.raises(APIError) as exc_info:
                    flaky_function(4)
                error = exc_info.value
                assert error.error_context.error_code == "PERF-RETRY-001"
                assert len(attempts) == 3
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
    
    end_time = time.time()
    retry_time = end_time - start_time
    
    # Should complete 100 retry sequences in less than 2 seconds
    assert retry_time < 2.0


def test_circuit_breaker_performance():
    """Test performance of circuit breaker under load."""
    breaker = CircuitBreaker(
        "test_service",
        failure_threshold=5,
        reset_timeout=0.01
    )
    success_count = 0
    failure_count = 0
    
    @breaker
    @with_api_error_handling
    def service_call(should_fail: bool) -> str:
        if should_fail:
            ctx = ErrorContext(
                source="test.circuit_breaker",
                operation="service_call",
                error_code="PERF-CIRC-001",
                severity=ErrorSeverity.ERROR,
                additional_data={"should_fail": should_fail}
            )
            raise APIError("Service error", error_context=ctx)
        return "Success"
    
    start_time = time.time()
    
    # Make 1000 service calls
    for i in range(1000):
        try:
            # Alternate between success and failure
            result = service_call(i % 2 == 0)
            if result == "Success":
                success_count += 1
        except APIError as e:
            failure_count += 1
            assert e.error_context.error_code == "PERF-CIRC-001"
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        
        # Add small delay to allow circuit breaker to reset
        if i % 100 == 0:
            time.sleep(0.01)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Should complete 1000 operations in less than 3 seconds
    assert execution_time < 3.0
    assert success_count > 0
    assert failure_count > 0
    assert success_count + failure_count == 1000


def test_error_context_memory_usage():
    """Test memory usage of error context creation and handling."""
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    contexts: List[ErrorContext] = []
    
    # Create 100,000 error contexts with nested data
    for i in range(100000):
        context = ErrorContext(
            source="test.memory",
            operation=f"operation_{i}",
            error_code=f"MEM-TEST-{i:03d}",
            severity=ErrorSeverity.ERROR,
            additional_data={
                "index": i,
                "nested": {
                    "data": "test" * 10,
                    "list": list(range(10))
                }
            }
        )
        contexts.append(context)
    
    # Force garbage collection
    gc.collect()
    
    # Check memory usage
    final_memory = process.memory_info().rss
    memory_increase = (final_memory - initial_memory) / (1024 * 1024)  # Convert to MB
    
    # Should not exceed 100MB for 100,000 contexts
    assert memory_increase < 100
    contexts.clear()
    gc.collect()


def test_error_context_thread_safety():
    """Test thread safety of error context handling."""
    error_counts: Dict[str, int] = {}
    lock = threading.Lock()
    
    def worker(worker_id: int):
        for i in range(1000):
            try:
                if i % 3 == 0:
                    raise ValidationError(
                        "Validation error",
                        error_context=ErrorContext(
                            source="test.thread",
                            operation=f"worker_{worker_id}",
                            error_code=f"THREAD-{worker_id:02d}",
                            severity=ErrorSeverity.ERROR
                        )
                    )
                elif i % 3 == 1:
                    raise DatabaseError(
                        "Database error",
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
    
    start_time = time.time()
    threads = []
    for i in range(10):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Should complete all operations in less than 2 seconds
    assert execution_time < 2.0
    assert error_counts["ValidationError"] > 0
    assert error_counts["DatabaseError"] > 0


@pytest.mark.asyncio
async def test_async_error_performance():
    """Test performance of async error handling."""
    async def async_worker(i: int):
        try:
            if i % 2 == 0:
                raise APIError(
                    "Async error",
                    error_context=ErrorContext(
                        source="test.async",
                        operation=f"async_worker_{i}",
                        error_code=f"ASYNC-{i:03d}",
                        severity=ErrorSeverity.ERROR
                    )
                )
            await asyncio.sleep(0.001)
            return f"Success {i}"
        except Exception as e:
            return e
    
    start_time = time.time()
    
    # Run 1000 async operations concurrently
    tasks = [async_worker(i) for i in range(1000)]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Should complete 1000 async operations in less than 2 seconds
    assert execution_time < 2.0
    assert len([r for r in results if isinstance(r, str)]) == 500
    assert len([r for r in results if isinstance(r, APIError)]) == 500


def test_error_logging_performance():
    """Test performance of error logging."""
    logger = logging.getLogger("error_test")
    logger.setLevel(logging.ERROR)
    log_count = 0
    
    def log_handler(record):
        nonlocal log_count
        log_count += 1
    
    handler = logging.Handler()
    handler.handle = log_handler
    logger.addHandler(handler)
    
    start_time = time.time()
    
    # Log 10,000 errors
    for i in range(10000):
        error = APIError(
            f"Error {i}",
            error_context=ErrorContext(
                source="test.logging",
                operation=f"log_operation_{i}",
                error_code=f"LOG-{i:04d}",
                severity=ErrorSeverity.ERROR,
                additional_data={"index": i}
            )
        )
        logger.error(str(error), extra={"error_context": error.error_context.to_dict()})
    
    end_time = time.time()
    logging_time = end_time - start_time
    
    # Should log 10,000 errors in less than 1 second
    assert logging_time < 1.0
    assert log_count == 10000


def test_error_context_chain_performance():
    """Test performance of error context chaining."""
    def create_error_chain(depth: int) -> BaseError:
        context = None
        for i in range(depth):
            context = ErrorContext(
                source=f"test.chain.{i}",
                operation=f"chain_operation_{i}",
                error_code=f"CHAIN-{i:03d}",
                severity=ErrorSeverity.ERROR,
                parent_context=context,
                additional_data={"depth": i}
            )
        return APIError("Chain error", error_context=context)
    
    start_time = time.time()
    chains = []
    
    # Create 1000 error chains with depth 10
    for _ in range(1000):
        error = create_error_chain(10)
        chains.append(error)
        str(error)  # Force string representation
        error.to_dict()  # Force serialization
    
    end_time = time.time()
    chain_time = end_time - start_time
    
    # Should create and process 1000 chains in less than 1 second
    assert chain_time < 1.0
    assert len(chains) == 1000
    assert all(isinstance(e, APIError) for e in chains)


def test_circuit_breaker_recovery_performance():
    """Test performance of circuit breaker recovery."""
    breaker = CircuitBreaker(
        "test_recovery",
        failure_threshold=3,
        reset_timeout=0.01
    )
    
    @breaker
    @with_api_error_handling
    def service_call(cycle: int) -> str:
        if cycle < 3:
            raise APIError(
                "Service error",
                error_context=ErrorContext(
                    source="test.circuit_breaker",
                    operation="recovery_test",
                    error_code="CIRC-REC-001",
                    severity=ErrorSeverity.ERROR
                )
            )
        return "Success"
    
    start_time = time.time()
    cycles = 0
    successes = 0
    
    # Test recovery cycles
    for _ in range(100):
        try:
            result = service_call(cycles)
            if result == "Success":
                successes += 1
                cycles = 0
            else:
                cycles += 1
        except APIError:
            cycles += 1
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        
        if cycles >= 3:
            time.sleep(0.01)  # Allow circuit breaker to reset
            cycles = 0
    
    end_time = time.time()
    recovery_time = end_time - start_time
    
    # Should complete 100 recovery cycles in less than 2 seconds
    assert recovery_time < 2.0
    assert successes > 0


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 
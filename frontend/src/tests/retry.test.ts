import { retryOperation } from '../lib/errorHandling';
import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import { ApiError } from '../lib/errorHandling';

describe('Retry Operation', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.clearAllMocks();
  });

  it('should retry a failed operation up to maxAttempts times', async () => {
    const operation = jest.fn<() => Promise<string>>()
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockResolvedValue('Success');

    const promise = retryOperation(operation, 3);
    
    // First retry
    await jest.advanceTimersByTimeAsync(1000);
    // Second retry
    await jest.advanceTimersByTimeAsync(2000);
    // Wait for the final attempt
    await jest.advanceTimersByTimeAsync(4000);

    const result = await promise;
    expect(result).toBe('Success');
    expect(operation).toHaveBeenCalledTimes(3);
  });

  it('should fail after maxAttempts unsuccessful retries', async () => {
    const networkError = new Error('Network Error');
    const operation = jest.fn<() => Promise<string>>()
      .mockRejectedValueOnce(networkError)
      .mockRejectedValueOnce(networkError)
      .mockRejectedValueOnce(networkError);

    const promise = retryOperation(operation, 3);
    
    // First retry
    await jest.advanceTimersByTimeAsync(1000);
    // Second retry
    await jest.advanceTimersByTimeAsync(2000);
    // Final attempt
    await jest.advanceTimersByTimeAsync(4000);

    await expect(promise).rejects.toEqual(expect.any(Object));
    expect(operation).toHaveBeenCalledTimes(3);
  });

  it('should succeed immediately if first attempt is successful', async () => {
    const operation = jest.fn<() => Promise<string>>().mockResolvedValue('Success');

    const result = await retryOperation(operation);

    expect(result).toBe('Success');
    expect(operation).toHaveBeenCalledTimes(1);
  });

  it('should use default maxAttempts if not specified', async () => {
    const operation = jest.fn<() => Promise<string>>()
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockResolvedValue('Success');

    const promise = retryOperation(operation);
    
    // First retry
    await jest.advanceTimersByTimeAsync(1000);
    // Second retry
    await jest.advanceTimersByTimeAsync(2000);
    // Wait for the final attempt
    await jest.advanceTimersByTimeAsync(4000);

    const result = await promise;
    expect(result).toBe('Success');
    expect(operation).toHaveBeenCalledTimes(3);
  });

  it('should retry with increasing delays', async () => {
    const operation = jest.fn<() => Promise<string>>()
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockResolvedValue('Success');

    const promise = retryOperation(operation, 3);
    
    // First retry
    await jest.advanceTimersByTimeAsync(1000);
    // Second retry
    await jest.advanceTimersByTimeAsync(2000);
    // Wait for the final attempt
    await jest.advanceTimersByTimeAsync(4000);

    const result = await promise;
    expect(result).toBe('Success');
    expect(operation).toHaveBeenCalledTimes(3);
  });
}); 
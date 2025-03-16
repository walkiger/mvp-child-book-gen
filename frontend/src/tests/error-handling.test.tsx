import { formatApiError, isRetryableError, retryOperation } from '../lib/errorHandling';
import { AxiosError } from 'axios';
import { describe, it, expect, jest } from '@jest/globals';

describe('Error Handling Utilities', () => {
  describe('formatApiError', () => {
    it('should format network errors', () => {
      const error = new Error('Network Error');
      const formatted = formatApiError(error);
      
      expect(formatted).toEqual({
        message: 'Unable to connect to the server. Please check your internet connection.',
        code: 'NETWORK_ERROR',
        details: 'Network Error',
        retry: true
      });
    });

    it('should format rate limit errors', () => {
      const error = new AxiosError(
        'Rate limit exceeded',
        '429',
        undefined,
        undefined,
        {
          status: 429,
          data: { detail: 'Too many requests' }
        } as any
      );
      
      const formatted = formatApiError(error);
      expect(formatted).toEqual({
        message: 'Rate limit exceeded. Please try again later.',
        code: 'RATE_LIMIT',
        details: 'Too many requests',
        retry: true
      });
    });

    it('should format authentication errors', () => {
      const error = new AxiosError(
        'Unauthorized',
        '401',
        undefined,
        undefined,
        { status: 401 } as any
      );
      
      const formatted = formatApiError(error);
      expect(formatted).toEqual({
        message: 'Your session has expired. Please log in again.',
        code: 'UNAUTHORIZED',
        retry: false
      });
    });
  });

  describe('isRetryableError', () => {
    it('should identify retryable errors', () => {
      const retryableErrors = [
        { message: 'Rate limit error', code: 'RATE_LIMIT', retry: true },
        { message: 'Network error', code: 'NETWORK_ERROR', retry: true },
        { message: 'Server error', code: 'SERVER_ERROR', retry: true }
      ];

      retryableErrors.forEach(error => {
        expect(isRetryableError(error)).toBe(true);
      });
    });

    it('should identify non-retryable errors', () => {
      const nonRetryableErrors = [
        { message: 'Unauthorized', code: 'UNAUTHORIZED', retry: false },
        { message: 'Validation error', code: 'VALIDATION_ERROR', retry: false },
        { message: 'Not found', code: 'NOT_FOUND', retry: false }
      ];

      nonRetryableErrors.forEach(error => {
        expect(isRetryableError(error)).toBe(false);
      });
    });
  });

  describe('retryOperation', () => {
    it('should retry failed operations up to max attempts', async () => {
      const mockOperation = jest.fn<() => Promise<string>>();
      let attempts = 0;
      
      mockOperation.mockImplementation(async () => {
        attempts++;
        if (attempts < 3) {
          throw new Error('Network Error');
        }
        return 'success';
      });

      const result = await retryOperation(mockOperation);
      expect(result).toBe('success');
      expect(mockOperation).toHaveBeenCalledTimes(3);
    });

    it('should not retry non-retryable errors', async () => {
      const mockOperation = jest.fn<() => Promise<never>>();
      mockOperation.mockRejectedValue(new AxiosError(
        'Unauthorized',
        '401',
        undefined,
        undefined,
        { status: 401 } as any
      ));

      await expect(retryOperation(mockOperation)).rejects.toEqual({
        message: 'Your session has expired. Please log in again.',
        code: 'UNAUTHORIZED',
        retry: false
      });
      expect(mockOperation).toHaveBeenCalledTimes(1);
    });
  });
}); 
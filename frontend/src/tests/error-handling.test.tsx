import { formatApiError, isRetryableError, retryOperation } from '../lib/errorHandling';
import { AxiosError } from 'axios';
import { describe, it, expect, jest } from '@jest/globals';
import { render, screen, waitFor } from '@testing-library/react';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { APIError, ValidationAPIError, AuthenticationAPIError, RateLimitAPIError, NotFoundAPIError } from '../types/errors';

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

describe('Error Handling', () => {
  it('shows API error details', () => {
    const error = new APIError({
      message: 'An unexpected error occurred',
      error_code: 'API-ERR-001',
      http_status: 500,
      details: 'Internal server error details'
    });

    render(<ErrorDisplay error={error} />);
    
    expect(screen.getByText('An unexpected error occurred')).toBeInTheDocument();
    expect(screen.getByText('Error Code: API-ERR-001')).toBeInTheDocument();
    expect(screen.getByText('Internal server error details')).toBeInTheDocument();
  });

  it('shows validation error details', () => {
    const error = new ValidationAPIError({
      message: 'Validation failed',
      details: 'Invalid input data',
      error_code: 'API-VAL-001'
    });

    render(<ErrorDisplay error={error} />);
    
    expect(screen.getByText('Validation failed')).toBeInTheDocument();
    expect(screen.getByText('Error Code: API-VAL-001')).toBeInTheDocument();
    expect(screen.getByText('Invalid input data')).toBeInTheDocument();
  });

  it('shows authentication error details', () => {
    const error = new AuthenticationAPIError({
      message: 'Authentication failed',
      details: 'Invalid credentials',
      error_code: 'API-AUTH-001'
    });

    render(<ErrorDisplay error={error} />);
    
    expect(screen.getByText('Authentication failed')).toBeInTheDocument();
    expect(screen.getByText('Error Code: API-AUTH-001')).toBeInTheDocument();
    expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
  });

  it('shows rate limit error details', () => {
    const error = new RateLimitAPIError({
      message: 'Rate limit exceeded',
      details: 'Try again in 60 seconds',
      error_code: 'API-RATE-001',
      reset_after: 60
    });

    render(<ErrorDisplay error={error} />);
    
    expect(screen.getByText('Rate limit exceeded')).toBeInTheDocument();
    expect(screen.getByText('Error Code: API-RATE-001')).toBeInTheDocument();
    expect(screen.getByText('Try again in 60 seconds')).toBeInTheDocument();
  });

  it('shows not found error details', () => {
    const error = new NotFoundAPIError({
      message: 'Resource not found',
      details: 'The requested story does not exist',
      error_code: 'API-404-001'
    });

    render(<ErrorDisplay error={error} />);
    
    expect(screen.getByText('Resource not found')).toBeInTheDocument();
    expect(screen.getByText('Error Code: API-404-001')).toBeInTheDocument();
    expect(screen.getByText('The requested story does not exist')).toBeInTheDocument();
  });

  it('handles missing details', () => {
    const error = new APIError({
      message: 'Simple error',
      error_code: 'API-ERR-002'
    });

    render(<ErrorDisplay error={error} />);
    
    expect(screen.getByText('Simple error')).toBeInTheDocument();
    expect(screen.getByText('Error Code: API-ERR-002')).toBeInTheDocument();
    expect(screen.queryByTestId('error-details')).not.toBeInTheDocument();
  });

  it('handles retry functionality', async () => {
    const onRetry = jest.fn();
    const error = new APIError({
      message: 'Retryable error',
      error_code: 'API-ERR-003'
    });

    render(<ErrorDisplay error={error} onRetry={onRetry} />);
    
    const retryButton = screen.getByText('Retry');
    retryButton.click();
    
    await waitFor(() => {
      expect(onRetry).toHaveBeenCalledTimes(1);
    });
  });
}); 
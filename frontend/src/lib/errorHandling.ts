import { AxiosError } from 'axios';

export interface ApiError {
  message: string;
  code?: string;
  details?: string;
  retry?: boolean;
}

export function formatApiError(error: unknown): ApiError {
  if (error instanceof AxiosError) {
    const response = error.response;
    if (!response) {
      return {
        message: 'Network error occurred.',
        code: 'NETWORK_ERROR',
        details: error.message,
        retry: true
      };
    }
    
    const status = response.status;
    if (status === 429) {
      return {
        message: 'Rate limit exceeded. Please try again later.',
        code: 'RATE_LIMIT',
        details: response.data?.detail,
        retry: true
      };
    }
    if (status === 401) {
      return {
        message: 'Your session has expired. Please log in again.',
        code: 'UNAUTHORIZED',
        retry: false
      };
    }
    if (status === 403) {
      return {
        message: 'You do not have permission to perform this action.',
        code: 'FORBIDDEN',
        retry: false
      };
    }
    if (status === 404) {
      return {
        message: 'The requested resource was not found.',
        code: 'NOT_FOUND',
        retry: false
      };
    }
    if (status >= 500) {
      return {
        message: 'Server error. Please try again later.',
        code: 'SERVER_ERROR',
        details: response.data?.detail,
        retry: true
      };
    }
    return {
      message: response.data?.detail || 'An unexpected error occurred.',
      code: `HTTP_${status}`,
      details: response.data?.message,
      retry: status >= 500
    };
  }
  
  if (error instanceof Error) {
    if (error.message.includes('Network Error')) {
      return {
        message: 'Unable to connect to the server. Please check your internet connection.',
        code: 'NETWORK_ERROR',
        details: error.message,
        retry: true
      };
    }
    return {
      message: error.message,
      code: 'CLIENT_ERROR',
      details: error.stack,
      retry: false
    };
  }
  
  return {
    message: 'An unexpected error occurred.',
    code: 'UNKNOWN_ERROR',
    details: String(error),
    retry: false
  };
}

export function isRetryableError(error: ApiError): boolean {
  return error.retry || [
    'RATE_LIMIT',
    'NETWORK_ERROR',
    'SERVER_ERROR'
  ].includes(error.code || '');
}

export function getRetryDelay(error: ApiError, attempt: number): number {
  if (error.code === 'RATE_LIMIT') {
    return Math.min(1000 * Math.pow(2, attempt), 30000); // Exponential backoff, max 30s
  }
  return Math.min(500 * Math.pow(2, attempt), 5000); // Exponential backoff, max 5s
}

export async function retryOperation<T>(
  operation: () => Promise<T>,
  maxAttempts: number = 3
): Promise<T> {
  let lastError: ApiError | null = null;
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = formatApiError(error);
      if (!isRetryableError(lastError) || attempt === maxAttempts - 1) {
        throw lastError;
      }
      const delay = getRetryDelay(lastError, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
} 
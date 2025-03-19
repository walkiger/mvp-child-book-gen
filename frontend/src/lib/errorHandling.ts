import { AxiosError } from 'axios';

export interface APIErrorParams {
  message: string;
  error_code: string;
  details?: Record<string, any>;
  source?: string;
  severity?: string;
  timestamp?: string;
  error_id?: string;
  additional_data?: Record<string, any>;
  suggestions?: string[];
  http_status: number;
}

export class APIError {
  message: string;
  error_code: string;
  details?: Record<string, any>;
  source?: string;
  severity?: string;
  timestamp?: string;
  error_id?: string;
  additional_data?: Record<string, any>;
  suggestions?: string[];
  http_status: number;

  constructor(params: APIErrorParams) {
    this.message = params.message;
    this.error_code = params.error_code;
    this.details = params.details;
    this.source = params.source;
    this.severity = params.severity;
    this.timestamp = params.timestamp;
    this.error_id = params.error_id;
    this.additional_data = params.additional_data;
    this.suggestions = params.suggestions;
    this.http_status = params.http_status;
  }

  toJSON() {
    return {
      message: this.message,
      error_code: this.error_code,
      details: this.details,
      source: this.source,
      severity: this.severity,
      timestamp: this.timestamp,
      error_id: this.error_id,
      additional_data: this.additional_data,
      suggestions: this.suggestions,
      http_status: this.http_status
    };
  }
}

export function formatApiError(error: unknown): APIError {
  if (error instanceof AxiosError && error.response?.data) {
    return new APIError({
      message: error.response.data.message || 'An error occurred',
      error_code: error.response.data.error_code || 'UNKNOWN_ERROR',
      details: error.response.data.details,
      source: error.response.data.source,
      severity: error.response.data.severity,
      timestamp: error.response.data.timestamp,
      error_id: error.response.data.error_id,
      additional_data: error.response.data.additional_data,
      suggestions: error.response.data.suggestions,
      http_status: error.response.status
    });
  }

  if (error instanceof Error) {
    return new APIError({
      message: error.message,
      error_code: 'CLIENT_ERROR',
      details: { stack: error.stack },
      http_status: 500
    });
  }

  return new APIError({
    message: 'An unexpected error occurred',
    error_code: 'UNKNOWN_ERROR',
    http_status: 500
  });
}

export function isRetryableError(error: APIError): boolean {
  if (!error) return false;
  
  // Network errors and rate limit errors are retryable
  if (error.error_code === 'NETWORK_ERROR' || error.error_code === 'RATE_LIMIT') {
    return true;
  }
  
  // 5xx errors are retryable
  if (error.http_status >= 500) {
    return true;
  }
  
  return false;
}

export function getRetryDelay(error: APIError, attempt: number): number {
  const baseDelay = 1000; // 1 second
  
  if (error.error_code === 'RATE_LIMIT' && 'reset_after' in error) {
    return (error as any).reset_after * 1000;
  }
  
  // Exponential backoff with jitter
  return Math.min(baseDelay * Math.pow(2, attempt) + Math.random() * 1000, 10000);
}

export async function retryOperation<T>(
  operation: () => Promise<T>,
  maxAttempts: number = 3
): Promise<T> {
  let lastError: APIError | null = null;
  
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
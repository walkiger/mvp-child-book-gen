// Error types for API error handling
export interface APIErrorParams {
  message: string;
  error_code: string;
  http_status?: number;
  details?: string;
  reset_after?: number;
}

export class APIError {
  message: string;
  error_code: string;
  http_status: number;
  details?: string;

  constructor(params: APIErrorParams) {
    this.message = params.message;
    this.error_code = params.error_code;
    this.http_status = params.http_status || 500;
    this.details = params.details;
  }

  toJSON() {
    return {
      message: this.message,
      error_code: this.error_code,
      http_status: this.http_status,
      details: this.details
    };
  }
}

export class ValidationAPIError extends APIError {
  constructor(params: APIErrorParams) {
    super({
      ...params,
      http_status: 422,
      error_code: params.error_code || 'API-VAL-001'
    });
  }
}

export class AuthenticationAPIError extends APIError {
  constructor(params: APIErrorParams) {
    super({
      ...params,
      http_status: 401,
      error_code: params.error_code || 'API-AUTH-001'
    });
  }
}

export class RateLimitAPIError extends APIError {
  reset_after: number;

  constructor(params: APIErrorParams) {
    super({
      ...params,
      http_status: 429,
      error_code: params.error_code || 'API-RATE-001'
    });
    this.reset_after = params.reset_after || 60;
  }

  toJSON() {
    return {
      ...super.toJSON(),
      reset_after: this.reset_after
    };
  }
}

export class NotFoundAPIError extends APIError {
  constructor(params: APIErrorParams) {
    super({
      ...params,
      http_status: 404,
      error_code: params.error_code || 'API-404-001'
    });
  }
}

// Export default for compatibility
export default {
  APIError,
  ValidationAPIError,
  AuthenticationAPIError,
  RateLimitAPIError,
  NotFoundAPIError
}; 
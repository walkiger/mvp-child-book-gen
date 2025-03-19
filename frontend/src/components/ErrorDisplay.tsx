import React from 'react';
import { APIError } from '../lib/errorHandling';

interface ErrorDisplayProps {
  error: APIError;
  onRetry?: () => void;
  onClose?: () => void;
  fullPage?: boolean;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, onRetry, onClose, fullPage }) => {
  const renderDetails = () => {
    if (!error.details) return null;
    
    if (typeof error.details === 'string') {
      return <p className="mt-1" data-testid="error-details">{error.details}</p>;
    }
    
    return (
      <div className="mt-1" data-testid="error-details">
        {Object.entries(error.details).map(([key, value]) => (
          <p key={key}>{key}: {JSON.stringify(value)}</p>
        ))}
      </div>
    );
  };

  return (
    <div 
      className="bg-red-50 border border-red-200 rounded-lg p-4 my-4" 
      role="alert"
      data-testid="error-display-container"
      style={fullPage ? { minHeight: '60vh' } : {}}
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">{error.message}</h3>
          <div className="mt-2 text-sm text-red-700">
            <p className="font-mono">Error Code: {error.error_code}</p>
            {renderDetails()}
            {'reset_after' in error && (
              <p className="mt-1">Please try again in {(error as any).reset_after} seconds</p>
            )}
          </div>
          <div className="mt-4 flex gap-2">
            {onRetry && (
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Retry
              </button>
            )}
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                Close
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ErrorDisplay; 
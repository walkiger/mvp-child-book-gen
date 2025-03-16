import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, jest } from '@jest/globals';
import '@testing-library/jest-dom';
import ErrorDisplay from '../components/ErrorDisplay';
import { ApiError } from '../lib/errorHandling';

describe('ErrorDisplay Component', () => {
  const mockError: ApiError = {
    message: 'Test error message',
    code: 'TEST_ERROR',
    details: 'Error details',
    retry: true
  };

  it('renders error message and code', () => {
    render(<ErrorDisplay error={mockError} />);
    
    expect(screen.getByText('TEST_ERROR')).toBeInTheDocument();
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('renders error details when provided', () => {
    render(<ErrorDisplay error={mockError} />);
    
    expect(screen.getByText('Error details')).toBeInTheDocument();
  });

  it('shows retry button when retry is true and onRetry provided', () => {
    const onRetry = jest.fn();
    render(<ErrorDisplay error={mockError} onRetry={onRetry} />);
    
    const retryButton = screen.getByRole('button', { name: /retry/i });
    expect(retryButton).toBeInTheDocument();
    
    fireEvent.click(retryButton);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('does not show retry button when retry is false', () => {
    const onRetry = jest.fn();
    const errorWithoutRetry = { ...mockError, retry: false };
    render(<ErrorDisplay error={errorWithoutRetry} onRetry={onRetry} />);
    
    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
  });

  it('shows close button when onClose provided', () => {
    const onClose = jest.fn();
    render(<ErrorDisplay error={mockError} onClose={onClose} />);
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    expect(closeButton).toBeInTheDocument();
    
    fireEvent.click(closeButton);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('renders in full page mode when fullPage is true', () => {
    render(<ErrorDisplay error={mockError} fullPage />);
    
    const container = screen.getByTestId('error-display-container');
    expect(container).toHaveStyle({
      minHeight: '60vh'
    });
  });
}); 
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from '@jest/globals';
import LoadingState from '../components/LoadingState';

describe('LoadingState Component', () => {
  it('renders spinner variant with text', () => {
    render(<LoadingState variant="spinner" text="Loading..." />);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders skeleton variant with specified count', () => {
    render(<LoadingState variant="skeleton" skeletonCount={3} />);
    
    const skeletons = screen.getAllByTestId('skeleton');
    expect(skeletons).toHaveLength(3);
  });

  it('renders spinner with custom height', () => {
    render(<LoadingState variant="spinner" height="200px" />);
    
    const container = screen.getByTestId('loading-container');
    expect(container).toHaveStyle({ height: '200px' });
  });

  it('renders skeleton with custom height', () => {
    render(<LoadingState variant="skeleton" height="150px" />);
    
    const container = screen.getByTestId('loading-container');
    expect(container).toHaveStyle({ height: '150px' });
  });

  it('renders spinner by default when no variant specified', () => {
    render(<LoadingState />);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
}); 
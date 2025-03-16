import '@testing-library/jest-dom';
import { expect, jest } from '@jest/globals';

// Add custom Jest DOM matchers to global Jest types
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeInTheDocument(): R;
      toHaveStyle(style: Record<string, any>): R;
    }
  }
} 
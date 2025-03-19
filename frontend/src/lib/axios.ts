/// <reference types="vite/client" />

import axios from 'axios'
import { formatApiError } from './errorHandling'

// Create axios instance
const instance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
  timeout: 30000, // 30 seconds default timeout
  withCredentials: true,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
})

// Add request interceptor
instance.interceptors.request.use(
  (config) => {
    // Get token from localStorage
    const token = localStorage.getItem('token')
    
    // If token exists, add it to request headers
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Set longer timeout for image generation endpoints
    if (config.url?.includes('/api/images/generate') || 
        config.url?.includes('/api/characters/generate-image')) {
      config.timeout = 120000; // 2 minutes for image generation
    }

    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(formatApiError(error))
  }
)

// Add response interceptor
instance.interceptors.response.use(
  (response) => {
    // Handle rate limit headers
    if (response.headers['x-ratelimit-remaining']) {
      // Store rate limit info for UI components to access
      window.rateLimitInfo = {
        requests: parseInt(response.headers['x-ratelimit-remaining'] || '0'),
        tokens: parseInt(response.headers['x-tokenlimit-remaining'] || '0'),
        resetIn: parseInt(response.headers['x-ratelimit-reset'] || '60'),
        timestamp: Date.now()
      }
    }
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // Handle token refresh
    if (error.response?.status === 401) {
      // Skip token refresh for auth endpoints
      if (originalRequest.url?.includes('/api/auth/')) {
        return Promise.reject(error);
      }

      // Check if this is a token verification error
      const isTokenVerificationError = error.response?.data?.detail?.includes('Signature verification failed');
      if (isTokenVerificationError) {
        localStorage.removeItem('token');
        window.location.href = '/login';
        return Promise.reject(error);
      }

      // Only attempt refresh if not already retrying and we have a token
      const token = localStorage.getItem('token');
      if (!error.config._retry && token) {
        error.config._retry = true;
        try {
          const response = await instance.post('/api/auth/refresh');
          const { access_token } = response.data;
          localStorage.setItem('token', access_token);
          
          // Update the failed request's authorization header
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return instance(originalRequest);
        } catch (e) {
          // If refresh fails, clear token and redirect to login
          localStorage.removeItem('token');
          window.location.href = '/login';
          return Promise.reject(e);
        }
      }
    }

    // Handle timeout errors specifically
    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      const retryCount = originalRequest._retryCount || 0;
      if (retryCount < 2) { // Allow up to 2 retries
        originalRequest._retryCount = retryCount + 1;
        return instance(originalRequest);
      }
    }

    // Handle rate limit errors
    if (error.response?.status === 429) {
      const retryAfter = parseInt(error.response.headers['retry-after'] || '60');
      const retryCount = originalRequest._retryCount || 0;
      
      if (retryCount < 2) { // Allow up to 2 retries
        originalRequest._retryCount = retryCount + 1;
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
        return instance(originalRequest);
      }
    }

    // Handle other errors
    console.error('Response error:', {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message,
    });

    return Promise.reject(formatApiError(error));
  }
)

// Add typings for window object
declare global {
  interface Window {
    rateLimitInfo?: {
      requests: number
      tokens: number
      resetIn: number
      timestamp: number
    }
  }
}

export default instance 
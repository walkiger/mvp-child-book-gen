/// <reference types="vite/client" />

import axios from 'axios'
import { formatApiError } from './errorHandling'

// Create axios instance
const instance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000, // 30 seconds
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
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Try to refresh token
        const response = await instance.post('/api/auth/refresh')
        const { access_token } = response.data

        // Update token in localStorage
        localStorage.setItem('token', access_token)

        // Update Authorization header
        originalRequest.headers.Authorization = `Bearer ${access_token}`

        // Retry the original request
        return instance(originalRequest)
      } catch (refreshError) {
        // If refresh fails, clear token and reject with original error
        localStorage.removeItem('token')
        console.error('Token refresh failed:', refreshError)
        return Promise.reject(formatApiError(error))
      }
    }

    // Handle other errors
    console.error('Response error:', {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message,
    })

    return Promise.reject(formatApiError(error))
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
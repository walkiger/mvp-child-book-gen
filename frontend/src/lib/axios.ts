import axios from 'axios'

// Create axios instance
const instance = axios.create({
  baseURL: 'http://localhost:8080',
  timeout: 30000, // 30 seconds
  withCredentials: true,
  headers: {
    'Accept': 'application/json',
  },
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
})

// Add request interceptor
instance.interceptors.request.use(
  (config) => {
    // Add authorization header if token exists
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }

    // Set Content-Type based on data type
    if (config.data instanceof URLSearchParams) {
      config.headers['Content-Type'] = 'application/x-www-form-urlencoded'
      // Convert URLSearchParams to string
      config.data = config.data.toString()
    } else if (!(config.data instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json'
    }

    return config
  },
  (error) => Promise.reject(error)
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
  (error) => {
    // Handle response errors
    if (error.response) {
      // Handle rate limit error
      if (error.response.status === 429) {
        // Store rate limit info
        window.rateLimitInfo = {
          requests: 0,
          tokens: 0,
          resetIn: parseInt(error.response.headers['x-ratelimit-reset'] || '60'),
          timestamp: Date.now()
        }
      }
      
      // Handle token expiration
      if (error.response.status === 401) {
        // Redirect to login if token is invalid/expired
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
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
import { create } from 'zustand'
import { AxiosError } from 'axios'
import axios from '../lib/axios'  // Use our custom axios instance

interface User {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  is_admin?: boolean  // Add optional is_admin field
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  token: string | null
  isAdmin: boolean     // Add isAdmin property
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, username: string, first_name: string, last_name: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
}

const useAuth = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  token: localStorage.getItem('token'),
  isAdmin: false,      // Initialize isAdmin state
  login: async (email: string, password: string) => {
    try {
      console.log('Attempting login...');
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await axios.post('/api/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      if (response.status === 200) {
        const data = response.data;
        localStorage.setItem('token', data.access_token);
        
        // Fetch user data to get admin status
        const userResponse = await axios.get('/api/auth/me', {
          headers: {
            Authorization: `Bearer ${data.access_token}`,
          },
        });
        
        const userData = userResponse.data;
        
        set({ 
          token: data.access_token, 
          user: userData, 
          isAuthenticated: true,
          isAdmin: userData.is_admin || false // Set isAdmin based on user data
        });
      }
    } catch (error: any) {
      console.error('Login failed:', error);
      if (error instanceof AxiosError) {
        console.error('Error details:', {
          message: error.message,
          code: error.code,
          response: {
            data: error.response?.data,
            status: error.response?.status,
            headers: error.response?.headers,
          },
          request: {
            url: error.config?.url,
            method: error.config?.method,
            headers: error.config?.headers,
            data: error.config?.data,
          }
        });
      }
      throw error;
    }
  },
  register: async (email: string, password: string, username: string, first_name: string, last_name: string) => {
    try {
      const response = await axios.post('/api/auth/register', {
        email,
        password,
        username,
        first_name,
        last_name,
      });
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      
      // Get user data after successful registration
      const userResponse = await axios.get('/api/auth/me');
      const user = userResponse.data;
      
      set({ token: access_token, user, isAuthenticated: true });
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  },
  logout: () => {
    localStorage.removeItem('token')
    set({ token: null, user: null, isAuthenticated: false, isAdmin: false })
  },
  checkAuth: async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        set({ user: null, isAuthenticated: false, isAdmin: false });
        return;
      }

      const response = await axios.get('/api/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (response.status === 200) {
        const userData = response.data;
        set({ 
          user: userData, 
          isAuthenticated: true, 
          token,
          isAdmin: userData.is_admin || false // Set isAdmin based on user data
        });
      } else {
        localStorage.removeItem('token');
        set({ user: null, isAuthenticated: false, token: null, isAdmin: false });
      }
    } catch (error) {
      localStorage.removeItem('token');
      set({ user: null, isAuthenticated: false, token: null, isAdmin: false });
    }
  }
}))

export default useAuth 
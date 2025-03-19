import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { isAxiosError } from 'axios';
import axiosInstance from '../lib/axios';
import { APIError, formatApiError } from '../lib/errorHandling';
import { useNavigate } from 'react-router-dom';

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error: APIError | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  clearError: () => void;
}

interface User {
  id: number;
  email: string;
  username: string;
  avatar_url?: string;
}

interface RegisterData {
  email: string;
  username: string;
  password: string;
  first_name: string;
  last_name: string;
}

export const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  user: null,
  loading: true,
  error: null,
  login: async () => {},
  logout: async () => {},
  register: async () => {},
  clearError: () => {},
});

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIError | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    // Skip check if no token exists
    const token = localStorage.getItem('token');
    if (!token) {
      setUser(null);
      setIsAuthenticated(false);
      setLoading(false);
      return;
    }

    try {
      // Try to get user info
      const response = await axiosInstance.get('/api/auth/me');
      setUser(response.data);
      setIsAuthenticated(true);
      setError(null);
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 401) {
        // Token is invalid or expired, try to refresh
        try {
          const refreshResponse = await axiosInstance.post('/api/auth/refresh');
          const { access_token, user: userData } = refreshResponse.data;
          localStorage.setItem('token', access_token);
          setUser(userData);
          setIsAuthenticated(true);
          setError(null);
        } catch (refreshErr) {
          // Refresh failed, clear auth state
          localStorage.removeItem('token');
          setUser(null);
          setIsAuthenticated(false);
          if (isAxiosError(refreshErr) && refreshErr.response?.status !== 401) {
            setError(formatApiError(refreshErr));
          }
        }
      } else if (isAxiosError(err)) {
        setError(formatApiError(err));
      }
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      
      const response = await axiosInstance.post('/api/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      const { access_token, user: userData } = response.data;
      localStorage.setItem('token', access_token);
      setUser(userData);
      setIsAuthenticated(true);
      navigate('/dashboard'); // Redirect to dashboard after successful login
    } catch (err) {
      setError(formatApiError(err));
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    setError(null);
    try {
      await axiosInstance.post('/api/auth/logout');
    } catch (err) {
      console.error('Logout error:', err);
      // Continue with local logout even if server request fails
    } finally {
      localStorage.removeItem('token');
      setUser(null);
      setIsAuthenticated(false);
      setLoading(false);
      navigate('/login');
    }
  };

  const register = async (userData: RegisterData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axiosInstance.post('/api/auth/register', userData);
      const { access_token, user: registeredUser } = response.data;
      localStorage.setItem('token', access_token);
      setUser(registeredUser);
      setIsAuthenticated(true);
      navigate('/dashboard'); // Redirect to dashboard after successful registration
    } catch (err) {
      setError(formatApiError(err));
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const clearError = () => {
    setError(null);
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        user,
        loading,
        error,
        login,
        logout,
        register,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}; 
import React, { createContext, useState, useEffect, ReactNode } from 'react';
import axios, { AxiosError, isAxiosError } from 'axios';
import axiosInstance from '../lib/axios';
import { ApiError, formatApiError } from '../lib/errorHandling';

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error: ApiError | null;
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
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await axiosInstance.get('/api/auth/me');
      setUser(response.data);
      setIsAuthenticated(true);
      setError(null);
    } catch (err) {
      setUser(null);
      setIsAuthenticated(false);
      // Don't set error for 401 responses during auth check
      if (isAxiosError(err) && err.response?.status !== 401) {
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
      const response = await axios.post('/api/auth/login', { email, password });
      setUser(response.data);
      setIsAuthenticated(true);
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
      await axios.post('/api/auth/logout');
      setUser(null);
      setIsAuthenticated(false);
    } catch (err) {
      setError(formatApiError(err));
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData: RegisterData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('/api/auth/register', userData);
      setUser(response.data);
      setIsAuthenticated(true);
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
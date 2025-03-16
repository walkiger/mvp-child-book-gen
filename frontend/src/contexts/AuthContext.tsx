import React, { createContext, ReactNode, useEffect } from 'react';
import useAuth from '../hooks/useAuth';

// Create context with default value
const AuthContext = createContext<ReturnType<typeof useAuth> | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const auth = useAuth();
  
  // Check authentication status on mount
  useEffect(() => {
    auth.checkAuth();
  }, []);
  
  return (
    <AuthContext.Provider value={auth}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext; 
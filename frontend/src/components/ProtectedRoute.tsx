import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { Box } from '@mui/material';
import useAuth from '../hooks/useAuth';
import LoadingState from './LoadingState';
import ErrorDisplay from './ErrorDisplay';

const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, loading, error } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <LoadingState variant="spinner" text="Checking authentication..." />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <ErrorDisplay error={error} />
      </Box>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login page with return URL
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute; 
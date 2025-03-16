import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box, Container } from '@mui/material';
import Navbar from './Navbar';
import useAuth from '../hooks/useAuth';
import ErrorDisplay from './ErrorDisplay';

const Layout: React.FC = () => {
  const { error, clearError } = useAuth();

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar />
      <Container component="main" sx={{ flex: 1, py: 4 }}>
        {error && (
          <Box sx={{ mb: 4 }}>
            <ErrorDisplay error={error} onClose={clearError} />
          </Box>
        )}
        <Outlet />
      </Container>
    </Box>
  );
};

export default Layout; 
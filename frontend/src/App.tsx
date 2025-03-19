import React, { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Stories from './pages/Stories';
import StoryBuilder from './pages/StoryBuilder';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import Characters from './pages/Characters';
import CharacterCreate from './pages/CharacterCreate';
import ErrorBoundary from './components/ErrorBoundary';
import LoadingState from './components/LoadingState';

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Suspense fallback={
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
            <LoadingState variant="spinner" text="Loading application..." />
          </Box>
        }>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/login" replace />} />
              <Route path="login" element={<Login />} />
              <Route path="register" element={<Register />} />
              
              <Route element={<ProtectedRoute />}>
                <Route path="dashboard" element={<Home />} />
                <Route path="stories" element={<Stories />} />
                <Route path="story-builder" element={<StoryBuilder />} />
                <Route path="characters" element={<Characters />} />
                <Route path="characters/create" element={<CharacterCreate />} />
              </Route>
            </Route>
          </Routes>
        </Suspense>
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default App; 
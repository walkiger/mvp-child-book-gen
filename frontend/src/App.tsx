import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Stories from './pages/Stories';
import StoryBuilder from './pages/StoryBuilder';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import Characters from './pages/Characters';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />
          
          <Route element={<ProtectedRoute />}>
            <Route path="stories" element={<Stories />} />
            <Route path="story-builder" element={<StoryBuilder />} />
            <Route path="characters" element={<Characters />} />
          </Route>
        </Route>
      </Routes>
    </AuthProvider>
  );
};

export default App; 
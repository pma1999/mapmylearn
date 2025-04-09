import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { useAuth } from '../services/authContext';

/**
 * A wrapper component for routes that require authentication.
 * Redirects to login page if user is not authenticated.
 */
const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (adminOnly && !user?.is_admin) {
    // Redirect to home if not an admin but trying to access admin-only route
    return <Navigate to="/" replace />;
  }

  // Render the protected content if authenticated
  return children;
};

export default ProtectedRoute; 
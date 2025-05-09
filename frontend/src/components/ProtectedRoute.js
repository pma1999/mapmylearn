import React, { useRef } from 'react';
import { Navigate, useLocation } from 'react-router';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '../services/authContext';

/**
 * A wrapper component for routes that require authentication.
 * Redirects to login page if user is not authenticated.
 * Relies on AuthContext for loading and authentication state.
 */
const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, user, loading, isLoggingOut } = useAuth();
  const location = useLocation();

  // Show loading spinner while AuthContext is initializing or a logout is actively processing.
  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <CircularProgress />
        <Typography variant="body2" sx={{ mt: 2 }}>
          Verifying authentication...
        </Typography>
      </Box>
    );
  }

  // After AuthContext is done loading (loading is false):
  // If a logout is in progress, we might want to show a specific message or rely on isAuthenticated being false.
  // For simplicity, if isLoggingOut is true, isAuthenticated should also be false, leading to login redirect.
  if (!isAuthenticated) { 
    // If isLoggingOut is true, the user is effectively not authenticated for accessing protected routes.
    // The redirect to login is appropriate.
    console.log('ProtectedRoute: Not authenticated, redirecting to login.', { isAuthenticated, loading, isLoggingOut, user: !!user });
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check admin access if required
  if (adminOnly && !user?.is_admin) {
    console.log('ProtectedRoute: Admin access required, but user is not admin. Redirecting.');
    return <Navigate to="/" replace />;
  }

  // Render the protected content if authenticated (and admin check passes if applicable)
  return children;
};

export default ProtectedRoute; 
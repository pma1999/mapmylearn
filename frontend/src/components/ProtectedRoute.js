import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '../services/authContext';

/**
 * A wrapper component for routes that require authentication.
 * Redirects to login page if user is not authenticated.
 * Handles session rehydration for expired tokens.
 */
const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, user, loading, initAuth, isLoggingOut } = useAuth();
  const location = useLocation();
  const [authChecked, setAuthChecked] = useState(false);
  const [isRehydrating, setIsRehydrating] = useState(false);
  const [rehydrationAttempted, setRehydrationAttempted] = useState(false);

  // Effect to handle session rehydration
  useEffect(() => {
    const checkAndRehydrateSession = async () => {
      // Skip rehydration if logout is in progress
      if (isLoggingOut) { 
        console.log('Logout in progress, skipping rehydration check.');
        return; 
      }

      // Only attempt rehydration if not authenticated and not already attempted
      if (!isAuthenticated && !rehydrationAttempted && !loading) {
        try {
          console.log('Attempting to rehydrate session');
          setIsRehydrating(true);
          
          // Force a re-initialization of auth state
          await initAuth();
          
          // Mark rehydration as attempted regardless of outcome
          setRehydrationAttempted(true);
        } catch (err) {
          console.error('Session rehydration failed:', err);
        } finally {
          setIsRehydrating(false);
          setAuthChecked(true);
        }
      } else if (!authChecked) {
        // If no rehydration needed, mark auth as checked
        setAuthChecked(true);
      }
    };

    checkAndRehydrateSession();
  }, [isAuthenticated, rehydrationAttempted, loading, initAuth, authChecked, isLoggingOut]);

  // Show loading spinner while checking authentication or rehydrating
  if (loading || isRehydrating) {
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
          {isRehydrating ? 'Restoring your session...' : 'Verifying authentication...'}
        </Typography>
      </Box>
    );
  }

  // After rehydration attempt, if still not authenticated, redirect to login
  if (!isAuthenticated && authChecked) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check admin access if required
  if (adminOnly && !user?.is_admin) {
    // Redirect to home if not an admin but trying to access admin-only route
    return <Navigate to="/" replace />;
  }

  // Render the protected content if authenticated
  return children;
};

export default ProtectedRoute; 
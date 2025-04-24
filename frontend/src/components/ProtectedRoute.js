import React, { useState, useEffect, useRef } from 'react';
import { Navigate, useLocation } from 'react-router';
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
  const isMountedRef = useRef(true);

  // Effect to handle session rehydration
  useEffect(() => {
    // Set mount status on mount
    isMountedRef.current = true;

    const checkAndRehydrateSession = async () => {
      // Skip rehydration if logout is in progress
      if (isLoggingOut) { 
        console.log('Logout in progress, skipping rehydration check.');
        // Ensure authChecked is true if we skip, otherwise loading might persist
        if (isMountedRef.current) {
          setAuthChecked(true); 
        }
        return; 
      }

      // Only attempt rehydration if not authenticated and not already attempted
      // Also ensure component is still mounted before starting async operation
      if (!isAuthenticated && !rehydrationAttempted && !loading && isMountedRef.current) {
        try {
          console.log('Attempting to rehydrate session');
          // Check mount status before setting state
          if (isMountedRef.current) setIsRehydrating(true); 
          
          // Force a re-initialization of auth state
          await initAuth();
          
          // Mark rehydration as attempted regardless of outcome
          // Check mount status before setting state
          if (isMountedRef.current) setRehydrationAttempted(true); 

        } catch (err) {
          // Handle errors potentially thrown by initAuth (other than the caught refresh error)
          console.error('Session rehydration failed in ProtectedRoute:', err);
          // Potentially set an error state here if needed
        } finally {
          // Check mount status before setting state in finally block
          if (isMountedRef.current) {
            setIsRehydrating(false);
            setAuthChecked(true);
          }
        }
      } else if (!authChecked && isMountedRef.current) {
        // If no rehydration needed, mark auth as checked (only if mounted)
        setAuthChecked(true);
      }
    };

    checkAndRehydrateSession();

    // Cleanup function: Set mount status to false when component unmounts
    return () => {
      isMountedRef.current = false;
    };
    // Dependencies: Ensure all necessary dependencies are included.
    // initAuth is a stable function from context, but including it follows linting rules.
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
import React, { createContext, useState, useEffect, useContext } from 'react';
import * as api from './api';

// Create authentication context
const AuthContext = createContext(null);

// Custom hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Authentication provider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tokenRefreshTimer, setTokenRefreshTimer] = useState(null);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = () => {
      try {
        const authData = localStorage.getItem('auth');
        if (authData) {
          const parsedAuth = JSON.parse(authData);
          if (parsedAuth.user && parsedAuth.accessToken) {
            setUser(parsedAuth.user);
            setupTokenRefresh(parsedAuth.expiresIn);
            
            // Fetch initial credit information
            fetchUserCredits();
          }
        }
      } catch (err) {
        console.error('Error initializing auth:', err);
      } finally {
        setLoading(false);
      }
    };

    initAuth();

    // Cleanup on unmount
    return () => {
      if (tokenRefreshTimer) {
        clearTimeout(tokenRefreshTimer);
      }
    };
  }, []);

  // Set up token refresh
  const setupTokenRefresh = (expiresInSeconds) => {
    if (tokenRefreshTimer) {
      clearTimeout(tokenRefreshTimer);
    }

    // Refresh token 5 minutes before expiration
    const refreshTime = (expiresInSeconds - 300) * 1000;
    const timer = setTimeout(refreshToken, refreshTime > 0 ? refreshTime : 0);
    setTokenRefreshTimer(timer);
  };

  // Refresh the access token
  const refreshToken = async () => {
    try {
      const response = await api.refreshAuthToken();
      const { access_token, expires_in, user: userData } = response;
      
      updateAuthState(access_token, expires_in, userData);
    } catch (err) {
      console.error('Token refresh failed:', err);
      // If refresh fails, log out the user
      logout();
    }
  };

  // Fetch user credits
  const fetchUserCredits = async () => {
    if (!user) return;
    
    try {
      const { credits } = await api.getUserCredits();
      
      // Only update if credits changed to prevent unnecessary renders
      if (user.credits !== credits) {
        setUser(prevUser => ({
          ...prevUser,
          credits
        }));
        
        // Update localStorage
        const authData = localStorage.getItem('auth');
        if (authData) {
          const parsedAuth = JSON.parse(authData);
          parsedAuth.user = {
            ...parsedAuth.user,
            credits
          };
          localStorage.setItem('auth', JSON.stringify(parsedAuth));
        }
      }
    } catch (err) {
      console.error('Failed to fetch user credits:', err);
    }
  };

  // Update authentication state
  const updateAuthState = (accessToken, expiresIn, userData) => {
    // Update state
    setUser(userData);
    
    // Store in localStorage
    localStorage.setItem('auth', JSON.stringify({
      accessToken,
      expiresIn,
      user: userData
    }));

    // Configure API with the new token
    api.setAuthToken(accessToken);

    // Setup token refresh timer
    setupTokenRefresh(expiresIn);

    return userData;
  };

  // Register a new user
  const register = async (email, password, fullName) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.register(email, password, fullName);
      const { access_token, expires_in, user: userData } = response;
      
      updateAuthState(access_token, expires_in, userData);
      return userData;
    } catch (err) {
      setError(err.message || 'Registration failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Log in an existing user
  const login = async (email, password, rememberMe) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.login(email, password, rememberMe);
      const { access_token, expires_in, user: userData } = response;
      
      updateAuthState(access_token, expires_in, userData);
      return userData;
    } catch (err) {
      setError(err.message || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Log out the current user
  const logout = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Clear auth token timer
      if (tokenRefreshTimer) {
        clearTimeout(tokenRefreshTimer);
        setTokenRefreshTimer(null);
      }
      
      // Call logout API
      await api.logout();
      
      // Clear local auth data
      localStorage.removeItem('auth');
      setUser(null);
      api.clearAuthToken();
      
      // Offer to migrate learning paths from localStorage on next login
      localStorage.setItem('pendingMigration', 'true');
    } catch (err) {
      console.error('Logout error:', err);
      // Still clear local auth data even if API call fails
      localStorage.removeItem('auth');
      setUser(null);
      api.clearAuthToken();
    } finally {
      setLoading(false);
    }
  };

  // Migrate learning paths from localStorage to the user's account
  const migrateLearningPaths = async () => {
    try {
      if (!user) {
        throw new Error('User must be logged in to migrate learning paths');
      }
      
      // Get all local history
      const localHistory = api.getLocalHistoryRaw();
      
      if (!localHistory || !localHistory.entries || localHistory.entries.length === 0) {
        return { success: true, migrated_count: 0 };
      }
      
      // Call migration API
      const result = await api.migrateLearningPaths(localHistory.entries);
      
      // Clear pending migration flag
      localStorage.removeItem('pendingMigration');
      
      // Clear local history after successful migration
      if (result.success) {
        api.clearLocalHistory();
      }
      
      return result;
    } catch (err) {
      console.error('Migration error:', err);
      throw err;
    }
  };

  // Check if there are learning paths to migrate
  const checkPendingMigration = () => {
    const pendingMigration = localStorage.getItem('pendingMigration') === 'true';
    const localHistory = api.getLocalHistoryRaw();
    const hasLocalPaths = localHistory && localHistory.entries && localHistory.entries.length > 0;
    
    return pendingMigration && hasLocalPaths;
  };

  // Context value
  const value = {
    user,
    loading,
    error,
    register,
    login,
    logout,
    migrateLearningPaths,
    checkPendingMigration,
    isAuthenticated: !!user,
    fetchUserCredits // Export the function to allow manual refresh of credits
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}; 
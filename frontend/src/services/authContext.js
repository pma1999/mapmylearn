import React, { createContext, useState, useEffect, useContext, useRef } from 'react';
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
  const [refreshInProgress, setRefreshInProgress] = useState(false);
  const refreshAttempts = useRef(0);
  const MAX_REFRESH_ATTEMPTS = 3;

  // Function to check if token is expired or about to expire
  const isTokenExpiredOrExpiring = (expiresAt) => {
    if (!expiresAt) return true;
    
    try {
      // Check if within 5 minutes of expiration (300 seconds)
      const currentTime = Math.floor(Date.now() / 1000);
      const bufferTime = 300; // 5 minutes in seconds
      return currentTime + bufferTime >= expiresAt;
    } catch (err) {
      console.error('Error checking token expiration:', err);
      return true; // Assume expired on error
    }
  };

  // Attempt to silently refresh the token if it exists but is expired
  const attemptSilentRefresh = async () => {
    try {
      setRefreshInProgress(true);
      
      if (refreshAttempts.current >= MAX_REFRESH_ATTEMPTS) {
        console.warn('Maximum refresh attempts reached, forcing logout');
        logout();
        return false;
      }
      
      refreshAttempts.current += 1;
      
      console.log('Attempting silent token refresh');
      const response = await api.refreshAuthToken();
      const { access_token, expires_in, user: userData } = response;
      
      // Reset refresh attempts counter on success
      refreshAttempts.current = 0;
      
      updateAuthState(access_token, expires_in, userData);
      return true;
    } catch (err) {
      console.error('Silent refresh failed:', err);
      return false;
    } finally {
      setRefreshInProgress(false);
    }
  };

  // Initialize auth state
  const initAuth = async () => {
    try {
      setLoading(true);
      const authData = localStorage.getItem('auth');
      
      if (authData) {
        const parsedAuth = JSON.parse(authData);
        
        if (parsedAuth.user && parsedAuth.accessToken) {
          // Check if token is expired or about to expire
          const isExpired = isTokenExpiredOrExpiring(parsedAuth.tokenExpiry);
          
          if (isExpired) {
            console.log('Stored token is expired or about to expire, attempting refresh');
            const refreshed = await attemptSilentRefresh();
            
            if (!refreshed) {
              // If refresh failed but we have user data, set as logged out but keep user info
              // This provides a smoother experience if they need to log back in
              localStorage.removeItem('auth');
              setUser(null);
              api.clearAuthToken();
            }
          } else {
            // Token is still valid
            console.log('Using valid stored token');
            setUser(parsedAuth.user);
            api.setAuthToken(parsedAuth.accessToken);
            setupTokenRefresh(parsedAuth.expiresIn, parsedAuth.tokenExpiry);
            
            // Fetch initial credit information
            fetchUserCredits();
          }
        }
      }
    } catch (err) {
      console.error('Error initializing auth:', err);
    } finally {
      setLoading(false);
    }
  };

  // Initialize auth when component mounts
  useEffect(() => {
    initAuth();
    
    // Listen for visibility changes (user returning to tab)
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && user) {
        // Check if token needs refresh when user returns to tab
        const authData = localStorage.getItem('auth');
        if (authData) {
          const parsedAuth = JSON.parse(authData);
          if (isTokenExpiredOrExpiring(parsedAuth.tokenExpiry)) {
            console.log('Token expired while page was inactive, refreshing');
            refreshToken();
          }
        }
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Sync auth state across tabs
    const handleStorageChange = (e) => {
      if (e.key === 'auth') {
        if (!e.newValue) {
          // Auth was cleared in another tab
          setUser(null);
          api.clearAuthToken();
        } else if (e.newValue !== e.oldValue) {
          // Auth was updated in another tab
          const parsedAuth = JSON.parse(e.newValue);
          if (parsedAuth.user && parsedAuth.accessToken) {
            setUser(parsedAuth.user);
            api.setAuthToken(parsedAuth.accessToken);
            setupTokenRefresh(parsedAuth.expiresIn, parsedAuth.tokenExpiry);
          }
        }
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    
    // Cleanup on unmount
    return () => {
      if (tokenRefreshTimer) {
        clearTimeout(tokenRefreshTimer);
      }
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  // Set up token refresh
  const setupTokenRefresh = (expiresInSeconds, tokenExpiry) => {
    if (tokenRefreshTimer) {
      clearTimeout(tokenRefreshTimer);
    }

    // Calculate time to refresh (15% of token lifetime before expiration)
    const refreshBuffer = Math.floor(expiresInSeconds * 0.15);
    const refreshTime = (expiresInSeconds - refreshBuffer) * 1000;
    
    console.log(`Setting up token refresh in ${refreshTime/1000} seconds`);
    
    // Set minimum refresh time to avoid immediate refresh loops
    const safeRefreshTime = Math.max(refreshTime, 10000); // At least 10 seconds
    
    const timer = setTimeout(refreshToken, safeRefreshTime > 0 ? safeRefreshTime : 0);
    setTokenRefreshTimer(timer);
  };

  // Refresh the access token
  const refreshToken = async () => {
    // Prevent multiple simultaneous refresh attempts
    if (refreshInProgress) {
      console.log('Refresh already in progress, skipping');
      return;
    }
    
    try {
      setRefreshInProgress(true);
      console.log('Refreshing authentication token');
      
      const response = await api.refreshAuthToken();
      const { access_token, expires_in, user: userData } = response;
      
      console.log('Token successfully refreshed');
      refreshAttempts.current = 0; // Reset counter on success
      
      updateAuthState(access_token, expires_in, userData);
    } catch (err) {
      console.error('Token refresh failed:', err);
      
      // If refresh fails, try again with exponential backoff
      if (refreshAttempts.current < MAX_REFRESH_ATTEMPTS) {
        refreshAttempts.current += 1;
        const backoffTime = Math.pow(2, refreshAttempts.current) * 1000; // Exponential backoff
        console.log(`Scheduling retry attempt ${refreshAttempts.current} in ${backoffTime/1000} seconds`);
        
        setTimeout(refreshToken, backoffTime);
      } else {
        console.warn('Maximum refresh attempts reached, logging out');
        // If all retries fail, log out the user
        logout();
      }
    } finally {
      setRefreshInProgress(false);
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
    
    // Calculate token expiry timestamp
    const tokenExpiry = Math.floor(Date.now() / 1000) + expiresIn;
    
    // Store in localStorage
    localStorage.setItem('auth', JSON.stringify({
      accessToken,
      expiresIn,
      tokenExpiry,
      user: userData
    }));

    // Configure API with the new token
    api.setAuthToken(accessToken);

    // Setup token refresh timer
    setupTokenRefresh(expiresIn, tokenExpiry);

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
      
      // Reset refresh attempts
      refreshAttempts.current = 0;
      
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
    fetchUserCredits, // Export the function to allow manual refresh of credits
    refreshToken,     // Allow manual refresh if needed
    initAuth          // Allow force re-initialization of auth
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}; 
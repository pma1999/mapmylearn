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
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const refreshAttempts = useRef(0);
  const MAX_REFRESH_ATTEMPTS = 3;
  const refreshPromise = useRef(null); // To store the promise during refresh
  const [showWelcomeModal, setShowWelcomeModal] = useState(false); // New state
  const WELCOME_FLAG_KEY = 'mapmylearn_welcome_shown';

  // Function to check if token is expired or about to expire
  const isTokenExpiredOrExpiring = (expiresAt) => {
    if (!expiresAt) return true;
    
    try {
      // Check if within 1 minute of expiration (60 seconds) - Reduced buffer
      const currentTime = Math.floor(Date.now() / 1000);
      const bufferTime = 60; // 1 minute in seconds
      return currentTime + bufferTime >= expiresAt;
    } catch (err) {
      console.error('Error checking token expiration:', err);
      return true; // Assume expired on error
    }
  };

  // Centralized function to update authentication state
  const updateAuthState = (accessToken, expiresIn, userData) => {
    const tokenExpiry = Math.floor(Date.now() / 1000) + expiresIn;
    const authData = {
      accessToken,
      expiresIn,
      tokenExpiry,
      user: userData,
    };
    
    setUser(userData);
    api.setAuthToken(accessToken);
    localStorage.setItem('auth', JSON.stringify(authData));
    setupTokenRefresh(expiresIn, tokenExpiry);
    setError(null); // Clear previous errors on successful auth update

    // Check if welcome modal should be shown (only after successful login/refresh)
    const welcomeShown = localStorage.getItem(WELCOME_FLAG_KEY);
    if (!welcomeShown) {
        setShowWelcomeModal(true); // Show the modal
    }
  };

  // Function to mark welcome modal as shown
  const markWelcomeModalShown = () => {
    localStorage.setItem(WELCOME_FLAG_KEY, 'true');
    setShowWelcomeModal(false);
  };
  
  // Logout function
  const logout = async () => {
    if (isLoggingOut) {
      console.log('Logout already in progress, skipping redundant call.');
      return;
    }
    setIsLoggingOut(true);
    console.log('Logging out user...');

    if (tokenRefreshTimer) {
      clearTimeout(tokenRefreshTimer);
      setTokenRefreshTimer(null);
    }
    refreshPromise.current = null; // Clear any pending refresh promise immediately

    // All other state updates and API calls will be in a try/finally
    try {
      setUser(null);
      // setError(null); // setError should be called based on actual errors, not generically on logout.
                      // If a session expiration message is desired, it should be set by the caller or a specific event.
      api.clearAuthToken();
      localStorage.removeItem('auth');
      // localStorage.removeItem(WELCOME_FLAG_KEY); // Optional: uncomment to show welcome again on next login
      setShowWelcomeModal(false); // Ensure modal is hidden on logout
      setRefreshInProgress(false); // Ensure refresh flag is reset
      refreshAttempts.current = 0; // Reset attempts on logout
      
      try {
        // Inform the backend about logout (optional, but good practice)
        await api.logout(); 
      } catch (err) {
        // Log non-critical API logout failure, but don't let it stop the client-side logout.
        console.warn('Logout API call failed (might be expected if token is already invalid or server unavailable):', err);
      }
      
      // Navigation is handled by ProtectedRoute via state change
    } finally {
      // This ensures that isLoggingOut is set to false even if an error occurs above (e.g., in api.logout())
      // though most critical state clearing is done before await.
      setIsLoggingOut(false); 
    }
  };

  // Unified and Robust Token Refresh Function
  const refreshToken = async () => {
    if (isLoggingOut) {
      console.warn('Token refresh aborted: Logout is in progress.');
      return Promise.reject(new Error('Logout in progress, refresh aborted'));
    }

    // If a refresh is already in progress, return the existing promise
    if (refreshInProgress && refreshPromise.current) {
      console.log('Refresh already in progress, returning existing promise.');
      return refreshPromise.current;
    }

    setRefreshInProgress(true);
    // refreshAttempts.current = 0; // Reset attempts for a new refresh sequence. Moved into executeRefresh start.
    console.log('Starting token refresh sequence.');

    const executeRefresh = async (attempt = 1) => {
      if (attempt === 1) { // Reset attempts only at the beginning of a new sequence
        refreshAttempts.current = 0;
      }
      refreshAttempts.current = attempt; // Keep track of current attempt for logging

      if (isLoggingOut) {
        console.warn('Token refresh attempt aborted mid-sequence: Logout is in progress.');
        setRefreshInProgress(false); // Clean up flag
        throw new Error('Logout in progress, refresh attempt cancelled');
      }
      
      console.log(`Attempting token refresh (Attempt ${attempt}/${MAX_REFRESH_ATTEMPTS})`);
      try {
        const response = await api.refreshAuthToken();
        const { access_token, expires_in, user: userData } = response;
        
        console.log('Token successfully refreshed.');
        updateAuthState(access_token, expires_in, userData);
        setRefreshInProgress(false);
        refreshAttempts.current = 0; // Reset counter on success
        refreshPromise.current = null; // Clear the promise on success
        return true; // Indicate success
      } catch (err) {
        console.error(`Token refresh attempt ${attempt} failed:`, err);
        
        // Check if it's an auth error (e.g., invalid refresh token) or max attempts reached
        if (err.response?.status === 401 || attempt >= MAX_REFRESH_ATTEMPTS) {
          if (isLoggingOut) {
            console.warn('Refresh failed likely due to an ongoing logout. Aborting this refresh path and not calling logout again.');
            // Do not call logout() again if one is already in progress.
          } else {
            console.warn(`Refresh failed permanently (status ${err.response?.status}) or max attempts reached. Logging out.`);
            // Call logout (which now only updates state and has its own guards)
            await logout(); 
          }
          // Common cleanup for permanent failure path
          setRefreshInProgress(false); 
          refreshPromise.current = null; // Clear the promise on failure
          // Throw the specific error to signal permanent failure upstream
          throw new Error("Token refresh failed permanently or due to logout."); 
        } else {
          // Schedule retry with exponential backoff
          const backoffTime = Math.pow(2, attempt) * 1000; // Exponential backoff (1s, 2s, 4s...)
          console.log(`Scheduling retry attempt ${attempt + 1} in ${backoffTime / 1000} seconds`);
          
          return new Promise(resolve => setTimeout(resolve, backoffTime))
            .then(() => executeRefresh(attempt + 1));
        }
      }
    };
    
    // Store the promise for the entire refresh sequence
    refreshPromise.current = executeRefresh();
    
    // Return the promise so callers can await the final result
    return refreshPromise.current.finally(() => {
        // Final cleanup, ensure flag is reset even if something unexpected happened
        setRefreshInProgress(false); 
        // Don't nullify the promise here if it's still being awaited elsewhere?
        // Let's reconsider - the promise is resolved/rejected, so it's fine to clear.
        refreshPromise.current = null; 
    });
  };


  // Wrapper function for initiating refresh, primarily used by initAuth
  // Returns the promise from refreshToken
  const attemptSilentRefresh = async () => {
    console.log("Attempting silent refresh via refreshToken function.");
    // Directly call the robust refreshToken function
    // No need for separate logic or attempts here anymore
    return refreshToken(); 
  };


  // Initialize auth state and trigger migration check
  const initAuth = async () => {
    try {
      // setLoading(true); // setLoading(true) is already called by the caller of initAuth in some cases or at the start of AuthProvider
      // Ensure loading is true at the start of this specific process
      setLoading(true); 
      setError(null); // Clear errors on init
      const authData = localStorage.getItem('auth');
      let isAuthenticated = false; // Track if user is authenticated after init
      let authUpdatedDuringInit = false; // Flag to check if updateAuthState was called
      
      if (authData) {
        const parsedAuth = JSON.parse(authData);
        
        if (parsedAuth.user && parsedAuth.accessToken && parsedAuth.tokenExpiry) {
           const isExpired = isTokenExpiredOrExpiring(parsedAuth.tokenExpiry);
          
          if (isExpired) {
            console.log('Stored token is expired or needs refresh, attempting silent refresh...');
            try {
              await attemptSilentRefresh(); 
              console.log("Silent refresh successful during init.");
              isAuthenticated = true; // User is authenticated after successful refresh
              authUpdatedDuringInit = true; // updateAuthState called in refreshToken
              // setLoading(false); // setLoading will be handled by the finally block of initAuth
            } catch (refreshError) {
              // Check if it's the specific error from refreshToken failure
              if (refreshError.message === "Token refresh failed permanently." || refreshError.message === "Token refresh failed permanently or due to logout." || refreshError.message === "Logout in progress, refresh aborted") {
                console.error("Silent refresh failed permanently or due to logout during init:", refreshError.message);
                // Logout state is already set by refreshToken calling logout() or refresh being aborted
                // We just need to ensure loading is false and stop further init steps
                // setLoading(false); // Handled by finally
                return; // Stop initialization here, user is logged out or logout is in progress
              } else {
                // Unexpected error during silent refresh attempt
                console.error("Unexpected error during silent refresh:", refreshError);
                setError("Failed to initialize session."); // Set a generic error
                // setLoading(false); // Moved to a finally block
                return; 
                // Optionally re-throw for higher-level error boundary: throw refreshError;
              }
            }
          } else {
            console.log('Using valid stored token.');
            updateAuthState(parsedAuth.accessToken, parsedAuth.expiresIn, parsedAuth.user);
            isAuthenticated = true; // User is authenticated with existing token
            authUpdatedDuringInit = true; // updateAuthState called here
            fetchUserCredits(); // Assuming this is defined later
            // setLoading(false); // Set loading false if token was valid
          }
        } else {
           console.log("Stored auth data incomplete, clearing.");
           // Logout ensures state is cleared properly
           await logout(); 
           // setLoading(false); 
        }
      } else {
         console.log("No stored auth data found.");
         setUser(null); 
         // setLoading(false); // No auth data, loading complete
      }
      
      // If user is authenticated but updateAuthState wasn't called during *this* init run
      // (e.g., token was valid), explicitly check if welcome needs showing.
      if (isAuthenticated && !authUpdatedDuringInit) {
          const welcomeShown = localStorage.getItem(WELCOME_FLAG_KEY);
          if (!welcomeShown) {
              setShowWelcomeModal(true);
          }
      }

      // --- Automatic Local History Migration --- 
      // REMOVED MIGRATION BLOCK
      // Ensure loading is false at the end of the process if not already set
      // setLoading(false); // Moved to a finally block
    } catch (err) {
      // Catch any unexpected errors during the broader init process (e.g., JSON parse)
      console.error("Critical error during auth initialization:", err);
      setError("Failed to initialize application.");
      setUser(null); // Ensure user is logged out
      api.clearAuthToken();
      localStorage.removeItem('auth');
      // setLoading(false); // Moved to a finally block
    } finally {
      // Always set loading to false at the end of initialization, regardless of path.
      setLoading(false);
    }
  };

  // Initialize auth when component mounts
  useEffect(() => {
    // Define async function inside useEffect or use IIFE
    const initialize = async () => {
      await initAuth();
    };
    initialize();
    
    // Listener for visibility changes (user returning to tab)
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && user) {
        // Check token validity when user returns
        const authData = localStorage.getItem('auth');
        if (authData) {
          try {
            const parsedAuth = JSON.parse(authData);
            if (parsedAuth.tokenExpiry && isTokenExpiredOrExpiring(parsedAuth.tokenExpiry)) {
              console.log('Token expired or needs refresh while page was inactive, initiating refresh.');
              // Call refreshToken directly - no need to await here, let it run in background
              // refreshToken handles logout on failure internally.
              refreshToken().catch(err => {
                  console.error("Background refresh triggered by visibility change failed:", err.message);
                  // Logout is handled within refreshToken if needed
              });
            }
          } catch (e) {
              console.error("Error parsing auth data on visibility change:", e);
              logout(); // Logout if stored data is corrupt
          }
        } else if (user) {
            // If we have a user state but no localStorage, logout to sync state
            console.warn("User state exists but no auth data in localStorage. Logging out.");
            logout();
        }
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Listener for storage changes (sync across tabs)
    const handleStorageChange = (e) => {
      if (e.key === 'auth') {
         console.log("Auth data changed in another tab/window.");
        if (!e.newValue) {
          // Auth was cleared in another tab - logout here too
          console.log("Auth cleared elsewhere. Logging out this tab.");
          // if (user) { // Only logout if currently logged in this tab -- logout() itself now handles if already logging out.
             logout();
          // }
        } else {
           // Auth was updated in another tab - re-initialize this tab's state from storage
           console.log("Auth updated elsewhere. Re-initializing this tab.");
           // Re-run initAuth to ensure consistency and potentially fetch new user data/credits
           initAuth(); 
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
     // Rerun useEffect only if needed - dependencies are tricky here.
     // Since initAuth/logout modify state, they might cause loops if included.
     // Empty array means run once on mount. This seems correct for setup/cleanup.
  }, []); 

  // Set up token refresh timer
  const setupTokenRefresh = (expiresInSeconds, tokenExpiry) => {
    if (tokenRefreshTimer) {
      clearTimeout(tokenRefreshTimer);
    }

    // Calculate time until token is considered "expiring" based on our check
    // const bufferTimeSeconds = 60; // Match the buffer in isTokenExpiredOrExpiring
    // Reduced buffer slightly to ensure refresh attempt starts before token is truly invalid for API calls.
    // The isTokenExpiredOrExpiring check still uses 60s for "is it considered expired by UI/logic"
    // This timer aims to refresh *before* that point.
    const refreshInitiationBufferSeconds = 90; // Try to refresh 90 seconds before it's "checked" as expired.
    
    const nowSeconds = Math.floor(Date.now() / 1000);
    // Time until we should *start* the refresh process
    let timeUntilRefreshStart = (tokenExpiry - refreshInitiationBufferSeconds - nowSeconds) * 1000;


    // Ensure refresh time is positive and has a minimum delay to avoid loops
    // If calculated time is negative (meaning we are already past the ideal refresh start time), refresh soon.
    if (timeUntilRefreshStart <= 0) {
        console.warn(`Token is already within the refresh initiation window (or past it). Scheduling refresh very soon.`);
        timeUntilRefreshStart = 5000; // Refresh in 5 seconds if already "late"
    }
    
    const safeRefreshTime = Math.max(timeUntilRefreshStart, 10000); // At least 10 seconds from now in any case.

    console.log(`Scheduling next token refresh check in ${safeRefreshTime / 1000} seconds`);
    
    const timer = setTimeout(() => {
       console.log("Scheduled refresh timer triggered.");
       // Call refreshToken directly. It handles the logic internally.
       refreshToken().catch(err => {
         console.error("Scheduled refresh failed:", err.message);
         // Logout is handled within refreshToken if needed
       });
    }, safeRefreshTime);

    setTokenRefreshTimer(timer);
  };

  // Fetch user credits (unchanged, assuming it works)
  const fetchUserCredits = async () => {
    // No changes needed here based on the spec
    if (!user) return;
    
    try {
      const { credits } = await api.getUserCredits();
      
      // Only update if credits changed to prevent unnecessary renders
      if (user.credits !== credits) {
        setUser(prevUser => {
           const updatedUser = { ...prevUser, credits };
           // Also update localStorage to keep it in sync
           const authData = localStorage.getItem('auth');
           if (authData) {
              try {
                 const parsedAuth = JSON.parse(authData);
                 parsedAuth.user = updatedUser;
                 localStorage.setItem('auth', JSON.stringify(parsedAuth));
              } catch (e) {
                 console.error("Failed to update credits in localStorage:", e);
              }
           }
           return updatedUser;
        });
      }
    } catch (err) {
      console.error('Failed to fetch user credits:', err);
      // Decide if this error should cause logout or just be logged
      if (err.response?.status === 401) {
         console.warn("Unauthorized fetching credits, likely needs refresh/logout.");
         // Refresh might be triggered by interceptor, or we could trigger it here.
         // Let's rely on the interceptor or next scheduled refresh for now.
      }
    }
  };

  // Register function - MODIFIED: Now only returns the API result (success/message)
  const register = async (email, password, fullName) => {
    setLoading(true);
    setError(null);
    try {
      // Call the API - it now returns { success: bool, message: str }
      const result = await api.register(email, password, fullName);
      
      // No automatic login after registration
      // No call to updateAuthState or fetchUserCredits here
      
      setLoading(false);
      // Return the result object from the API call directly
      return result; 
    } catch (err) {
      // api.register should format the error, but catch generic errors too
      const errorMessage = err.message || 'Registration failed';
      console.error('Registration failed in context:', errorMessage);
      setError(errorMessage);
      setLoading(false);
      // Return an error object consistent with the success object
      return { success: false, message: errorMessage };
    }
  };

  // Login function
  const login = async (email, password, rememberMe) => {
    setLoading(true); // Ensure loading state is set
    try {
      const response = await api.login(email, password, rememberMe);
      const { access_token, expires_in, user: userData } = response;
      updateAuthState(access_token, expires_in, userData);
      fetchUserCredits(); // Fetch credits after login
      return userData;
    } catch (err) {
      console.error('Login failed:', err);
      setError(err.message || 'Login failed');
      throw err; // Propagate the error so the UI can display it
    } finally {
      setLoading(false);
    }
  };

  // --- NEW: Password Reset Functions ---
  const forgotPassword = async (email) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.forgotPassword(email);
      setLoading(false);
      return response; // Contains the generic message
    } catch (err) {
      console.error('Forgot password error in context:', err);
      setError(err); // Store the formatted error from the interceptor
      setLoading(false);
      throw err; // Re-throw for the component to handle
    }
  };

  const resetPassword = async (token, newPassword) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.resetPassword(token, newPassword);
      setLoading(false);
      return response; // Contains success message
    } catch (err) {
      console.error('Reset password error in context:', err);
      setError(err);
      setLoading(false);
      throw err;
    }
  };
  // -------------------------------------

  // Provide auth context value
  const authContextValue = {
    user,
    loading,
    error,
    isAuthenticated: !!user && !loading && !isLoggingOut, // Added !isLoggingOut
    isLoggingOut,
    login,
    logout,
    register,
    fetchUserCredits, // Expose credit fetching if needed by components
    resendVerificationEmail: api.resendVerificationEmail,
    // NEW:
    forgotPassword,
    resetPassword,
    showWelcomeModal, // Expose state
    markWelcomeModalShown // Expose function
    // Don't expose internal functions like refreshToken directly if not needed
  };

  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
    </AuthContext.Provider>
  );
}; 
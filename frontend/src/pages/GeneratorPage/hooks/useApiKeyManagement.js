import { useState, useEffect } from 'react';
import * as apiService from '../../../services/api';

/**
 * Custom hook for managing API keys, validation, and secure token handling
 * @param {Function} showNotification - Function to display notifications
 * @returns {Object} API key state and management functions
 */
const useApiKeyManagement = (showNotification) => {
  // API Key states
  const [googleApiKey, setGoogleApiKey] = useState('');
  const [pplxApiKey, setPplxApiKey] = useState('');
  const [showGoogleKey, setShowGoogleKey] = useState(false);
  const [showPplxKey, setShowPplxKey] = useState(false);
  const [rememberApiKeys, setRememberApiKeys] = useState(false);
  const [googleKeyValid, setGoogleKeyValid] = useState(null);
  const [pplxKeyValid, setPplxKeyValid] = useState(null);
  const [validatingKeys, setValidatingKeys] = useState(false);
  
  // Token states for secure API requests
  const [googleKeyToken, setGoogleKeyToken] = useState(null);
  const [pplxKeyToken, setPplxKeyToken] = useState(null);

  // Load saved API tokens on hook initialization
  useEffect(() => {
    const { googleKeyToken, pplxKeyToken, remember } = apiService.getSavedApiTokens();
    if (googleKeyToken) {
      setGoogleKeyToken(googleKeyToken);
      setGoogleKeyValid(true); // Assume token is valid if it exists
    }
    
    if (pplxKeyToken) {
      setPplxKeyToken(pplxKeyToken);
      setPplxKeyValid(true); // Assume token is valid if it exists
    }
    
    if (remember) setRememberApiKeys(remember);
  }, []);

  /**
   * Validate API keys and obtain secure tokens
   */
  const handleValidateApiKeys = async () => {
    if (!googleApiKey.trim() && !pplxApiKey.trim()) {
      showNotification('Please enter at least one API key to authenticate', 'warning');
      return;
    }
    
    // Check basic format before sending to backend
    if (googleApiKey.trim() && !googleApiKey.trim().startsWith("AIza")) {
      showNotification('Invalid Google API key format. The key should start with "AIza".', 'error');
      setGoogleKeyValid(false);
      return;
    }
    
    if (pplxApiKey.trim() && !pplxApiKey.trim().startsWith("pplx-")) {
      showNotification('Invalid Perplexity API key format. The key should start with "pplx-".', 'error');
      setPplxKeyValid(false);
      return;
    }
    
    setValidatingKeys(true);
    setGoogleKeyValid(null);
    setPplxKeyValid(null);
    
    try {
      showNotification('Authenticating API keys...', 'info');
      console.log("Authenticating API keys to get secure tokens");
      
      const trimmedGoogleKey = googleApiKey.trim();
      const trimmedPplxKey = pplxApiKey.trim();
      
      const result = await apiService.authenticateApiKeys(trimmedGoogleKey, trimmedPplxKey, rememberApiKeys);
      
      // Update validation status and tokens
      if (trimmedGoogleKey) {
        setGoogleKeyValid(result.googleKeyValid || false);
        if (result.googleKeyValid) {
          setGoogleKeyToken(result.googleKeyToken);
          showNotification('Google API key authenticated successfully!', 'success');
        } else {
          setGoogleKeyToken(null);
          showNotification(`Google API key invalid: ${result.googleKeyError || 'Unknown error'}`, 'error');
        }
      }
      
      if (trimmedPplxKey) {
        setPplxKeyValid(result.pplxKeyValid || false);
        if (result.pplxKeyValid) {
          setPplxKeyToken(result.pplxKeyToken);
          showNotification('Perplexity API key authenticated successfully!', 'success');
        } else {
          setPplxKeyToken(null);
          showNotification(`Perplexity API key invalid: ${result.pplxKeyError || 'Unknown error'}`, 'error');
        }
      }
      
      // Show success notification if all provided keys are valid
      const googleSuccess = trimmedGoogleKey ? result.googleKeyValid : true;
      const pplxSuccess = trimmedPplxKey ? result.pplxKeyValid : true;
      
      if (googleSuccess && pplxSuccess) {
        if (trimmedGoogleKey && trimmedPplxKey) {
          showNotification('Both API keys authenticated successfully!', 'success');
        }
      }
    } catch (error) {
      console.error('Error during API key authentication:', error);
      showNotification('Network error authenticating API keys. Please check your internet connection and try again.', 'error');
      setGoogleKeyValid(false);
      setPplxKeyValid(false);
      setGoogleKeyToken(null);
      setPplxKeyToken(null);
    } finally {
      setValidatingKeys(false);
    }
  };

  /**
   * Clear API keys and tokens
   */
  const handleClearApiKeys = () => {
    setGoogleApiKey('');
    setPplxApiKey('');
    setGoogleKeyValid(null);
    setPplxKeyValid(null);
    setGoogleKeyToken(null);
    setPplxKeyToken(null);
    apiService.clearSavedApiTokens();
    setRememberApiKeys(false);
    showNotification('API keys cleared', 'success');
  };

  /**
   * Check if at least one valid API key token is available
   */
  const hasValidApiKey = () => {
    return Boolean(googleKeyToken || pplxKeyToken);
  };

  return {
    googleApiKey,
    setGoogleApiKey,
    pplxApiKey,
    setPplxApiKey,
    showGoogleKey,
    setShowGoogleKey,
    showPplxKey,
    setShowPplxKey,
    rememberApiKeys,
    setRememberApiKeys,
    googleKeyValid,
    pplxKeyValid,
    validatingKeys,
    googleKeyToken,
    pplxKeyToken,
    handleValidateApiKeys,
    handleClearApiKeys,
    hasValidApiKey
  };
};

export default useApiKeyManagement; 
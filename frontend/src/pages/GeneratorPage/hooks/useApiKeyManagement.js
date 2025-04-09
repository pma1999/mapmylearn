import { useState, useEffect } from 'react';
import * as apiService from '../../../services/api';

/**
 * Custom hook for API key management compatibility with server-provided keys
 * @param {Function} showNotification - Function to display notifications
 * @returns {Object} API key state and management functions
 */
const useApiKeyManagement = (showNotification) => {
  // Legacy state for backwards compatibility
  const [googleApiKey, setGoogleApiKey] = useState('');
  const [pplxApiKey, setPplxApiKey] = useState('');
  const [showGoogleKey, setShowGoogleKey] = useState(false);
  const [showPplxKey, setShowPplxKey] = useState(false);
  const [rememberApiKeys, setRememberApiKeys] = useState(false);
  
  // API key validation is always true with server-provided keys
  const [googleKeyValid, setGoogleKeyValid] = useState(true);
  const [pplxKeyValid, setPplxKeyValid] = useState(true);
  const [validatingKeys, setValidatingKeys] = useState(false);
  
  // We'll keep these for compatibility but they'll be null
  const [googleKeyToken, setGoogleKeyToken] = useState(null);
  const [pplxKeyToken, setPplxKeyToken] = useState(null);

  /**
   * Validate API keys (no-op in server-provided mode)
   */
  const handleValidateApiKeys = async () => {
    showNotification('API keys are now provided by the server. No validation needed.', 'info');
  };

  /**
   * Clear API keys (no-op in server-provided mode)
   */
  const handleClearApiKeys = () => {
    setGoogleApiKey('');
    setPplxApiKey('');
    showNotification('API key fields cleared. Note: The server will continue to use its own API keys.', 'info');
  };

  /**
   * Check if valid API keys are available (always true with server-provided keys)
   */
  const hasValidApiKey = () => {
    return true;
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
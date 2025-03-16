import React, { createContext, useState, useContext, useEffect } from 'react';
import * as api from '../services/api';

// Create Settings context
const SettingsContext = createContext();

// Default settings
const defaultSettings = {
  darkMode: window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches,
  parallelCount: 3,
  searchParallelCount: 2,
  submoduleParallelCount: 2,
  saveToHistory: true,
  openaiApiKeySet: false,
  tavilyApiKeySet: false,
};

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState(defaultSettings);
  const [apiKeys, setApiKeys] = useState({
    openaiApiKey: '',
    tavilyApiKey: '',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load settings from backend when the component mounts
  useEffect(() => {
    const loadSettings = async () => {
      try {
        setLoading(true);
        const data = await api.getSettings();
        
        setSettings({
          ...defaultSettings,
          ...data,
          // Override with local storage preferences if available
          darkMode: localStorage.getItem('darkMode') !== null
            ? localStorage.getItem('darkMode') === 'true'
            : data.darkMode || defaultSettings.darkMode,
        });
        
        setError(null);
      } catch (err) {
        console.error('Error loading settings:', err);
        setError('Failed to load settings');
        
        // Use localStorage settings if available
        const localDarkMode = localStorage.getItem('darkMode');
        if (localDarkMode !== null) {
          setSettings(prevSettings => ({
            ...prevSettings,
            darkMode: localDarkMode === 'true',
          }));
        }
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, []);

  // Update settings in the backend and local state
  const updateSettings = async (newSettings) => {
    try {
      // Update dark mode immediately for better UX
      if (newSettings.darkMode !== undefined) {
        localStorage.setItem('darkMode', newSettings.darkMode);
        setSettings(prevSettings => ({
          ...prevSettings,
          darkMode: newSettings.darkMode,
        }));
      }
      
      // For other settings, update via API
      const updatedSettings = await api.updateSettings({
        ...settings,
        ...newSettings,
      });
      
      setSettings(prevSettings => ({
        ...prevSettings,
        ...updatedSettings,
      }));
      
      return { success: true };
    } catch (err) {
      console.error('Error updating settings:', err);
      return { success: false, error: err.message || 'Failed to update settings' };
    }
  };

  // Update API keys
  const updateApiKeys = async (newKeys) => {
    try {
      // Only include non-empty keys in the update
      const keysToUpdate = {};
      if (newKeys.openaiApiKey) keysToUpdate.openaiApiKey = newKeys.openaiApiKey;
      if (newKeys.tavilyApiKey) keysToUpdate.tavilyApiKey = newKeys.tavilyApiKey;
      
      if (Object.keys(keysToUpdate).length === 0) {
        return { success: false, error: 'No keys to update' };
      }
      
      // Update API keys via backend
      const result = await api.updateSettings(keysToUpdate);
      
      // Update local state with the API key status
      setSettings(prevSettings => ({
        ...prevSettings,
        openaiApiKeySet: newKeys.openaiApiKey ? true : prevSettings.openaiApiKeySet,
        tavilyApiKeySet: newKeys.tavilyApiKey ? true : prevSettings.tavilyApiKeySet,
      }));
      
      return { success: true };
    } catch (err) {
      console.error('Error updating API keys:', err);
      return { success: false, error: err.message || 'Failed to update API keys' };
    }
  };

  // Value to be provided by the context
  const value = {
    settings,
    apiKeys,
    loading,
    error,
    updateSettings,
    updateApiKeys,
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};

// Custom hook to use the Settings context
export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

export default SettingsContext; 
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import * as apiService from '../../../services/api';
import * as languageService from '../../../services/languageService';

/**
 * Custom hook for managing generator form state and submission
 * @param {Object} apiKeyState - API key state from useApiKeyManagement hook
 * @param {Object} progressTrackingState - Progress tracking state from useProgressTracking hook
 * @param {Object} historyState - History management state from useHistoryManagement hook
 * @param {Function} showNotification - Function to display notifications
 * @returns {Object} Form state and management functions
 */
const useGeneratorForm = (
  { googleKeyToken, pplxKeyToken, rememberApiKeys, hasValidApiKey },
  { connectToProgressUpdates },
  { savePreferencesToSessionStorage },
  showNotification
) => {
  const navigate = useNavigate();
  
  // Form fields
  const [topic, setTopic] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  
  // Generator configuration
  const [parallelCount, setParallelCount] = useState(2);
  const [searchParallelCount, setSearchParallelCount] = useState(3);
  const [submoduleParallelCount, setSubmoduleParallelCount] = useState(2);
  
  // Module and Submodule count states
  const [autoModuleCount, setAutoModuleCount] = useState(true);
  const [desiredModuleCount, setDesiredModuleCount] = useState(5);
  const [autoSubmoduleCount, setAutoSubmoduleCount] = useState(true);
  const [desiredSubmoduleCount, setDesiredSubmoduleCount] = useState(3);
  
  // Language state
  const [language, setLanguage] = useState(languageService.getLanguagePreference());
  
  // Accordion state
  const [advancedSettingsOpen, setAdvancedSettingsOpen] = useState(false);
  const [apiSettingsOpen, setApiSettingsOpen] = useState(false);
  
  // Save language preference whenever it changes
  const handleLanguageChange = (newLanguage) => {
    setLanguage(newLanguage);
    languageService.saveLanguagePreference(newLanguage);
  };

  /**
   * Handle form submission
   * @param {Event} e - Form submit event
   */
  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    
    if (!topic.trim()) {
      setError('Please enter a topic');
      return;
    }

    // Check if API key tokens are available
    if (!hasValidApiKey()) {
      setError('API keys are required. Please authenticate your API keys in the API Key Settings section.');
      setApiSettingsOpen(true); // Open the API settings accordion
      return;
    }
    
    setError('');
    setIsGenerating(true);
    
    try {
      console.log("Using secure token-based API access for learning path generation");
      
      // Prepare the request data, including the new module and submodule count parameters
      const requestData = {
        parallelCount,
        searchParallelCount,
        submoduleParallelCount,
        googleKeyToken,
        pplxKeyToken,
        rememberTokens: rememberApiKeys,
        language
      };
      
      // Only include module count if automatic mode is disabled
      if (!autoModuleCount) {
        requestData.desiredModuleCount = desiredModuleCount;
      }
      
      // Only include submodule count if automatic mode is disabled
      if (!autoSubmoduleCount) {
        requestData.desiredSubmoduleCount = desiredSubmoduleCount;
      }
      
      const response = await apiService.generateLearningPath(topic, requestData);
      
      // Connect to progress updates
      connectToProgressUpdates(response.task_id);
      
      // Save preferences for the result page
      savePreferencesToSessionStorage(topic);
      
      // Navigate to result page
      navigate(`/result/${response.task_id}`);
    } catch (err) {
      console.error('Error generating learning path:', err);
      
      // Check if this is an API key validation error
      if (err.response && err.response.status === 400 && err.response.data.detail) {
        if (err.response.data.detail.includes('API key tokens') || 
            err.response.data.detail.includes('token')) {
          setError(err.response.data.detail);
          setApiSettingsOpen(true);
        } else {
          setError(err.response.data.detail);
        }
      } else {
        setError('Failed to generate learning path. Please try again.');
      }
      
      setIsGenerating(false);
    }
  };

  return {
    // Form fields
    topic,
    setTopic,
    isGenerating,
    error,
    
    // Generator configuration
    parallelCount,
    setParallelCount,
    searchParallelCount,
    setSearchParallelCount,
    submoduleParallelCount,
    setSubmoduleParallelCount,
    
    // Module and Submodule count
    autoModuleCount,
    setAutoModuleCount,
    desiredModuleCount,
    setDesiredModuleCount,
    autoSubmoduleCount,
    setAutoSubmoduleCount,
    desiredSubmoduleCount,
    setDesiredSubmoduleCount,
    
    // Language
    language,
    setLanguage: handleLanguageChange,
    
    // Accordion state
    advancedSettingsOpen,
    setAdvancedSettingsOpen,
    apiSettingsOpen,
    setApiSettingsOpen,
    
    // Form submission
    handleSubmit
  };
};

export default useGeneratorForm; 
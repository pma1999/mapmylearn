import { useNavigate } from 'react-router';
import { useState, useCallback } from 'react';
import * as apiService from '../../../services/api';
import * as languageService from '../../../services/languageService';

// Define default styles
const defaultStyles = {
  standard: "Standard",
  simple: "Simple & Clear",
  technical: "Technical Deep Dive",
  example: "Learn by Example",
  conceptual: "Big Picture Focus",
  grumpy_genius: "Grumpy Genius Mode"
};

/**
 * Custom hook for managing generator form state and submission
 * @param {Function} showNotification - Function to display notifications
 * @returns {Object} Form state and management functions
 */
const useGeneratorForm = (
  showNotification
) => {
  const navigate = useNavigate();
  
  // Form fields
  const [topic, setTopic] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [taskId, setTaskId] = useState(null);
  
  // Generator configuration
  const [parallelCount, setParallelCount] = useState(5);
  const [searchParallelCount, setSearchParallelCount] = useState(5);
  const [submoduleParallelCount, setSubmoduleParallelCount] = useState(5);
  
  // Module and Submodule count states
  const [autoModuleCount, setAutoModuleCount] = useState(true);
  const [desiredModuleCount, setDesiredModuleCount] = useState(5);
  const [autoSubmoduleCount, setAutoSubmoduleCount] = useState(true);
  const [desiredSubmoduleCount, setDesiredSubmoduleCount] = useState(3);
  
  // Language state
  const [language, setLanguage] = useState(languageService.getLanguagePreference());
  
  // Accordion state
  const [advancedSettingsOpen, setAdvancedSettingsOpen] = useState(false);
  
  // Explanation style state
  const [explanationStyle, setExplanationStyle] = useState('standard');
  
  // Save language preference whenever it changes
  const handleLanguageChange = (newLanguage) => {
    setLanguage(newLanguage);
    languageService.saveLanguagePreference(newLanguage);
  };

  /**
   * Setup navigation after task creation
   * @param {string} currentTaskId - Task ID to navigate to
   * @param {string} currentTopic - The topic being generated
   */
  const setupNavigationToResultPage = useCallback((currentTaskId, currentTopic) => {
    // Save topic to session storage HERE
    sessionStorage.setItem('currentTopic', currentTopic);
    
    // Navigate to result page
    navigate(`/generating/${currentTaskId}`);
  }, [navigate]);

  /**
   * Handle form submission
   * @param {Event} e - Form submit event
   */
  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    
    if (!topic.trim()) {
      setError('Please enter a topic to generate a course for.');
      return;
    }
    
    setError(null);
    setIsGenerating(true);
    
    try {
      const result = await apiService.generateLearningPath(topic, {
        parallelCount,
        searchParallelCount,
        submoduleParallelCount,
        desiredModuleCount: autoModuleCount ? null : desiredModuleCount,
        desiredSubmoduleCount: autoSubmoduleCount ? null : desiredSubmoduleCount,
        language: language,
        explanationStyle: explanationStyle
      });
      
      // Store task ID and set generating state
      setTaskId(result.task_id);
      
      // Navigate to result page
      setupNavigationToResultPage(result.task_id, topic);
      
    } catch (err) {
      console.error('Error starting generation:', err);
      setIsGenerating(false);
      
      // Check for network errors
      if (!err.response) {
        setError('Network error. Please check your internet connection and try again.');
        return;
      }
      
      // Check for specific error types
      if (err.response && err.response.data) {
        // Check if this is an API key validation error
        if (err.response.data.detail && 
           (err.response.data.detail.includes('API key validation') || 
            err.response.data.detail.includes('API key error'))) {
          setError(`API key error: ${err.response.data.detail}`);
          return;
        }
        
        setError(err.response.data.detail || 'An error occurred while starting the generation. Please try again.');
      } else {
        setError(err.message || 'An unexpected error occurred. Please try again.');
      }
    }
  };

  return {
    // Form fields
    topic,
    setTopic,
    isGenerating,
    error,
    taskId,
    
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
    
    // Explanation style
    explanationStyle,
    setExplanationStyle,
    
    // Accordion state
    advancedSettingsOpen,
    setAdvancedSettingsOpen,
    
    // Form submission
    handleSubmit
  };
};

export default useGeneratorForm; 
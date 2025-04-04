import { useState } from 'react';

/**
 * Custom hook for managing notification state and display logic
 * @returns {Object} Notification state and utility functions
 */
const useNotification = () => {
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'success',
    duration: 6000
  });

  /**
   * Show a notification with the specified message and severity
   * @param {string} message - The notification message to display
   * @param {string} severity - The severity level (success, error, warning, info)
   */
  const showNotification = (message, severity = 'success') => {
    // Adjust duration based on message type
    const duration = severity === 'error' ? 10000 : 6000;
    
    // Format error messages for better readability
    let formattedMessage = message;
    if (severity === 'error' && (message.includes('API key') || message.includes('Perplexity'))) {
      formattedMessage = message.replace('. ', '.\n\n');
    }
    
    setNotification({
      open: true,
      message: formattedMessage,
      severity,
      duration
    });
  };

  /**
   * Close the currently displayed notification
   */
  const closeNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };

  return {
    notification,
    showNotification,
    closeNotification
  };
};

export default useNotification; 
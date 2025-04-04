import { useState } from 'react';

/**
 * Custom hook for managing notifications
 * @returns {Object} Notification state and functions
 */
const useNotification = () => {
  const [notification, setNotification] = useState({ 
    open: false, 
    message: '', 
    severity: 'info' 
  });

  /**
   * Show a notification with specified message and severity
   * @param {string} message - The message to display
   * @param {string} severity - The severity level (info, success, warning, error)
   */
  const showNotification = (message, severity = 'info') => {
    setNotification({
      open: true,
      message,
      severity,
    });
  };

  /**
   * Close the current notification
   */
  const handleNotificationClose = () => {
    setNotification({ ...notification, open: false });
  };

  return {
    notification,
    showNotification,
    closeNotification: handleNotificationClose
  };
};

export default useNotification; 
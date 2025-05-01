import { useNotifier } from '../../../contexts/NotificationContext';

/**
 * Custom hook providing a simple interface to display notifications.
 * This hook now acts as a wrapper around the NotificationContext.
 * @returns {Function} showNotification function
 */
const useNotification = () => {
  const { showNotification: contextShowNotification } = useNotifier();

  /**
   * Show a notification with specified message and severity/options.
   * @param {string} message - The message to display.
   * @param {object|string} [optionsOrSeverity='info'] - Either a severity string ('info', 'success', 'warning', 'error') 
   *                                                    or an options object { severity?: string, duration?: number }.
   */
  const showNotification = (message, optionsOrSeverity = 'info') => {
    let options = {};
    if (typeof optionsOrSeverity === 'string') {
      options.severity = optionsOrSeverity;
    } else if (typeof optionsOrSeverity === 'object' && optionsOrSeverity !== null) {
      options = optionsOrSeverity;
    }
    
    contextShowNotification(message, options);
  };

  // The actual Snackbar rendering and closing logic is now handled by NotificationProvider.
  // This hook just provides the function to trigger notifications.
  return {
    showNotification,
    // No need to return notification state or closeNotification anymore
  };
};

export default useNotification; 
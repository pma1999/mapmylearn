import React, { createContext, useState, useCallback, useContext, useMemo } from 'react';
import { Snackbar, Alert } from '@mui/material';

// Create the context
const NotificationContext = createContext(null);

// Create a provider component
export const NotificationProvider = ({ children }) => {
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info', // Default severity
    duration: 6000, // Default duration
  });

  const showNotification = useCallback((message, options = {}) => {
    setNotification({
      open: true,
      message,
      severity: options.severity || 'info',
      duration: options.duration || 6000, // Use provided or default duration
    });
  }, []);

  const closeNotification = useCallback((event, reason) => {
    // Prevent closing on clickaway unless explicitly allowed (optional)
    if (reason === 'clickaway') {
      // return;
    }
    setNotification((prev) => ({ ...prev, open: false }));
  }, []);

  const contextValue = useMemo(() => ({
    showNotification,
  }), [showNotification]);

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
      <Snackbar
        open={notification.open}
        autoHideDuration={notification.duration}
        onClose={closeNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }} // Consistent position
        // Adjust key to ensure re-triggering for same message/severity if needed
        // key={`${notification.message}-${notification.severity}-${Date.now()}`}
      >
        {/* Use onClose on Alert only if you want the 'X' button */}
        <Alert 
          severity={notification.severity} 
          sx={{ width: '100%' }} 
          variant="filled"
          elevation={6}
          onClose={closeNotification} // Add close button to Alert
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </NotificationContext.Provider>
  );
};

// Create a custom hook to use the notification context
export const useNotifier = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifier must be used within a NotificationProvider');
  }
  return context;
}; 
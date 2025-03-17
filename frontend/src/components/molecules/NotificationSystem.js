import React from 'react';
import { Snackbar, Alert } from '@mui/material';

function NotificationSystem({ notification, onClose }) {
  return (
    <Snackbar
      open={notification.open}
      autoHideDuration={notification.duration || 6000}
      onClose={onClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
    >
      <Alert 
        onClose={onClose}
        severity={notification.severity}
        variant={notification.severity === 'error' ? "filled" : "standard"}
        sx={{ 
          width: '100%',
          whiteSpace: 'pre-line',
          '& .MuiAlert-message': {
            maxWidth: '500px'
          }
        }}
      >
        {notification.message}
      </Alert>
    </Snackbar>
  );
}

export default NotificationSystem; 
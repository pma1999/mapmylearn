import React, { useState, useEffect } from 'react';
import { Snackbar, Alert } from '@mui/material';

const NotificationBar = ({ message, severity, onClose, autoHideDuration = 6000 }) => {
  const [open, setOpen] = useState(false);

  // Open the notification when message changes
  useEffect(() => {
    if (message) {
      setOpen(true);
    }
  }, [message]);

  // Handle close
  const handleClose = (event, reason) => {
    if (reason === 'clickaway') {
      return;
    }
    setOpen(false);
    // Delay the onClose callback to allow the closing animation to finish
    setTimeout(() => {
      if (onClose) onClose();
    }, 300);
  };

  if (!message) return null;

  return (
    <Snackbar
      open={open}
      autoHideDuration={autoHideDuration}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
    >
      <Alert
        onClose={handleClose}
        severity={severity}
        sx={{ width: '100%' }}
        elevation={6}
        variant="filled"
      >
        {message}
      </Alert>
    </Snackbar>
  );
};

export default NotificationBar; 
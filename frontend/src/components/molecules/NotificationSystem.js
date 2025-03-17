import React from 'react';
import {
  Snackbar,
  Alert,
  IconButton,
  useMediaQuery,
  useTheme
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

const NotificationSystem = ({ notification, onClose }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  return (
    <Snackbar
      open={notification.open}
      autoHideDuration={notification.duration || 6000}
      onClose={onClose}
      anchorOrigin={{
        vertical: 'bottom',
        horizontal: isMobile ? 'center' : 'right'
      }}
      sx={{
        '& .MuiPaper-root': {
          maxWidth: isMobile ? '90%' : '400px',
        }
      }}
    >
      <Alert
        severity={notification.severity || 'info'}
        variant="filled"
        action={
          <IconButton
            aria-label="close"
            color="inherit"
            size={isMobile ? "small" : "medium"}
            onClick={onClose}
          >
            <CloseIcon fontSize={isMobile ? "small" : "medium"} />
          </IconButton>
        }
        sx={{ 
          width: '100%',
          fontSize: { xs: '0.75rem', sm: '0.875rem' },
          alignItems: 'center'
        }}
      >
        {notification.message}
      </Alert>
    </Snackbar>
  );
};

export default NotificationSystem; 
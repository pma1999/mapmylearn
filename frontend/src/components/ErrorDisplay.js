import React from 'react';
import { Box, Typography, Paper, Button, Link } from '@mui/material';
import ErrorIcon from '@mui/icons-material/Error';
import { Link as RouterLink } from 'react-router-dom';

const ErrorDisplay = ({ 
  title = 'Error', 
  message = 'Something went wrong', 
  details = null, 
  actionText = 'Try Again', 
  onAction = null,
  showHomeLink = true 
}) => {
  return (
    <Paper
      elevation={3}
      sx={{
        p: 4,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        maxWidth: '600px',
        mx: 'auto',
        mt: 4
      }}
    >
      <ErrorIcon color="error" sx={{ fontSize: 60, mb: 2 }} />
      
      <Typography variant="h5" component="h2" gutterBottom fontWeight="bold">
        {title}
      </Typography>
      
      <Typography variant="body1" sx={{ mb: 3 }}>
        {message}
      </Typography>
      
      {details && (
        <Typography 
          variant="body2" 
          color="text.secondary" 
          sx={{ 
            mb: 3, 
            p: 2, 
            backgroundColor: 'background.paper', 
            borderRadius: 1,
            width: '100%',
            overflowX: 'auto'
          }}
        >
          {details}
        </Typography>
      )}
      
      <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
        {onAction && (
          <Button 
            variant="contained" 
            color="primary" 
            onClick={onAction}
          >
            {actionText}
          </Button>
        )}
        
        {showHomeLink && (
          <Button 
            variant="outlined" 
            component={RouterLink} 
            to="/"
          >
            Return to Home
          </Button>
        )}
      </Box>
    </Paper>
  );
};

export default ErrorDisplay; 
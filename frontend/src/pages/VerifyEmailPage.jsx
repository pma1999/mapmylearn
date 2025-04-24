import React, { useState, useEffect } from 'react';
import { useSearchParams, Link as RouterLink } from 'react-router';
import { Container, Paper, Typography, Box, CircularProgress, Alert, Button } from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import { verifyEmail } from '../services/api'; // Assuming api.js is in ../services

const VerifyEmailPage = () => {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('verifying'); // verifying | success | error
  const [message, setMessage] = useState('Verifying your email address...');

  useEffect(() => {
    const token = searchParams.get('token');

    if (!token) {
      setStatus('error');
      setMessage('Verification token missing. Please check the link in your email.');
      return;
    }

    const verify = async () => {
      const result = await verifyEmail(token);
      if (result.success) {
        setStatus('success');
        setMessage(result.message);
      } else {
        setStatus('error');
        setMessage(result.message || 'An error occurred during email verification.');
      }
    };

    verify();
  }, [searchParams]);

  return (
    <Container maxWidth="sm">
      <Paper elevation={3} sx={{ p: 4, mt: 6, textAlign: 'center' }}>
        <Box sx={{ mb: 3 }}>
          {status === 'verifying' && <CircularProgress />}
          {status === 'success' && <CheckCircleOutlineIcon color="success" sx={{ fontSize: 60 }} />}
          {status === 'error' && <ErrorOutlineIcon color="error" sx={{ fontSize: 60 }} />}
        </Box>
        
        <Typography variant="h5" component="h1" gutterBottom>
          Email Verification
        </Typography>
        
        <Alert 
          severity={status === 'verifying' ? 'info' : status} 
          sx={{ mt: 2, mb: 3, textAlign: 'center' }}
        >
          {message}
        </Alert>
        
        {status === 'success' && (
          <Button component={RouterLink} to="/login" variant="contained">
            Proceed to Login
          </Button>
        )}
        
        {status === 'error' && (
          <Typography variant="body2">
            If you continue to have issues, please contact support or try registering again.
          </Typography>
        )}
      </Paper>
    </Container>
  );
};

export default VerifyEmailPage; 
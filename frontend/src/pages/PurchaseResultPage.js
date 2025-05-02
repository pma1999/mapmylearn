import React, { useEffect, useState, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router';
import { Box, CircularProgress, Typography, Alert, Snackbar, Button, Paper, Divider } from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import { useAuth } from '../services/authContext';
import * as api from '../services/api';

const PurchaseResultPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { fetchUserCredits } = useAuth();
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('processing'); // 'processing', 'success', 'error', 'canceled'
  const [message, setMessage] = useState('Processing your purchase...');
  const [notification, setNotification] = useState({ open: false, message: '' });
  const [sessionDetails, setSessionDetails] = useState(null); // State to hold session details

  const handleCloseNotification = () => {
    setNotification({ open: false, message: '' });
  };

  const checkSessionStatus = useCallback(async (sessionId) => {
    try {
      console.log('Checking session status for:', sessionId);
      const response = await api.getCheckoutSession(sessionId);
      console.log('Session status response:', response);

      if (response.status === 'complete' || response.status === 'paid') {
        setStatus('success');
        setMessage('Purchase successful! Credits have been added to your account.');
        setSessionDetails(response); // Store details on success
        // Fetch updated credits (this updates context)
        await fetchUserCredits();
        setNotification({ open: true, message: 'Credits added successfully!' });
      } else if (response.status === 'open') {
        // Payment was likely canceled or incomplete
        setStatus('canceled');
        setMessage('Purchase was canceled or is still pending.');
      } else {
        setStatus('error');
        setMessage(`Purchase failed. Status: ${response.status}. Please contact support if payment was taken.`);
      }
    } catch (error) {
      setStatus('error');
      setMessage(error.message || 'An error occurred while verifying your purchase.');
      console.error('Error verifying purchase:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchUserCredits]);

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const sessionId = queryParams.get('session_id');

    if (sessionId) {
      checkSessionStatus(sessionId);
    } else {
      setMessage('No session ID found. Invalid redirect.');
      setStatus('error');
      setLoading(false);
    }
  }, [location.search, checkSessionStatus]);

  return (
    <Box 
      display="flex" 
      flexDirection="column" 
      alignItems="center" 
      justifyContent="center" 
      minHeight="60vh"
      p={3}
    >
      {loading ? (
        <Box textAlign="center">
          <CircularProgress />
          <Typography variant="h6" sx={{ mt: 2 }}>Verifying purchase...</Typography>
        </Box>
      ) : (
        <Paper elevation={3} sx={{ p: {xs: 2, sm: 4}, maxWidth: 600, width: '100%', textAlign: 'center' }}>
          {status === 'success' && (
            <CheckCircleOutlineIcon color="success" sx={{ fontSize: 60, mb: 2 }} />
          )}
          {status === 'error' && (
            <ErrorOutlineIcon color="error" sx={{ fontSize: 60, mb: 2 }} />
          )}
          {status === 'canceled' && (
             <ErrorOutlineIcon color="warning" sx={{ fontSize: 60, mb: 2 }} />
          )}

          <Typography variant="h5" gutterBottom align="center">
            {status === 'success' ? 'Purchase Complete' : 
             status === 'canceled' ? 'Purchase Canceled' : 'Purchase Status'}
          </Typography>

          <Alert 
            severity={status === 'success' ? 'success' : status === 'canceled' ? 'warning' : 'error'}
            sx={{ mt: 2, mb: 3, width: '100%', textAlign: 'left' }}
          >
            {message}
          </Alert>

          {/* Display details on success */}
          {status === 'success' && sessionDetails && (
            <Box mb={3} textAlign="left" sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
              <Typography variant="subtitle1" gutterBottom>
                Purchase Details:
              </Typography>
              <Divider sx={{ mb: 1 }}/>
              <Typography variant="body2" color="text.secondary">
                Amount: {sessionDetails.currency.toUpperCase()} {(sessionDetails.amount_total / 100).toFixed(2)}
              </Typography>
              {sessionDetails.metadata?.credit_quantity && (
                <Typography variant="body2" color="text.secondary">
                  Credits Added: {sessionDetails.metadata.credit_quantity}
                </Typography>
              )}
              <Typography variant="body2" color="text.secondary">
                Transaction ID: {sessionDetails.payment_intent_id || 'N/A'}
              </Typography>
            </Box>
          )}

          {status !== 'processing' && (
            <Button variant="contained" onClick={() => navigate('/generator')}>
              Go to Generator
            </Button>
          )}
        </Paper>
      )}

      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseNotification} severity="success" sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default PurchaseResultPage; 
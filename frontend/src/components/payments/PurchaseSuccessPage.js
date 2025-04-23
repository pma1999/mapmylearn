import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  CircularProgress,
  Alert
} from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import * as api from '../../services/api';
import { useAuth } from '../../services/authContext';

const PurchaseSuccessPage = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sessionData, setSessionData] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();
  const { fetchUserCredits } = useAuth();

  useEffect(() => {
    const checkSession = async () => {
      try {
        // Get session_id from URL parameters
        const params = new URLSearchParams(location.search);
        const sessionId = params.get('session_id');

        if (!sessionId) {
          throw new Error('No session ID provided');
        }

        // Check session status
        const session = await api.getCheckoutSession(sessionId);
        setSessionData(session);

        // Refresh user credits
        await fetchUserCredits();

      } catch (err) {
        setError(err.message || 'Failed to verify purchase');
      } finally {
        setLoading(false);
      }
    };

    checkSession();
  }, [location, fetchUserCredits]);

  const handleContinue = () => {
    navigate('/'); // Or wherever you want to redirect
  };

  if (loading) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="80vh"
      >
        <CircularProgress />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Verifying your purchase...
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="80vh"
      px={2}
    >
      <Paper elevation={3} sx={{ p: 4, maxWidth: 600, width: '100%' }}>
        {error ? (
          <>
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
            <Button
              variant="contained"
              color="primary"
              onClick={handleContinue}
              fullWidth
            >
              Return to Dashboard
            </Button>
          </>
        ) : (
          <>
            <Box display="flex" flexDirection="column" alignItems="center" mb={4}>
              <CheckCircleOutlineIcon
                color="success"
                sx={{ fontSize: 64, mb: 2 }}
              />
              <Typography variant="h4" gutterBottom>
                Purchase Successful!
              </Typography>
              <Typography variant="body1" color="text.secondary" align="center">
                Thank you for your purchase. Your credits have been added to your account.
              </Typography>
            </Box>

            {sessionData && (
              <Box mb={4}>
                <Typography variant="subtitle1" gutterBottom>
                  Purchase Details:
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Amount: €{(sessionData.amount_total / 100).toFixed(2)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Credits: {sessionData.metadata?.credit_quantity}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Transaction ID: {sessionData.payment_intent_id || 'N/A'}
                </Typography>
              </Box>
            )}

            <Button
              variant="contained"
              color="primary"
              onClick={handleContinue}
              fullWidth
            >
              Continue to Dashboard
            </Button>
          </>
        )}
      </Paper>
    </Box>
  );
};

export default PurchaseSuccessPage; 
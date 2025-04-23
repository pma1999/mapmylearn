import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
} from '@mui/material';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';

const PurchaseCancelPage = () => {
  const navigate = useNavigate();

  const handleTryAgain = () => {
    navigate('/'); // Or wherever you want to redirect
  };

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
        <Box display="flex" flexDirection="column" alignItems="center" mb={4}>
          <CancelOutlinedIcon
            color="error"
            sx={{ fontSize: 64, mb: 2 }}
          />
          <Typography variant="h4" gutterBottom>
            Purchase Cancelled
          </Typography>
          <Typography variant="body1" color="text.secondary" align="center">
            Your credit purchase was cancelled. No charges were made to your account.
          </Typography>
        </Box>

        <Box display="flex" flexDirection="column" gap={2}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleTryAgain}
            fullWidth
          >
            Try Again
          </Button>
          <Button
            variant="outlined"
            onClick={() => navigate('/')}
            fullWidth
          >
            Return to Dashboard
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default PurchaseCancelPage; 
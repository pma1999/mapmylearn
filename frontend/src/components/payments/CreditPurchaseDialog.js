import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  Alert,
  CircularProgress,
  InputAdornment
} from '@mui/material';
import { loadStripe } from '@stripe/stripe-js';
import * as api from '../../services/api';

// Initialize Stripe
const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

const CREDIT_PRICE = 1; // €0.60 per credit

const CreditPurchaseDialog = ({ open, onClose }) => {
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleQuantityChange = (event) => {
    const value = parseInt(event.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setQuantity(value);
    }
  };

  const handlePurchase = async () => {
    try {
      setLoading(true);
      setError(null);

      // Create Checkout Session
      const response = await api.createCheckoutSession(quantity);
      
      // Get Stripe instance
      const stripe = await stripePromise;
      if (!stripe) {
        throw new Error('Failed to load Stripe');
      }

      // Redirect to Checkout
      const { error } = await stripe.redirectToCheckout({
        sessionId: response.sessionId
      });

      if (error) {
        throw error;
      }

    } catch (err) {
      setError(err.message || 'Failed to initiate purchase');
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Purchase Credits</DialogTitle>
      <DialogContent>
        <Box sx={{ my: 2 }}>
          <Typography variant="body1" gutterBottom>
            Credits are used to generate learning paths. Each credit allows you to generate one learning path.
          </Typography>

          <TextField
            fullWidth
            type="number"
            label="Number of Credits"
            value={quantity}
            onChange={handleQuantityChange}
            inputProps={{ min: 1 }}
            sx={{ mt: 2 }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  credits
                </InputAdornment>
              ),
            }}
          />

          <Typography variant="body1" color="text.secondary" sx={{ mt: 2 }}>
            Price per credit: €{CREDIT_PRICE.toFixed(2)}
          </Typography>

          <Typography variant="h6" sx={{ mt: 1 }}>
            Total: €{(quantity * CREDIT_PRICE).toFixed(2)}
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handlePurchase}
          variant="contained"
          color="primary"
          disabled={loading || quantity < 1}
          startIcon={loading && <CircularProgress size={20} />}
        >
          {loading ? 'Processing...' : 'Purchase'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreditPurchaseDialog; 
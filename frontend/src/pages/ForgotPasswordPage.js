import React, { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Link,
  Alert,
  CircularProgress,
} from '@mui/material';
import MailOutlineIcon from '@mui/icons-material/MailOutline'; // Icon suggestion
import { useAuth } from '../services/authContext';

const ForgotPasswordPage = () => {
  const { forgotPassword } = useAuth(); // Get the function from context
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    try {
      // Call the function from the auth context
      const response = await forgotPassword(email);
      setMessage(response.message); // Display the generic success message from context/API
    } catch (err) {
      console.error("Forgot password error on page:", err);
      // Use the error message processed by the context/interceptor if available
      setError(err.message || 'Ocurrió un error al procesar tu solicitud. Inténtalo de nuevo más tarde.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Paper elevation={3} sx={{ p: 4, mt: 6 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
           <Box 
            sx={{ 
              backgroundColor: 'secondary.main', // Or primary.main
              color: 'white', 
              borderRadius: '50%', 
              p: 1,
              mb: 2
            }}
          >
            <MailOutlineIcon />
          </Box>
          <Typography component="h1" variant="h5" sx={{ mb: 1 }}>
            Reset Password
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3, textAlign: 'center' }}>
            Enter your email address and we'll send you a link to reset your password (if the account exists and is verified).
          </Typography>

          {/* Show message OR error, not both potentially */} 
          {message && !error && (
              <Alert severity="success" sx={{ width: '100%', mb: 2 }}>
                  {message}
              </Alert>
          )}
          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {error}
            </Alert>
          )}

          {!message && ( // Hide form after successful message is shown
            <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
              <TextField
                margin="normal"
                required
                fullWidth
                id="email"
                label="Email Address"
                name="email"
                autoComplete="email"
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 2, mb: 2 }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Send Reset Link'}
              </Button>
            </Box>
          )}

          <Box sx={{ mt: 2 }}>
            <Link component={RouterLink} to="/login" variant="body2">
              Back to Sign In
            </Link>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default ForgotPasswordPage; 
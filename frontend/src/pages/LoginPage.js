import React, { useState, useEffect } from 'react';
import { useNavigate, Link as RouterLink, useLocation } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Link,
  FormControlLabel,
  Checkbox,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { useAuth } from '../services/authContext';

const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, error, loading, isAuthenticated, resendVerificationEmail } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true); // Default to true for better UX
  const [showError, setShowError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [sessionExpired, setSessionExpired] = useState(false);
  const [needsVerification, setNeedsVerification] = useState(false); // State for verification error
  const [isResending, setIsResending] = useState(false); // State for resend button
  const [resendMessage, setResendMessage] = useState(''); // State for resend feedback

  // Check if redirected due to session expiration
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('session_expired') === 'true') {
      setSessionExpired(true);
      setShowError(true);
      setErrorMessage('Your session has expired. Please sign in again to continue.');
    }
  }, [location]);

  // Get return path from state if available
  const from = location.state?.from?.pathname || '/generator';

  // Redirect to generator page if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      // Check for pending migration before navigating
      // const pendingMigration = checkPendingMigration(); // Removed call
      // console.log("Pending Migration Check on Login:", pendingMigration);
      // if (pendingMigration) {
      //   // Optional: Show a message or redirect to a migration status page
      //   console.log("Pending migration detected, handling...");
      //   // Example: navigate('/migration-status'); 
      //   // For now, just navigate to dashboard after check
      // }
      
      // Navigate to the intended destination or dashboard
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]); // Removed checkPendingMigration from dependencies

  const handleSubmit = async (e) => {
    e.preventDefault();
    setShowError(false);
    setSessionExpired(false);
    setNeedsVerification(false); // Reset verification state
    setResendMessage(''); // Reset resend message

    try {
      await login(email, password, rememberMe);
      // Navigate handled by the useEffect
    } catch (err) {
      // Check for specific verification error message
      if (err.message && err.message.toLowerCase().includes('account not verified')) {
        setNeedsVerification(true);
        setErrorMessage(err.message + ' Would you like to resend the verification email?');
      } else {
        setErrorMessage(err.message || 'Login failed. Please check your credentials.');
      }
      setShowError(true);
    }
  };

  // Handler for resending verification email
  const handleResendVerification = async () => {
    setIsResending(true);
    setResendMessage('');
    try {
      const result = await resendVerificationEmail(email);
      setResendMessage(result.message); // Show success/info message from backend
    } catch (err) {
      // api.js should handle formatting, show a generic message here
      setResendMessage('Failed to resend verification email. Please try again later.'); 
    } finally {
      setIsResending(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Paper elevation={3} sx={{ p: 4, mt: 6 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Box 
            sx={{ 
              backgroundColor: 'primary.main', 
              color: 'white', 
              borderRadius: '50%', 
              p: 1,
              mb: 2
            }}
          >
            <LockOutlinedIcon />
          </Box>
          
          <Typography component="h1" variant="h5" sx={{ mb: 3 }}>
            Sign in to MapMyLearn
          </Typography>
          
          {showError && (
            <Alert 
              severity={sessionExpired ? "info" : "error"} 
              sx={{ width: '100%', mb: 2 }}
            >
              {errorMessage}
              {/* Add Resend button if verification needed */}
              {needsVerification && (
                <Button 
                  variant="text" 
                  size="small" 
                  onClick={handleResendVerification}
                  disabled={isResending || !email}
                  sx={{ ml: 1, textTransform: 'none' }}
                >
                  {isResending ? <CircularProgress size={16} /> : 'Resend Email'}
                </Button>
              )}
              {/* Show feedback from resend attempt */} 
              {resendMessage && (
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  {resendMessage}
                </Typography>
              )}
            </Alert>
          )}
          
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
            
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
            
            <FormControlLabel
              control={
                <Checkbox 
                  value="remember" 
                  color="primary" 
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  disabled={loading}
                />
              }
              label="Remember me for 30 days"
            />
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Sign In'}
            </Button>
            
            {/* Changed Box layout and added Forgot Password link */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
              <Link component={RouterLink} to="/forgot-password" variant="body2">
                Forgot password?
              </Link>
              <Link component={RouterLink} to="/register" variant="body2">
                Don't have an account? Sign up
              </Link>
            </Box>
          </Box>
        </Box>
      </Paper>
      
      <Box sx={{ mt: 3, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          By signing in, you'll be able to save your learning paths to the cloud.
        </Typography>
      </Box>
    </Container>
  );
};

export default LoginPage; 
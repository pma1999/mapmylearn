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
  const { login, error, loading, isAuthenticated, checkPendingMigration } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true); // Default to true for better UX
  const [showError, setShowError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [sessionExpired, setSessionExpired] = useState(false);

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
      const pendingMigration = checkPendingMigration();
      if (pendingMigration) {
        navigate('/migrate');
      } else {
        // Navigate to the page they were trying to access, or default to generator
        navigate(from);
      }
    }
  }, [isAuthenticated, navigate, checkPendingMigration, from]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setShowError(false);
    setSessionExpired(false);

    try {
      await login(email, password, rememberMe);
      
      // Navigate handled by the useEffect
    } catch (err) {
      setErrorMessage(err.message || 'Login failed. Please check your credentials.');
      setShowError(true);
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
            Sign in to LearnCompass
          </Typography>
          
          {showError && (
            <Alert 
              severity={sessionExpired ? "info" : "error"} 
              sx={{ width: '100%', mb: 2 }}
            >
              {errorMessage}
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
            
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
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
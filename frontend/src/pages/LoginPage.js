import React, { useState, useEffect } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
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
  const { login, error, loading, isAuthenticated, checkPendingMigration } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showError, setShowError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Redirect to generator page if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const pendingMigration = checkPendingMigration();
      if (pendingMigration) {
        navigate('/migrate');
      } else {
        navigate('/generator');
      }
    }
  }, [isAuthenticated, navigate, checkPendingMigration]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setShowError(false);

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
            Sign in to Learni
          </Typography>
          
          {showError && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
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
              label="Remember me"
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
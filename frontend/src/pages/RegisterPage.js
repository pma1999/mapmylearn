import React, { useState, useEffect } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router';
import { Helmet } from 'react-helmet-async';
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
  Grid,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import { useAuth } from '../services/authContext';

const RegisterPage = () => {
  const navigate = useNavigate();
  const { register, loading: contextLoading, isAuthenticated } = useAuth();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
  });
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [termsError, setTermsError] = useState(false);

  const [errors, setErrors] = useState({});
  const [showError, setShowError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/generator');
    }
  }, [isAuthenticated, navigate]);

  const validateForm = () => {
    const newErrors = {};
    
    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }
    
    // Confirm password validation
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    // Terms validation
    if (!agreedToTerms) {
      setTermsError(true);
    } else {
      setTermsError(false);
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0 && agreedToTerms;
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    
    // Clear error for this field when typing
    if (errors[e.target.name]) {
      setErrors({
        ...errors,
        [e.target.name]: undefined,
      });
    }
    
    // Clear terms error when checkbox is clicked
    if (termsError && e.target.name === 'agreedToTerms') {
      setTermsError(false);
    }
  };

  const handleCheckboxChange = (event) => {
    setAgreedToTerms(event.target.checked);
    // Clear error when checkbox state changes
    if (termsError) {
      setTermsError(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    setShowError(false);
    setShowSuccessMessage(false);
    
    if (!validateForm()) {
      // Check specifically if the terms were the issue
      if (!agreedToTerms) {
        setTermsError(true);
      }
      return;
    }
    
    setIsSubmitting(true);
    
    const result = await register(formData.email, formData.password, formData.fullName);

    if (result.success) {
      setSuccessMessage(result.message);
      setShowSuccessMessage(true);
      setIsSubmitting(false);
    } else {
      setErrorMessage(result.message || 'Registration failed. Please try again.');
      setShowError(true);
      setIsSubmitting(false);
    }
  };

  const isLoading = contextLoading || isSubmitting;

  return (
    <Container maxWidth="sm">
      <Helmet>
        <title>Create Account | MapMyLearn</title>
        <meta name="description" content="Sign up for MapMyLearn to start generating personalized courses and save your progress." />
      </Helmet>
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
            <AccountCircleIcon />
          </Box>
          
          <Typography component="h1" variant="h5" sx={{ mb: 3 }}>
            Create an Account
          </Typography>
          
          {showSuccessMessage && (
            <Alert severity="success" sx={{ width: '100%', mb: 2 }}>
              {successMessage}
            </Alert>
          )}
          
          {showError && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {errorMessage}
            </Alert>
          )}
          
          <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%', pointerEvents: showSuccessMessage ? 'none' : 'auto', opacity: showSuccessMessage ? 0.7 : 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="fullName"
              label="Full Name"
              name="fullName"
              autoComplete="name"
              autoFocus
              value={formData.fullName}
              onChange={handleChange}
              error={!!errors.fullName}
              helperText={errors.fullName}
              disabled={isLoading}
            />
            
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="Email Address"
              name="email"
              autoComplete="email"
              value={formData.email}
              onChange={handleChange}
              error={!!errors.email}
              helperText={errors.email}
              disabled={isLoading}
            />
            
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="new-password"
              value={formData.password}
              onChange={handleChange}
              error={!!errors.password}
              helperText={errors.password}
              disabled={isLoading}
            />
            
            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="Confirm Password"
              type="password"
              id="confirmPassword"
              autoComplete="new-password"
              value={formData.confirmPassword}
              onChange={handleChange}
              error={!!errors.confirmPassword}
              helperText={errors.confirmPassword}
              disabled={isLoading}
            />
            
            <FormControlLabel
              control={
                <Checkbox
                  checked={agreedToTerms}
                  onChange={handleCheckboxChange}
                  name="agreedToTerms"
                  color="primary"
                  required
                  sx={{ '&.Mui-checked': { color: 'primary.main' } }}
                />
              }
              label={
                <Typography variant="body2" color={termsError ? "error" : "text.secondary"}>
                  I have read and agree to the{' '}
                  <Link component={RouterLink} to="/terms" target="_blank" rel="noopener noreferrer" variant="body2">
                    Terms and Conditions
                  </Link>
                  {' '}and acknowledge the{' '}
                  <Link component={RouterLink} to="/privacy" target="_blank" rel="noopener noreferrer" variant="body2">
                    Privacy Policy
                  </Link>
                  .
                </Typography>
              }
              sx={{ mt: 1, mb: 1 }}
            />
            {termsError && (
              <Typography variant="caption" color="error" sx={{ display: 'block', ml: 1.8, mt: -0.5 }}>
                You must accept the terms and conditions to register.
              </Typography>
            )}
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={isLoading || showSuccessMessage || !agreedToTerms}
            >
              {isLoading ? <CircularProgress size={24} /> : 'Create Account'}
            </Button>
            
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <Link component={RouterLink} to="/login" variant="body2">
                Already have an account? Sign in
              </Link>
            </Box>
          </Box>
        </Box>
      </Paper>
      
      <Box sx={{ mt: 3, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          By creating an account, you'll be able to save your courses to the cloud.
        </Typography>
      </Box>
    </Container>
  );
};

export default RegisterPage; 
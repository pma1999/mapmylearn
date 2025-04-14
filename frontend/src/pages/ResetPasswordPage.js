import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
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
  InputAdornment, // For potential show/hide password
  IconButton // For potential show/hide password
} from '@mui/material';
import LockResetIcon from '@mui/icons-material/LockReset'; // Icon suggestion
// import Visibility from '@mui/icons-material/Visibility'; // Icon suggestion
// import VisibilityOff from '@mui/icons-material/VisibilityOff'; // Icon suggestion
import { useAuth } from '../services/authContext';

const ResetPasswordPage = () => {
    const { token } = useParams(); // Get token from URL parameter
    const navigate = useNavigate(); // Hook for redirection
    const { resetPassword } = useAuth(); // Get function from context
    
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    // const [showPassword, setShowPassword] = useState(false); // State for show/hide
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    // Basic password strength check (example - enhance as needed)
    const validatePassword = (password) => {
        if (password.length < 8) {
            return "Password must be at least 8 characters long.";
        }
        // Add more checks (uppercase, lowercase, numbers, symbols) here if desired
        // if (!/[A-Z]/.test(password)) return "Password must contain an uppercase letter.";
        // if (!/[a-z]/.test(password)) return "Password must contain a lowercase letter.";
        // if (!/[0-9]/.test(password)) return "Password must contain a number.";
        return null; // Password is valid
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setMessage('');
        setError('');

        if (newPassword !== confirmPassword) {
            setError('Passwords do not match.');
            setLoading(false);
            return;
        }

        const passwordError = validatePassword(newPassword);
        if (passwordError) {
             setError(passwordError);
             setLoading(false);
             return;
        }

        try {
            const response = await resetPassword(token, newPassword);
            setMessage(response.message);
            // Redirect to login after a short delay
            setTimeout(() => {
                navigate('/login'); // Adjust '/login' to your actual login route
            }, 3000); // 3 second delay

        } catch (err) {
            console.error("Reset password error on page:", err);
            setError(err.message || 'An error occurred while resetting your password. The link may be invalid, expired, or there was a server issue.');
        } finally {
            setLoading(false);
        }
    };

     // Verify token presence on mount
     useEffect(() => {
        if (!token) {
            setError("No valid password reset token provided in the URL.");
            // Optionally disable form or redirect
             setTimeout(() => {
                navigate('/forgot-password'); 
            }, 4000); // Redirect after showing message
        }
     }, [token]); // Removed navigate from dependency array to avoid potential loop if error state causes rerender

    // const handleClickShowPassword = () => setShowPassword((show) => !show);
    // const handleMouseDownPassword = (event) => event.preventDefault();

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
                        <LockResetIcon />
                    </Box>
                    <Typography component="h1" variant="h5" sx={{ mb: 3 }}>
                        Set New Password
                    </Typography>

                    {message && (
                        <Alert severity="success" sx={{ width: '100%', mb: 2 }}>
                            {message}
                        </Alert>
                    )}
                    {error && (
                        <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
                        {error}
                        </Alert>
                    )}
                    
                    {/* Only show form if token exists and no success message */} 
                    {token && !message && (
                        <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
                        <TextField
                            margin="normal"
                            required
                            fullWidth
                            name="newPassword"
                            label="New Password"
                            type={'password'} // Change based on showPassword state if implemented
                            id="newPassword"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            disabled={loading}
                            autoFocus
                            autoComplete="new-password"
                            // Add InputProps for show/hide icon if implementing
                            /*
                            InputProps={{
                                endAdornment: (
                                <InputAdornment position="end">
                                    <IconButton
                                    aria-label="toggle password visibility"
                                    onClick={handleClickShowPassword}
                                    onMouseDown={handleMouseDownPassword}
                                    edge="end"
                                    >
                                    {showPassword ? <VisibilityOff /> : <Visibility />}
                                    </IconButton>
                                </InputAdornment>
                                ),
                            }}
                            */
                        />
                        <TextField
                            margin="normal"
                            required
                            fullWidth
                            name="confirmPassword"
                            label="Confirm New Password"
                            type={'password'} // Change based on showPassword state
                            id="confirmPassword"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            disabled={loading}
                            autoComplete="new-password"
                        />
                        
                        <Button
                            type="submit"
                            fullWidth
                            variant="contained"
                            sx={{ mt: 3, mb: 2 }}
                            disabled={loading}
                        >
                            {loading ? <CircularProgress size={24} /> : 'Reset Password'}
                        </Button>
                        </Box>
                    )}

                    {/* Link to request new reset if error or no token */} 
                    {(error || !token) && !message && (
                         <Box sx={{ mt: 2 }}>
                            <Link component={RouterLink} to="/forgot-password" variant="body2">
                                Need to request a new link?
                            </Link>
                        </Box>
                    )}

                    {/* Link to login if successful */} 
                     {message && (
                         <Box sx={{ mt: 2 }}>
                            <Link component={RouterLink} to="/login" variant="body2">
                                Go to Sign In
                            </Link>
                        </Box>
                    )}
                 </Box>
            </Paper>
        </Container>
    );
};

export default ResetPasswordPage; 
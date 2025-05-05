import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Grid,
  Divider,
  Autocomplete,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormHelperText,
  Alert,
  Snackbar,
  CircularProgress,
  Chip,
  Avatar,
  Slide,
  InputAdornment,
  Collapse
} from '@mui/material';
import TokenIcon from '@mui/icons-material/Token';
import CreditScoreIcon from '@mui/icons-material/CreditScore';
import PersonIcon from '@mui/icons-material/Person';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import InfoIcon from '@mui/icons-material/Info';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

import * as api from '../../../services/api';
import UserManagement from './UserManagement';
import { useAuth } from '../../../services/authContext';

// Maximum credits allowed per transaction
const MAX_CREDITS_PER_TRANSACTION = 1000;
// Threshold for high value confirmation
const HIGH_VALUE_THRESHOLD = 100;

const CreditManagement = ({ setError }) => {
  const [selectedUser, setSelectedUser] = useState(null);
  const [amount, setAmount] = useState('');
  const [notes, setNotes] = useState('');
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [highValueConfirmDialogOpen, setHighValueConfirmDialogOpen] = useState(false);
  const [success, setSuccess] = useState(false);
  const [activeTab, setActiveTab] = useState('form'); // 'form' or 'table'
  const [usersLoading, setUsersLoading] = useState(false);
  const [alertInfo, setAlertInfo] = useState({
    show: false,
    severity: 'info',
    message: ''
  });
  const [formErrors, setFormErrors] = useState({
    user: '',
    amount: ''
  });
  const { fetchUserCredits } = useAuth();

  const fetchUsers = useCallback(async () => {
    try {
      setUsersLoading(true);
      const response = await api.getUsers(1, 100, '');
      if (response && response.users) {
        setUsers(response.users);
      } else {
        throw new Error('Invalid response format from server');
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      setAlertInfo({
        show: true,
        severity: 'error',
        message: error.message || 'Failed to load users. Please refresh the page.'
      });
      setError(error.message || 'Failed to load users');
    } finally {
      setUsersLoading(false);
    }
  }, [setError]);

  useEffect(() => {
    // Fetch real users from API
    fetchUsers();
  }, [fetchUsers]);

  const validateForm = () => {
    let valid = true;
    const errors = {
      user: '',
      amount: ''
    };
    
    if (!selectedUser) {
      errors.user = 'Please select a user';
      valid = false;
    }
    
    if (!amount) {
      errors.amount = 'Please enter an amount';
      valid = false;
    } else {
      const amountNum = parseInt(amount, 10);
      if (isNaN(amountNum) || amountNum <= 0) {
        errors.amount = 'Amount must be a positive number';
        valid = false;
      } else if (amountNum > MAX_CREDITS_PER_TRANSACTION) {
        errors.amount = `Maximum ${MAX_CREDITS_PER_TRANSACTION} credits allowed per transaction`;
        valid = false;
      }
    }
    
    setFormErrors(errors);
    return valid;
  };

  const handleOpenConfirmDialog = () => {
    if (validateForm()) {
      const amountNum = parseInt(amount, 10);
      // Additional confirmation for high-value transactions
      if (amountNum >= HIGH_VALUE_THRESHOLD) {
        setHighValueConfirmDialogOpen(true);
      } else {
        setConfirmDialogOpen(true);
      }
    }
  };

  const handleCloseConfirmDialog = () => {
    setConfirmDialogOpen(false);
  };

  const handleCloseHighValueDialog = () => {
    setHighValueConfirmDialogOpen(false);
  };

  const handleProceedToConfirm = () => {
    setHighValueConfirmDialogOpen(false);
    setConfirmDialogOpen(true);
  };

  const handleAddCredits = async () => {
    if (!selectedUser) {
       setAlertInfo({ show: true, severity: 'error', message: 'No user selected.' });
       return;
    }
    try {
      setLoading(true);
      
      // Validate amount one more time before API call
      const amountNum = parseInt(amount, 10);
      if (isNaN(amountNum) || amountNum <= 0 || amountNum > MAX_CREDITS_PER_TRANSACTION) {
        throw new Error(`Invalid credit amount. Must be between 1 and ${MAX_CREDITS_PER_TRANSACTION}.`);
      }
      
      // API call to add credits
      await api.addCredits(selectedUser.id, amountNum, notes);
      
      // Refresh global user state
      if (fetchUserCredits) {
         await fetchUserCredits();
         console.log("AuthContext refreshed after adding credits.");
      } else {
         console.warn("fetchUserCredits function not available from AuthContext.");
      }

      // Show success message AFTER refresh
      setSuccess(true);

      // Reset form
      setSelectedUser(null);
      setAmount('');
      setNotes('');
      setConfirmDialogOpen(false);
            
      // Refresh users data list in this component to ensure it's up to date
      fetchUsers();
      
    } catch (error) {
      console.error('Error adding credits:', error);
      setAlertInfo({
        show: true,
        severity: 'error',
        message: error.response?.data?.detail || error.message || 'Failed to add credits. Please try again.'
      });
      setError(error.response?.data?.detail || error.message || 'Failed to add credits');
      setConfirmDialogOpen(false);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectUser = (user) => {
    setSelectedUser(user);
    setActiveTab('form');
  };

  const handleTabChange = (tabValue) => {
    setActiveTab(tabValue);
  };

  const closeAlert = () => {
    setAlertInfo(prev => ({ ...prev, show: false }));
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Credit Management
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Assign credits to users for generating courses. Each course generation consumes one credit.
      </Typography>
      
      <Collapse in={alertInfo.show}>
        <Alert 
          severity={alertInfo.severity}
          action={
            <Button color="inherit" size="small" onClick={closeAlert}>
              Close
            </Button>
          }
          sx={{ mb: 2 }}
        >
          {alertInfo.message}
        </Alert>
      </Collapse>
      
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', mb: 2 }}>
          <Button
            variant={activeTab === 'form' ? 'contained' : 'outlined'}
            onClick={() => handleTabChange('form')}
            sx={{ mr: 1 }}
          >
            Credit Form
          </Button>
          <Button
            variant={activeTab === 'table' ? 'contained' : 'outlined'}
            onClick={() => handleTabChange('table')}
          >
            User Table
          </Button>
        </Box>
        
        <Divider sx={{ mb: 3 }} />
        
        {activeTab === 'form' ? (
          <Paper elevation={2} sx={{ p: 3 }}>
            <form>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Autocomplete
                    options={users}
                    getOptionLabel={(option) => `${option.email} (${option.credits} credits)`}
                    value={selectedUser}
                    onChange={(event, newValue) => {
                      setSelectedUser(newValue);
                      setFormErrors(prev => ({ ...prev, user: '' }));
                    }}
                    isOptionEqualToValue={(option, value) => option.id === value.id}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Select User"
                        error={!!formErrors.user}
                        helperText={formErrors.user}
                        fullWidth
                        InputProps={{
                          ...params.InputProps,
                          endAdornment: (
                            <>
                              {usersLoading ? <CircularProgress size={20} /> : null}
                              {params.InputProps.endAdornment}
                            </>
                          ),
                        }}
                      />
                    )}
                    renderOption={(props, option) => {
                      const { key, ...otherProps } = props;
                      return (
                        <li key={key} {...otherProps}>
                          <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                            <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                              <PersonIcon />
                            </Avatar>
                            <Box sx={{ flexGrow: 1 }}>
                              <Typography variant="body1">{option.email}</Typography>
                              <Typography variant="body2" color="text.secondary">
                                {option.full_name || 'No name provided'}
                              </Typography>
                            </Box>
                            <Chip
                              icon={<TokenIcon />}
                              label={`${option.credits} credits`}
                              size="small"
                              color={option.credits > 0 ? 'primary' : 'default'}
                            />
                          </Box>
                        </li>
                      );
                    }}
                    loading={usersLoading}
                    loadingText="Loading users..."
                    noOptionsText="No users found"
                    disabled={loading}
                  />
                </Grid>
                
                {selectedUser && (
                  <Grid item xs={12}>
                    <Box sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Selected User Details
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="body2" color="text.secondary">
                            Email:
                          </Typography>
                          <Typography variant="body1">
                            {selectedUser.email}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="body2" color="text.secondary">
                            Name:
                          </Typography>
                          <Typography variant="body1">
                            {selectedUser.full_name || 'Not provided'}
                          </Typography>
                        </Grid>
                        <Grid item xs={12}>
                          <Typography variant="body2" color="text.secondary">
                            Current Credits:
                          </Typography>
                          <Chip
                            icon={<TokenIcon />}
                            label={`${selectedUser.credits} credits`}
                            color={selectedUser.credits > 0 ? 'primary' : 'default'}
                          />
                        </Grid>
                      </Grid>
                    </Box>
                  </Grid>
                )}
                
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Credit Amount"
                    type="number"
                    value={amount}
                    onChange={(e) => {
                      // Prevent negative values and non-numeric input
                      const value = e.target.value;
                      if (value === '' || (parseInt(value, 10) >= 0 && /^\d+$/.test(value))) {
                        setAmount(value);
                        setFormErrors(prev => ({ ...prev, amount: '' }));
                      }
                    }}
                    inputProps={{ 
                      min: 1, 
                      max: MAX_CREDITS_PER_TRANSACTION,
                      'aria-label': 'Credit amount'
                    }}
                    fullWidth
                    error={!!formErrors.amount}
                    helperText={formErrors.amount || `Maximum ${MAX_CREDITS_PER_TRANSACTION} credits per transaction`}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <TokenIcon />
                        </InputAdornment>
                      ),
                    }}
                    disabled={loading}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    label="Notes (Optional)"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    fullWidth
                    multiline
                    rows={3}
                    placeholder="Add any notes about this credit assignment"
                    inputProps={{
                      maxLength: 500
                    }}
                    helperText={`${notes.length}/500 characters`}
                    disabled={loading}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  {loading || usersLoading ? (
                    <span>
                      <Button
                        variant="contained"
                        color="primary"
                        disabled={true}
                        startIcon={<CircularProgress size={20} />}
                        size="large"
                      >
                        Add Credits
                      </Button>
                    </span>
                  ) : (
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={handleOpenConfirmDialog}
                      disabled={false}
                      startIcon={<CreditScoreIcon />}
                      size="large"
                    >
                      Add Credits
                    </Button>
                  )}
                </Grid>
              </Grid>
            </form>
          </Paper>
        ) : (
          <UserManagement 
            setError={setError} 
            onSelectUserForCredits={handleSelectUser} 
          />
        )}
      </Box>
      
      {/* High Value Confirmation Dialog */}
      <Dialog
        open={highValueConfirmDialogOpen}
        onClose={handleCloseHighValueDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ bgcolor: 'warning.light', color: 'warning.contrastText', display: 'flex', alignItems: 'center' }}>
          <WarningAmberIcon sx={{ mr: 1 }} />
          High Value Transaction Warning
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body1" gutterBottom>
              You are about to add <strong>{amount} credits</strong> to a user account.
            </Typography>
            <Typography variant="body1" gutterBottom>
              This is a high-value transaction. Please confirm that you intend to add this many credits.
            </Typography>
            
            <Alert severity="warning" sx={{ mt: 2 }}>
              <Typography variant="body2">
                For security purposes, this action will be logged with your administrator ID, timestamp, and IP address.
              </Typography>
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseHighValueDialog}>Cancel</Button>
          <Button
            onClick={handleProceedToConfirm}
            variant="contained"
            color="warning"
          >
            Yes, Proceed
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Regular Confirmation Dialog */}
      <Dialog
        open={confirmDialogOpen}
        onClose={handleCloseConfirmDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Confirm Credit Addition</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to add <strong>{amount} credits</strong> to the following user?
          </Typography>
          
          {selectedUser && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
              <Typography variant="subtitle2">
                <strong>Email:</strong> {selectedUser.email}
              </Typography>
              <Typography variant="subtitle2">
                <strong>Name:</strong> {selectedUser.full_name || 'Not provided'}
              </Typography>
              <Typography variant="subtitle2">
                <strong>Current Credits:</strong> {selectedUser.credits}
              </Typography>
              <Typography variant="subtitle2">
                <strong>New Balance:</strong> {parseInt(selectedUser.credits) + parseInt(amount || 0)}
              </Typography>
            </Box>
          )}
          
          {notes && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2">Notes:</Typography>
              <Typography variant="body2">{notes}</Typography>
            </Box>
          )}
          
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              This action will be logged for auditing purposes.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseConfirmDialog}>Cancel</Button>
          {loading ? (
            <span>
              <Button
                variant="contained"
                color="primary"
                disabled={true}
                startIcon={<CircularProgress size={20} />}
              >
                Confirm
              </Button>
            </span>
          ) : (
            <Button
              onClick={handleAddCredits}
              variant="contained"
              color="primary"
              disabled={false}
              startIcon={<CreditScoreIcon />}
            >
              Confirm
            </Button>
          )}
        </DialogActions>
      </Dialog>
      
      {/* Success notification */}
      <Snackbar
        open={success}
        autoHideDuration={6000}
        onClose={() => setSuccess(false)}
        TransitionComponent={Slide}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity="success"
          variant="filled"
          icon={<CheckCircleOutlineIcon />}
          onClose={() => setSuccess(false)}
        >
          Credits added successfully!
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CreditManagement; 
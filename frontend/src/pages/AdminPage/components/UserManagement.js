import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  IconButton,
  Tooltip,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch,
  CircularProgress,
  Divider,
  InputAdornment,
  Alert,
  Collapse
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import EditIcon from '@mui/icons-material/Edit';
import TokenIcon from '@mui/icons-material/Token';
import CreditScoreIcon from '@mui/icons-material/CreditScore';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import PersonOffIcon from '@mui/icons-material/PersonOff';
import PersonIcon from '@mui/icons-material/Person';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import RefreshIcon from '@mui/icons-material/Refresh';
import { formatDistance, parseISO } from 'date-fns';

import * as api from '../../../services/api';
import { useAuth } from '../../../services/authContext';

// Define refresh interval in milliseconds
const AUTO_REFRESH_INTERVAL = 60000; // 60 seconds
const DEBOUNCE_SEARCH_DELAY = 500; // 500ms debounce for search

const UserManagement = ({ setError, onSelectUserForCredits }) => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalUsers, setTotalUsers] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchInputValue, setSearchInputValue] = useState('');
  const [editUserDialog, setEditUserDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [formValues, setFormValues] = useState({
    full_name: '',
    is_active: true,
    is_admin: false
  });
  const [saveLoading, setSaveLoading] = useState(false);
  const [lastRefreshTime, setLastRefreshTime] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [alertInfo, setAlertInfo] = useState({
    show: false,
    severity: 'info',
    message: ''
  });

  // Fetch users function that can be called from multiple places
  const fetchUsers = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      
      const response = await api.getUsers(page + 1, rowsPerPage, searchTerm);
      
      if (response && response.users) {
        setUsers(response.users);
        setTotalUsers(response.total);
        setLastRefreshTime(new Date());
      } else {
        throw new Error('Invalid response format from server');
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      setAlertInfo({
        show: true,
        severity: 'error',
        message: error.message || 'Failed to load users'
      });
      setError(error.message || 'Failed to load users');
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }, [page, rowsPerPage, searchTerm, setError]);

  // Fetch users on component mount and when search/pagination changes
  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Setup auto-refresh
  useEffect(() => {
    let refreshInterval;
    
    if (autoRefresh) {
      refreshInterval = setInterval(() => {
        fetchUsers(false); // Don't show loading indicator for auto-refresh
      }, AUTO_REFRESH_INTERVAL);
    }
    
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [autoRefresh, fetchUsers]);

  // Debounce search term input
  useEffect(() => {
    const handler = setTimeout(() => {
      if (searchInputValue !== searchTerm) {
        setSearchTerm(searchInputValue);
        setPage(0); // Reset to first page with new search
      }
    }, DEBOUNCE_SEARCH_DELAY);
    
    return () => {
      clearTimeout(handler);
    };
  }, [searchInputValue, searchTerm]);

  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  const handleRowsPerPageChange = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleManualRefresh = () => {
    fetchUsers();
  };

  const toggleAutoRefresh = () => {
    setAutoRefresh(prev => !prev);
  };

  const handleSearchChange = (event) => {
    setSearchInputValue(event.target.value);
  };

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setFormValues({
      full_name: user.full_name || '',
      is_active: user.is_active,
      is_admin: user.is_admin
    });
    setEditUserDialog(true);
  };

  const handleCloseEditDialog = () => {
    setEditUserDialog(false);
    setSelectedUser(null);
  };

  const handleFormChange = (event) => {
    const { name, checked, value } = event.target;
    setFormValues(prev => ({
      ...prev,
      [name]: name === 'is_active' || name === 'is_admin' ? checked : value
    }));
  };

  const handleSaveUser = async () => {
    try {
      setSaveLoading(true);
      
      // Security check - prevent removing admin privileges from your own account
      if (selectedUser.id === currentUser?.id && !formValues.is_admin && selectedUser.is_admin) {
        throw new Error('You cannot remove your own admin privileges');
      }
      
      // Additional validation
      if (formValues.full_name && formValues.full_name.length > 100) {
        throw new Error('Full name must be less than 100 characters');
      }
      
      // API call to update user
      await api.updateUser(selectedUser.id, formValues);
      
      // Update local state to reflect changes
      setUsers(users.map(u => {
        if (u.id === selectedUser.id) {
          return { ...u, ...formValues };
        }
        return u;
      }));
      
      setAlertInfo({
        show: true,
        severity: 'success',
        message: `User ${selectedUser.email} updated successfully`
      });
      
      setEditUserDialog(false);
      setSelectedUser(null);
      
      // Refresh the user list to ensure we have the latest data
      fetchUsers(false);
      
    } catch (error) {
      console.error('Error updating user:', error);
      setAlertInfo({
        show: true,
        severity: 'error',
        message: error.message || 'Failed to update user'
      });
      setError(error.message || 'Failed to update user');
    } finally {
      setSaveLoading(false);
    }
  };

  const handleAddCredits = (user) => {
    if (onSelectUserForCredits) {
      onSelectUserForCredits(user);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    try {
      const date = parseISO(dateString);
      return formatDistance(date, new Date(), { addSuffix: true });
    } catch (error) {
      console.error('Error formatting date:', error);
      return 'Invalid date';
    }
  };

  const closeAlert = () => {
    setAlertInfo(prev => ({ ...prev, show: false }));
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        User Management
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        View and manage all users in the system. You can edit user details, assign admin privileges, and manage credits.
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

      <Box sx={{ mb: 3, display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
        <TextField
          placeholder="Search users..."
          variant="outlined"
          value={searchInputValue}
          onChange={handleSearchChange}
          sx={{ flexGrow: 1, maxWidth: { xs: '100%', sm: 300, md: 400 } }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title={`Last refreshed ${lastRefreshTime ? formatDistance(lastRefreshTime, new Date(), { addSuffix: true }) : 'never'}`}>
            {loading ? (
              <span>
                <Button
                  variant="outlined"
                  startIcon={<CircularProgress size={20} />}
                  disabled={true}
                >
                  Refresh
                </Button>
              </span>
            ) : (
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={handleManualRefresh}
                disabled={false}
              >
                Refresh
              </Button>
            )}
          </Tooltip>
          
          <Button
            variant={autoRefresh ? "contained" : "outlined"}
            color={autoRefresh ? "success" : "primary"}
            onClick={toggleAutoRefresh}
            size="small"
          >
            {autoRefresh ? "Auto-Refresh On" : "Auto-Refresh Off"}
          </Button>
        </Box>
      </Box>

      <TableContainer component={Paper} elevation={2}>
        <Table sx={{ minWidth: 650 }}>
          <TableHead>
            <TableRow sx={{ backgroundColor: theme => theme.palette.primary.main }}>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Email</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Name</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Status</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Role</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Credits</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Registered</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Last Login</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 3 }}>
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 3 }}>
                  No users found
                </TableCell>
              </TableRow>
            ) : (
              users.map((user) => (
                <TableRow key={user.id} hover>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>{user.full_name || 'Not provided'}</TableCell>
                  <TableCell>
                    {user.is_active ? (
                      <Chip 
                        icon={<VerifiedUserIcon />} 
                        label="Active" 
                        color="success" 
                        size="small"
                      />
                    ) : (
                      <Chip 
                        icon={<PersonOffIcon />} 
                        label="Inactive" 
                        color="error" 
                        size="small"
                      />
                    )}
                  </TableCell>
                  <TableCell>
                    {user.is_admin ? (
                      <Chip 
                        icon={<AdminPanelSettingsIcon />} 
                        label="Admin" 
                        color="primary" 
                        size="small"
                      />
                    ) : (
                      <Chip 
                        icon={<PersonIcon />} 
                        label="User" 
                        color="default" 
                        size="small"
                      />
                    )}
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      <TokenIcon sx={{ mr: 0.5, color: 'primary.main' }} fontSize="small" />
                      {user.credits}
                    </Box>
                  </TableCell>
                  <TableCell>{formatDate(user.created_at)}</TableCell>
                  <TableCell>{formatDate(user.last_login)}</TableCell>
                  <TableCell>
                    <Box>
                      <Tooltip title="Edit User">
                        {user.id === currentUser?.id && user.is_admin ? (
                          <span>
                            <IconButton 
                              size="small"
                              aria-label="Edit user"
                              disabled={true}
                            >
                              <EditIcon />
                            </IconButton>
                          </span>
                        ) : (
                          <IconButton 
                            onClick={() => handleEditUser(user)}
                            size="small"
                            aria-label="Edit user"
                            disabled={false}
                          >
                            <EditIcon />
                          </IconButton>
                        )}
                      </Tooltip>
                      <Tooltip title="Add Credits">
                        <IconButton 
                          onClick={() => handleAddCredits(user)}
                          size="small"
                          aria-label="Add credits"
                        >
                          <CreditScoreIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={totalUsers}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handlePageChange}
          onRowsPerPageChange={handleRowsPerPageChange}
        />
      </TableContainer>

      {/* Edit User Dialog */}
      <Dialog 
        open={editUserDialog} 
        onClose={handleCloseEditDialog} 
        maxWidth="sm" 
        fullWidth
        aria-labelledby="edit-user-dialog-title"
      >
        <DialogTitle id="edit-user-dialog-title">
          Edit User
          <Typography variant="subtitle2" color="text.secondary">
            {selectedUser?.email}
          </Typography>
        </DialogTitle>
        <Divider />
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              margin="normal"
              label="Full Name"
              name="full_name"
              value={formValues.full_name}
              onChange={handleFormChange}
              inputProps={{ maxLength: 100 }}
              helperText={`${formValues.full_name.length}/100 characters`}
            />
            <Box sx={{ mt: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formValues.is_active}
                    onChange={handleFormChange}
                    name="is_active"
                    color="success"
                  />
                }
                label="Active User"
              />
            </Box>
            <Box sx={{ mt: 1 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formValues.is_admin}
                    onChange={handleFormChange}
                    name="is_admin"
                    color="primary"
                    disabled={selectedUser?.id === currentUser?.id}
                  />
                }
                label="Admin Privileges"
              />
              {selectedUser?.id === currentUser?.id && (
                <Typography variant="caption" color="error">
                  You cannot revoke your own admin privileges
                </Typography>
              )}
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseEditDialog}>Cancel</Button>
          <Button 
            onClick={handleSaveUser}
            variant="contained"
            color="primary"
            disabled={saveLoading}
            startIcon={saveLoading ? <CircularProgress size={20} /> : null}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserManagement; 
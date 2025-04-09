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
  Chip,
  IconButton,
  TextField,
  Button,
  Grid,
  Divider,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  InputAdornment,
  Tooltip,
  Alert,
  Collapse
} from '@mui/material';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers';
import { formatDistance, format, isValid, parseISO } from 'date-fns';
import FilterListIcon from '@mui/icons-material/FilterList';
import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import RefreshIcon from '@mui/icons-material/Refresh';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import PermDataSettingIcon from '@mui/icons-material/PermDataSetting';
import DownloadIcon from '@mui/icons-material/Download';
import InfoIcon from '@mui/icons-material/Info';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import PersonIcon from '@mui/icons-material/Person';

import * as api from '../../../services/api';

// Define refresh interval in milliseconds
const AUTO_REFRESH_INTERVAL = 60000; // 60 seconds

const TransactionHistory = ({ setError }) => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalTransactions, setTotalTransactions] = useState(0);
  const [filterMenuAnchor, setFilterMenuAnchor] = useState(null);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [alertInfo, setAlertInfo] = useState({
    show: false,
    severity: 'info',
    message: ''
  });
  const [lastRefreshTime, setLastRefreshTime] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  // Filter states
  const [filters, setFilters] = useState({
    actionType: '',
    fromDate: null,
    toDate: null,
    userId: '',
    adminId: ''
  });

  // Function to fetch transactions
  const fetchTransactions = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      
      const response = await api.getCreditTransactions(
        page + 1, 
        rowsPerPage, 
        filters.actionType,
        filters.fromDate,
        filters.toDate,
        filters.userId,
        filters.adminId
      );
      
      if (response && response.transactions) {
        setTransactions(response.transactions);
        setTotalTransactions(response.total);
        setLastRefreshTime(new Date());
      } else {
        throw new Error('Invalid response format from server');
      }
    } catch (error) {
      console.error('Error fetching transactions:', error);
      setAlertInfo({
        show: true,
        severity: 'error',
        message: error.message || 'Failed to load transaction history'
      });
      setError(error.message || 'Failed to load transaction history');
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }, [page, rowsPerPage, filters, setError]);

  // Initial load and refresh on filter/pagination changes
  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  // Setup auto-refresh
  useEffect(() => {
    let refreshInterval;
    
    if (autoRefresh) {
      refreshInterval = setInterval(() => {
        fetchTransactions(false); // Don't show loading indicator for auto-refresh
      }, AUTO_REFRESH_INTERVAL);
    }
    
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [autoRefresh, fetchTransactions]);

  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  const handleRowsPerPageChange = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleFilterMenuOpen = (event) => {
    setFilterMenuAnchor(event.currentTarget);
  };

  const handleFilterMenuClose = () => {
    setFilterMenuAnchor(null);
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
    setPage(0);
  };

  const clearFilters = () => {
    setFilters({
      actionType: '',
      fromDate: null,
      toDate: null,
      userId: '',
      adminId: ''
    });
    setPage(0);
    handleFilterMenuClose();
  };

  const handleManualRefresh = () => {
    fetchTransactions();
  };

  const toggleAutoRefresh = () => {
    setAutoRefresh(prev => !prev);
  };

  const handleExportCSV = async () => {
    try {
      setExportLoading(true);
      
      // Security check - limit export size
      if (totalTransactions > 10000) {
        setAlertInfo({
          show: true,
          severity: 'warning',
          message: 'Export limited to 10,000 records. Please apply filters to narrow down your data.'
        });
        return;
      }
      
      // Create CSV content with proper escaping for all fields
      const headers = ['ID', 'User', 'Admin', 'Amount', 'Type', 'Date', 'Notes'];
      
      const sanitizeForCSV = (text) => {
        if (text === null || text === undefined) return '';
        const str = String(text);
        // If the string contains commas, quotes, or newlines, wrap it in quotes and escape any quotes
        if (str.includes(',') || str.includes('"') || str.includes('\n')) {
          return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
      };
      
      const csvRows = [
        headers.join(','),
        ...transactions.map(t => [
          t.id,
          sanitizeForCSV(t.user_email),
          sanitizeForCSV(t.admin_email || 'System'),
          t.amount,
          t.action_type,
          format(parseISO(t.created_at), 'yyyy-MM-dd HH:mm:ss'),
          sanitizeForCSV(t.notes || '')
        ].join(','))
      ];
      
      const csvContent = csvRows.join('\n');
      
      // Create download link
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      const timestamp = format(new Date(), 'yyyy-MM-dd_HHmmss');
      
      link.setAttribute('href', url);
      link.setAttribute('download', `credit-transactions-${timestamp}.csv`);
      document.body.appendChild(link);
      link.click();
      
      // Clean up
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 100);
      
      setAlertInfo({
        show: true,
        severity: 'success',
        message: 'CSV export completed successfully.'
      });
    } catch (error) {
      console.error('Error exporting CSV:', error);
      setAlertInfo({
        show: true,
        severity: 'error', 
        message: 'Failed to export transaction data: ' + (error.message || 'Unknown error')
      });
      setError('Failed to export transaction data');
    } finally {
      setExportLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    try {
      const date = parseISO(dateString);
      if (!isValid(date)) return 'Invalid date';
      return format(date, 'PPP p'); // Format as "Apr 29, 2023, 3:45 PM"
    } catch (e) {
      return 'Invalid date';
    }
  };

  const formatTimeAgo = (dateString) => {
    if (!dateString) return 'Unknown';
    try {
      const date = parseISO(dateString);
      if (!isValid(date)) return 'Invalid date';
      return formatDistance(date, new Date(), { addSuffix: true });
    } catch (e) {
      return 'Invalid date';
    }
  };

  const getChipColor = (type) => {
    switch (type) {
      case 'admin_add':
        return 'primary';
      case 'generation_use':
        return 'error';
      case 'refund':
        return 'success';
      case 'system_add':
        return 'info';
      default:
        return 'default';
    }
  };

  const getChipIcon = (type) => {
    switch (type) {
      case 'admin_add':
        return <AdminPanelSettingsIcon />;
      case 'generation_use':
        return <RemoveIcon />;
      case 'refund':
        return <RefreshIcon />;
      case 'system_add':
        return <PermDataSettingIcon />;
      default:
        return null;
    }
  };

  const getActionTypeLabel = (type) => {
    switch (type) {
      case 'admin_add':
        return 'Admin Addition';
      case 'generation_use':
        return 'Generation Usage';
      case 'refund':
        return 'Credit Refund';
      case 'system_add':
        return 'System Addition';
      default:
        return type;
    }
  };

  const openTransactionDetails = (transaction) => {
    setSelectedTransaction(transaction);
    setDetailsOpen(true);
  };

  const closeAlert = () => {
    setAlertInfo(prev => ({ ...prev, show: false }));
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Transaction History
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        View all credit transactions including admin additions, usage, and refunds. Filter and export data as needed.
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
      
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item>
            <Button
              variant="outlined"
              startIcon={<FilterListIcon />}
              onClick={handleFilterMenuOpen}
              sx={{ minWidth: 120 }}
            >
              Filter
              {Object.values(filters).some(v => v !== '' && v !== null) && (
                <Box
                  component="span"
                  sx={{
                    ml: 1,
                    width: 6,
                    height: 6,
                    bgcolor: 'primary.main',
                    borderRadius: '50%',
                    display: 'inline-block'
                  }}
                />
              )}
            </Button>
          </Grid>
          
          <Grid item>
            <Tooltip title={`Last refreshed ${lastRefreshTime ? formatTimeAgo(lastRefreshTime) : 'never'}`}>
              {loading ? (
                <span>
                  <Button
                    variant="outlined"
                    startIcon={<CircularProgress size={20} />}
                    onClick={handleManualRefresh}
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
          </Grid>
          
          <Grid item>
            <Button
              variant={autoRefresh ? "contained" : "outlined"}
              color={autoRefresh ? "success" : "primary"}
              onClick={toggleAutoRefresh}
              size="small"
            >
              {autoRefresh ? "Auto-Refresh On" : "Auto-Refresh Off"}
            </Button>
          </Grid>
          
          {filters.actionType && (
            <Grid item>
              <Chip
                label={`Type: ${getActionTypeLabel(filters.actionType)}`}
                onDelete={() => handleFilterChange('actionType', '')}
                color="primary"
                variant="outlined"
                size="small"
              />
            </Grid>
          )}
          
          {(filters.fromDate || filters.toDate) && (
            <Grid item>
              <Chip
                label={`Date: ${filters.fromDate ? format(filters.fromDate, 'PP') : 'Any'} to ${filters.toDate ? format(filters.toDate, 'PP') : 'Now'}`}
                onDelete={() => {
                  handleFilterChange('fromDate', null);
                  handleFilterChange('toDate', null);
                }}
                color="primary"
                variant="outlined"
                size="small"
              />
            </Grid>
          )}
          
          {filters.userId && (
            <Grid item>
              <Chip
                label={`User ID: ${filters.userId}`}
                onDelete={() => handleFilterChange('userId', '')}
                color="primary"
                variant="outlined"
                size="small"
              />
            </Grid>
          )}
          
          {filters.adminId && (
            <Grid item>
              <Chip
                label={`Admin ID: ${filters.adminId}`}
                onDelete={() => handleFilterChange('adminId', '')}
                color="primary"
                variant="outlined"
                size="small"
              />
            </Grid>
          )}
          
          <Grid item sx={{ ml: 'auto' }}>
            {transactions.length === 0 || exportLoading ? (
              <span>
                <Button
                  variant="outlined"
                  startIcon={exportLoading ? <CircularProgress size={20} /> : <DownloadIcon />}
                  disabled={true}
                >
                  Export CSV
                </Button>
              </span>
            ) : (
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={handleExportCSV}
                disabled={false}
              >
                Export CSV
              </Button>
            )}
          </Grid>
        </Grid>
      </Box>
      
      <Menu
        anchorEl={filterMenuAnchor}
        open={Boolean(filterMenuAnchor)}
        onClose={handleFilterMenuClose}
        PaperProps={{
          sx: { maxWidth: 400, width: '100%', p: 2 }
        }}
      >
        <Typography variant="subtitle1" sx={{ px: 2, pb: 1 }}>
          Filter Transactions
        </Typography>
        <Divider sx={{ my: 1 }} />
        
        <Box sx={{ p: 2 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            Transaction Type
          </Typography>
          <Grid container spacing={1}>
            <Grid item xs={6}>
              <Button
                fullWidth
                variant={filters.actionType === 'admin_add' ? 'contained' : 'outlined'}
                size="small"
                onClick={() => handleFilterChange('actionType', filters.actionType === 'admin_add' ? '' : 'admin_add')}
                startIcon={<AdminPanelSettingsIcon />}
                sx={{ justifyContent: 'flex-start', mb: 1 }}
              >
                Admin Add
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                fullWidth
                variant={filters.actionType === 'generation_use' ? 'contained' : 'outlined'}
                size="small"
                onClick={() => handleFilterChange('actionType', filters.actionType === 'generation_use' ? '' : 'generation_use')}
                startIcon={<RemoveIcon />}
                sx={{ justifyContent: 'flex-start', mb: 1 }}
              >
                Usage
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                fullWidth
                variant={filters.actionType === 'refund' ? 'contained' : 'outlined'}
                size="small"
                onClick={() => handleFilterChange('actionType', filters.actionType === 'refund' ? '' : 'refund')}
                startIcon={<RefreshIcon />}
                sx={{ justifyContent: 'flex-start' }}
              >
                Refund
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                fullWidth
                variant={filters.actionType === 'system_add' ? 'contained' : 'outlined'}
                size="small"
                onClick={() => handleFilterChange('actionType', filters.actionType === 'system_add' ? '' : 'system_add')}
                startIcon={<PermDataSettingIcon />}
                sx={{ justifyContent: 'flex-start' }}
              >
                System Add
              </Button>
            </Grid>
          </Grid>
        </Box>
        
        <Divider sx={{ my: 1 }} />
        
        <Box sx={{ p: 2 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            Date Range
          </Typography>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <DatePicker
                  label="From Date"
                  value={filters.fromDate}
                  onChange={(date) => handleFilterChange('fromDate', date)}
                  renderInput={(params) => <TextField {...params} size="small" fullWidth />}
                  maxDate={filters.toDate || undefined}
                />
              </Grid>
              <Grid item xs={6}>
                <DatePicker
                  label="To Date"
                  value={filters.toDate}
                  onChange={(date) => handleFilterChange('toDate', date)}
                  renderInput={(params) => <TextField {...params} size="small" fullWidth />}
                  minDate={filters.fromDate || undefined}
                  maxDate={new Date()}
                />
              </Grid>
            </Grid>
          </LocalizationProvider>
        </Box>
        
        <Divider sx={{ my: 1 }} />
        
        <Box sx={{ p: 2 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            User / Admin ID
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <TextField
                label="User ID"
                value={filters.userId}
                onChange={(e) => {
                  // Only allow numbers
                  const value = e.target.value;
                  if (value === '' || /^\d+$/.test(value)) {
                    handleFilterChange('userId', value);
                  }
                }}
                size="small"
                fullWidth
                type="number"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <PersonIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
                inputProps={{ min: 1 }}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                label="Admin ID"
                value={filters.adminId}
                onChange={(e) => {
                  // Only allow numbers
                  const value = e.target.value;
                  if (value === '' || /^\d+$/.test(value)) {
                    handleFilterChange('adminId', value);
                  }
                }}
                size="small"
                fullWidth
                type="number"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <AdminPanelSettingsIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
                inputProps={{ min: 1 }}
              />
            </Grid>
          </Grid>
        </Box>
        
        <Divider sx={{ my: 1 }} />
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', p: 2 }}>
          <Button 
            onClick={clearFilters}
            sx={{ mr: 1 }}
          >
            Clear All
          </Button>
          <Button 
            onClick={handleFilterMenuClose}
            variant="contained"
          >
            Apply Filters
          </Button>
        </Box>
      </Menu>
      
      <TableContainer component={Paper} elevation={2}>
        <Table sx={{ minWidth: 650 }}>
          <TableHead>
            <TableRow sx={{ backgroundColor: (theme) => theme.palette.primary.main }}>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>ID</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Type</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>User</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Admin</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Amount</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Date</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 3 }}>
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : transactions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 3 }}>
                  No transactions found
                </TableCell>
              </TableRow>
            ) : (
              transactions.map((transaction) => (
                <TableRow key={transaction.id} hover>
                  <TableCell>{transaction.id}</TableCell>
                  <TableCell>
                    <Chip
                      icon={getChipIcon(transaction.action_type)}
                      label={getActionTypeLabel(transaction.action_type)}
                      color={getChipColor(transaction.action_type)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Tooltip title={`User ID: ${transaction.user_id}`}>
                      <Box>{transaction.user_email}</Box>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    {transaction.admin_id ? (
                      <Tooltip title={`Admin ID: ${transaction.admin_id}`}>
                        <Box>{transaction.admin_email}</Box>
                      </Tooltip>
                    ) : (
                      'System'
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography
                      sx={{
                        color: transaction.amount > 0 ? 'success.main' : 'error.main',
                        fontWeight: 'bold'
                      }}
                    >
                      {transaction.amount > 0 ? `+${transaction.amount}` : transaction.amount}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Tooltip title={formatDate(transaction.created_at)}>
                      <Box>{formatTimeAgo(transaction.created_at)}</Box>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    <IconButton
                      onClick={() => openTransactionDetails(transaction)}
                      size="small"
                      aria-label="View transaction details"
                    >
                      <InfoIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={totalTransactions}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handlePageChange}
          onRowsPerPageChange={handleRowsPerPageChange}
        />
      </TableContainer>
      
      {/* Transaction Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center">
            <ReceiptLongIcon sx={{ mr: 1 }} />
            Transaction Details
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {selectedTransaction && (
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Box display="flex" justifyContent="center" mb={2}>
                  <Chip
                    icon={getChipIcon(selectedTransaction.action_type)}
                    label={getActionTypeLabel(selectedTransaction.action_type)}
                    color={getChipColor(selectedTransaction.action_type)}
                    sx={{ px: 2, py: 3, '& .MuiChip-label': { fontSize: '1rem' } }}
                  />
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">Transaction ID</Typography>
                <Typography variant="body1">{selectedTransaction.id}</Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">Date & Time</Typography>
                <Typography variant="body1">{formatDate(selectedTransaction.created_at)}</Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">User</Typography>
                <Typography variant="body1">{selectedTransaction.user_email}</Typography>
                <Typography variant="caption" color="text.secondary">ID: {selectedTransaction.user_id}</Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">Admin</Typography>
                <Typography variant="body1">
                  {selectedTransaction.admin_email || 'System'}
                  {selectedTransaction.admin_id && (
                    <>
                      <br />
                      <Typography variant="caption" color="text.secondary">
                        ID: {selectedTransaction.admin_id}
                      </Typography>
                    </>
                  )}
                </Typography>
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">Credit Amount</Typography>
                <Typography 
                  variant="h5"
                  sx={{
                    color: selectedTransaction.amount > 0 ? 'success.main' : 'error.main',
                    fontWeight: 'bold'
                  }}
                >
                  {selectedTransaction.amount > 0 ? `+${selectedTransaction.amount}` : selectedTransaction.amount}
                </Typography>
              </Grid>
              
              {selectedTransaction.notes && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">Notes</Typography>
                  <Paper 
                    variant="outlined" 
                    sx={{ 
                      p: 2, 
                      bgcolor: 'background.default',
                      mt: 1
                    }}
                  >
                    <Typography variant="body2">{selectedTransaction.notes}</Typography>
                  </Paper>
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default TransactionHistory;
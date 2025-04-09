import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Divider,
  CircularProgress,
  Paper,
  Skeleton,
  Alert
} from '@mui/material';
import PersonOutlineIcon from '@mui/icons-material/PersonOutline';
import PeopleIcon from '@mui/icons-material/People';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import TokenIcon from '@mui/icons-material/Token';
import EqualizerIcon from '@mui/icons-material/Equalizer';
import CreditScoreIcon from '@mui/icons-material/CreditScore';
import PersonAddAltIcon from '@mui/icons-material/PersonAddAlt';

import * as api from '../../../services/api';

// Dashboard card component
const DashboardCard = ({ title, value, icon, color, loading }) => (
  <Card 
    elevation={3} 
    sx={{ 
      height: '100%',
      borderLeft: `4px solid ${color}`,
      transition: 'transform 0.3s',
      '&:hover': {
        transform: 'translateY(-4px)',
      }
    }}
  >
    <CardContent>
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Box>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {title}
          </Typography>
          {loading ? (
            <Skeleton variant="text" width={80} height={40} />
          ) : (
            <Typography variant="h4">
              {value}
            </Typography>
          )}
        </Box>
        <Box 
          sx={{ 
            bgcolor: `${color}20`, 
            p: 1.5, 
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {React.cloneElement(icon, { sx: { fontSize: 30, color: color } })}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const AdminDashboard = ({ setError }) => {
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeUsers: 0,
    adminUsers: 0,
    totalCredits: 0,
    creditsUsed: 0,
    recentTransactions: 0,
    usersWithCredits: 0,
    averageCredits: 0
  });
  const [loading, setLoading] = useState(true);
  const [hasErrors, setHasErrors] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 2;

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setHasErrors(false);
        // Fetch dashboard statistics from API
        const response = await api.getAdminStats();
        if (response && response.stats) {
          setStats(response.stats);
          // Reset retry count on success
          setRetryCount(0);
        } else {
          throw new Error('Invalid response format from server');
        }
      } catch (error) {
        console.error('Error fetching admin stats:', error);
        setHasErrors(true);
        setError(error.message || 'Failed to load dashboard statistics');
        
        // Implement retry logic for transient errors
        if (retryCount < MAX_RETRIES) {
          const nextRetry = retryCount + 1;
          setRetryCount(nextRetry);
          console.log(`Retrying fetch stats (${nextRetry}/${MAX_RETRIES})...`);
          // Exponential backoff: 2s, 4s
          setTimeout(() => fetchStats(), 2000 * Math.pow(2, retryCount));
        }
      } finally {
        setLoading(false);
      }
    };

    // Fetch admin stats
    fetchStats();
  }, [setError, retryCount]);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Overview Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Key statistics and performance metrics for your application.
      </Typography>

      {hasErrors && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }}
          onClose={() => setHasErrors(false)}
        >
          Failed to load dashboard statistics. Please refresh the page or try again later.
        </Alert>
      )}

      <Divider sx={{ my: 3 }} />

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4}>
          <DashboardCard 
            title="Total Users"
            value={stats.totalUsers}
            icon={<PeopleIcon />}
            color="#3f51b5"
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <DashboardCard 
            title="Active Users"
            value={stats.activeUsers}
            icon={<PersonOutlineIcon />}
            color="#4caf50"
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <DashboardCard 
            title="Admin Users"
            value={stats.adminUsers}
            icon={<AdminPanelSettingsIcon />}
            color="#ff9800"
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <DashboardCard 
            title="Total Credits Assigned"
            value={stats.totalCredits}
            icon={<TokenIcon />}
            color="#e91e63"
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <DashboardCard 
            title="Credits Used"
            value={stats.creditsUsed}
            icon={<EqualizerIcon />}
            color="#2196f3"
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <DashboardCard 
            title="Users With Credits"
            value={stats.usersWithCredits}
            icon={<CreditScoreIcon />}
            color="#9c27b0"
            loading={loading}
          />
        </Grid>
      </Grid>

      <Box sx={{ mt: 4 }}>
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Quick Tips
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="body2" paragraph>
            • <strong>User Management:</strong> View all users, edit their details, and manage their admin status.
          </Typography>
          <Typography variant="body2" paragraph>
            • <strong>Credit Management:</strong> Add credits to user accounts and view their current balance.
          </Typography>
          <Typography variant="body2" paragraph>
            • <strong>Transaction History:</strong> Track all credit transactions including additions, usages, and refunds.
          </Typography>
          <Typography variant="body2" sx={{ mt: 2 }}>
            Remember that all admin actions are logged for security purposes.
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
};

export default AdminDashboard; 
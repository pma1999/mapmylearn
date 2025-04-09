import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Tabs,
  Tab,
  Paper,
  Alert,
  Fade,
  CircularProgress
} from '@mui/material';
import PeopleAltIcon from '@mui/icons-material/PeopleAlt';
import TokenIcon from '@mui/icons-material/Token';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import DashboardIcon from '@mui/icons-material/Dashboard';

import { useAuth } from '../../services/authContext';
import UserManagement from './components/UserManagement';
import CreditManagement from './components/CreditManagement';
import TransactionHistory from './components/TransactionHistory';
import AdminDashboard from './components/AdminDashboard';

// TabPanel component to display tab content
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
      style={{ padding: '20px 0' }}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

function a11yProps(index) {
  return {
    id: `admin-tab-${index}`,
    'aria-controls': `admin-tabpanel-${index}`,
  };
}

const AdminPage = () => {
  const navigate = useNavigate();
  const { user, loading } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [error, setError] = useState(null);

  // Redirect if not an admin
  useEffect(() => {
    if (!loading && (!user || !user.is_admin)) {
      navigate('/');
    }
  }, [user, loading, navigate]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!user || !user.is_admin) {
    return null; // Will be redirected by useEffect
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          mb: 3,
          background: 'linear-gradient(45deg, #1a237e 30%, #283593 90%)',
          color: 'white'
        }}
      >
        <Typography variant="h4" component="h1" gutterBottom>
          Admin Dashboard
        </Typography>
        <Typography variant="subtitle1">
          Manage users, credits, and view transaction history
        </Typography>
      </Paper>

      {error && (
        <Fade in={!!error}>
          <Alert 
            severity="error" 
            sx={{ mb: 3 }}
            onClose={() => setError(null)}
          >
            {error}
          </Alert>
        </Fade>
      )}

      <Paper elevation={2}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          variant="fullWidth"
          scrollButtons="auto"
          allowScrollButtonsMobile
          sx={{
            '& .MuiTab-root': {
              minHeight: '72px',
            },
            borderBottom: 1,
            borderColor: 'divider',
          }}
        >
          <Tab 
            icon={<DashboardIcon />} 
            label="Dashboard" 
            {...a11yProps(0)} 
          />
          <Tab 
            icon={<PeopleAltIcon />} 
            label="User Management" 
            {...a11yProps(1)} 
          />
          <Tab 
            icon={<TokenIcon />} 
            label="Credit Management" 
            {...a11yProps(2)} 
          />
          <Tab 
            icon={<ReceiptLongIcon />} 
            label="Transaction History" 
            {...a11yProps(3)} 
          />
        </Tabs>

        <Box sx={{ p: 2 }}>
          <TabPanel value={tabValue} index={0}>
            <AdminDashboard setError={setError} />
          </TabPanel>
          <TabPanel value={tabValue} index={1}>
            <UserManagement setError={setError} />
          </TabPanel>
          <TabPanel value={tabValue} index={2}>
            <CreditManagement setError={setError} />
          </TabPanel>
          <TabPanel value={tabValue} index={3}>
            <TransactionHistory setError={setError} />
          </TabPanel>
        </Box>
      </Paper>
    </Container>
  );
};

export default AdminPage; 
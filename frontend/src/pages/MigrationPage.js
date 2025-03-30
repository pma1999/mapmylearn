import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  Alert,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
} from '@mui/material';
import FolderIcon from '@mui/icons-material/Folder';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import { useAuth } from '../services/authContext';
import * as api from '../services/api';

const MigrationPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated, migrateLearningPaths, checkPendingMigration } = useAuth();

  const [loading, setLoading] = useState(false);
  const [migrationComplete, setMigrationComplete] = useState(false);
  const [localPaths, setLocalPaths] = useState([]);
  const [error, setError] = useState(null);
  const [migrationStats, setMigrationStats] = useState(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    // Check if there's anything to migrate
    const pendingMigration = checkPendingMigration();
    if (!pendingMigration) {
      navigate('/generator');
      return;
    }

    // Load local learning paths
    const localHistory = api.getLocalHistoryRaw();
    if (localHistory && localHistory.entries) {
      setLocalPaths(localHistory.entries);
    }
  }, [isAuthenticated, navigate, checkPendingMigration]);

  const handleMigrate = async () => {
    setLoading(true);
    setError(null);

    try {
      // Pre-process local paths to ensure IDs are preserved properly
      const processedPaths = localPaths.map(path => {
        // Ensure the path has an ID value that can be preserved
        if (!path.id && !path.path_id) {
          // Generate a UUID if no ID exists at all
          path.id = String(Date.now()) + '-' + Math.random().toString(36).substring(2, 15);
        } 
        // If path.id exists, ensure it's a string
        else if (path.id) {
          path.id = String(path.id);
        }
        // If only path_id exists, use that as id
        else if (path.path_id) {
          path.id = String(path.path_id);
        }
        
        // Make sure path_data exists
        if (!path.path_data) {
          // If it's not there, use the entry itself as path_data
          // This handles the case where the entire entry is actually the path data
          path.path_data = {...path};
        }
        
        return path;
      });
      
      console.log('Starting migration with processed paths:', processedPaths);
      
      const result = await migrateLearningPaths(processedPaths);
      setMigrationStats(result);
      setMigrationComplete(true);
    } catch (err) {
      setError(err.message || 'Failed to migrate learning paths. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    // Clear pending migration flag
    localStorage.removeItem('pendingMigration');
    navigate('/generator');
  };

  const handleContinue = () => {
    navigate('/history');
  };

  return (
    <Container maxWidth="md">
      <Paper elevation={3} sx={{ p: { xs: 2, sm: 4 }, mt: 6 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Box
            sx={{
              backgroundColor: 'primary.main',
              color: 'white',
              borderRadius: '50%',
              p: 1,
              mb: 2,
            }}
          >
            <CloudUploadIcon fontSize="large" />
          </Box>

          <Typography component="h1" variant="h4" sx={{ mb: 2 }}>
            {migrationComplete ? 'Migration Complete!' : 'Migrate Learning Paths'}
          </Typography>

          {migrationComplete ? (
            <Box sx={{ width: '100%', mb: 3 }}>
              <Alert severity="success" sx={{ mb: 3 }}>
                Successfully migrated {migrationStats?.migrated_count || 0} learning paths to your account.
              </Alert>
              
              <Typography variant="body1" sx={{ mb: 3, textAlign: 'center' }}>
                All your learning paths are now safely stored in your account and accessible from any device.
              </Typography>
              
              <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  onClick={handleContinue}
                  startIcon={<CheckCircleOutlineIcon />}
                >
                  View My Learning Paths
                </Button>
              </Box>
            </Box>
          ) : (
            <>
              <Typography variant="body1" sx={{ mb: 3, textAlign: 'center' }}>
                We've found {localPaths.length} learning path{localPaths.length !== 1 ? 's' : ''} stored 
                in your browser. Would you like to migrate them to your account?
              </Typography>

              {error && (
                <Alert severity="error" sx={{ width: '100%', mb: 3 }}>
                  {error}
                </Alert>
              )}

              {localPaths.length > 0 && (
                <Box sx={{ width: '100%', mb: 3 }}>
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    Learning Paths Found:
                  </Typography>
                  <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
                    {localPaths.slice(0, 5).map((path, index) => (
                      <ListItem key={index} divider={index < Math.min(localPaths.length, 5) - 1}>
                        <ListItemIcon>
                          <FolderIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={path.topic}
                          secondary={`Created: ${new Date(path.creation_date).toLocaleDateString()}`}
                        />
                        <Chip
                          label={path.source === 'generated' ? 'Generated' : 'Imported'}
                          color={path.source === 'generated' ? 'primary' : 'secondary'}
                          size="small"
                        />
                      </ListItem>
                    ))}
                    {localPaths.length > 5 && (
                      <ListItem>
                        <ListItemText 
                          primary={`And ${localPaths.length - 5} more...`} 
                          sx={{ fontStyle: 'italic', color: 'text.secondary' }}
                        />
                      </ListItem>
                    )}
                  </List>
                </Box>
              )}

              <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mt: 2 }}>
                <Button
                  variant="outlined"
                  color="primary"
                  onClick={handleSkip}
                  disabled={loading}
                >
                  Skip
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleMigrate}
                  disabled={loading || localPaths.length === 0}
                  startIcon={loading ? <CircularProgress size={20} /> : <CloudUploadIcon />}
                >
                  {loading ? 'Migrating...' : 'Migrate Now'}
                </Button>
              </Box>
            </>
          )}
        </Box>
      </Paper>

      <Box sx={{ mt: 3, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Your data is securely stored in your account and will be available whenever you sign in.
        </Typography>
      </Box>
    </Container>
  );
};

export default MigrationPage; 
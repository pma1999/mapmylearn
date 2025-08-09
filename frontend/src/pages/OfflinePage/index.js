import React, { useEffect, useState } from 'react';
import { Box, Typography, List, ListItem, ListItemButton, ListItemText, Divider, IconButton, Button, Alert, Chip } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import InfoIcon from '@mui/icons-material/Info';
import SchoolIcon from '@mui/icons-material/School';
import { Link as RouterLink } from 'react-router';
import { getOfflinePaths, removeOfflinePath, estimateUsage, getOfflinePathsIndex } from '../../services/offlineService';
import { usePwaIntro } from '../../contexts/PwaIntroContext';

const OfflinePage = () => {
  const [paths, setPaths] = useState([]);
  const [storageInfo, setStorageInfo] = useState('Unknown');
  const { openPwaIntro, pwaCapabilities } = usePwaIntro();

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getOfflinePaths();
        setPaths(Object.values(data));
      } catch (e) {
        console.warn('Failed to load offline paths:', e);
        setPaths([]);
      }
      try {
        const usage = await estimateUsage();
        if (usage?.usedBytes != null) {
          const sizeInKB = (usage.usedBytes / 1024).toFixed(1);
          setStorageInfo(`${sizeInKB} KB${usage.quotaBytes ? ` of ${(usage.quotaBytes / (1024 * 1024)).toFixed(1)} MB` : ''}`);
        } else {
          setStorageInfo('Unknown');
        }
      } catch (e) {
        setStorageInfo('Unknown');
      }
    };
    load();
  }, []);

  const handleDelete = async (id) => {
    try {
      await removeOfflinePath(id);
      const updated = await getOfflinePaths();
      setPaths(Object.values(updated));
      // refresh storage info
      const usage = await estimateUsage();
      if (usage?.usedBytes != null) {
        const sizeInKB = (usage.usedBytes / 1024).toFixed(1);
        setStorageInfo(`${sizeInKB} KB${usage.quotaBytes ? ` of ${(usage.quotaBytes / (1024 * 1024)).toFixed(1)} MB` : ''}`);
      }
    } catch (e) {
      console.warn('Failed to remove offline path:', e);
    }
  };

  const getTotalCoursesSize = () => {
    return paths.length;
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
          <SchoolIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h4" component="h1">
            Offline Learning Paths
          </Typography>
        </Box>
        <Button 
          size="small" 
          variant="outlined" 
          onClick={openPwaIntro}
          startIcon={<InfoIcon />}
        >
          App Tutorial
        </Button>
      </Box>

      {/* Status information */}
      <Box sx={{ mb: 3 }}>
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            <strong>Offline Learning:</strong> Courses saved here work without internet connection. 
            Perfect for travel, commuting, or areas with poor connectivity.
          </Typography>
        </Alert>
        
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          <Chip 
            label={`${getTotalCoursesSize()} courses saved`} 
            color="primary"
            size="small"
          />
          <Chip 
            label={`Storage: ${storageInfo}`} 
            variant="outlined"
            size="small"
          />
          {pwaCapabilities && (
            <Chip 
              label={pwaCapabilities.canUseOffline ? 'Offline Ready' : 'Limited Offline Support'} 
              color={pwaCapabilities.canUseOffline ? 'success' : 'warning'}
              size="small"
            />
          )}
        </Box>
      </Box>

      {/* Courses list */}
      {paths.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No offline courses saved yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            To save a course for offline use:
          </Typography>
          <Box sx={{ textAlign: 'left', maxWidth: 400, mx: 'auto' }}>
            <Typography variant="body2" color="text.secondary" component="ol" sx={{ pl: 2 }}>
              <li>Generate or open a course</li>
              <li>Save it to your History</li>
              <li>The course will automatically be available offline</li>
            </Typography>
          </Box>
          <Button 
            variant="contained" 
            component={RouterLink} 
            to="/" 
            sx={{ mt: 2 }}
          >
            Generate Your First Course
          </Button>
        </Box>
      ) : (
        <Box>
          <Typography variant="h6" gutterBottom>
            Your Offline Courses
          </Typography>
          <List>
            {paths.map((path, index) => (
              <React.Fragment key={path.offline_id}>
                <ListItem
                  secondaryAction={
                    <IconButton 
                      edge="end" 
                      aria-label="delete" 
                      onClick={() => handleDelete(path.offline_id)}
                      title="Remove from offline storage"
                    >
                      <DeleteIcon />
                    </IconButton>
                  }
                  disablePadding
                >
                  <ListItemButton 
                    component={RouterLink} 
                    to={`/offline/${path.offline_id}`}
                    sx={{ 
                      borderRadius: 1,
                      '&:hover': {
                        backgroundColor: 'action.hover'
                      }
                    }}
                  >
                    <ListItemText 
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle1" fontWeight="medium">
                            {path.topic || 'Untitled Course'}
                          </Typography>
                          <Chip 
                            label="Offline"
                            size="small"
                            color="success"
                            sx={{ fontSize: '0.7rem', height: 20 }}
                          />
                        </Box>
                      }
                      secondary={
                        path.saved_at 
                          ? `Saved ${new Date(path.saved_at).toLocaleDateString()}`
                          : 'Course available offline'
                      }
                    />
                  </ListItemButton>
                </ListItem>
                {index < paths.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
          
          <Box sx={{ mt: 3, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary">
              💡 <strong>Pro Tip:</strong> These courses work completely offline. 
              Once loaded, you can access all content, take quizzes, and read materials 
              without any internet connection.
            </Typography>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default OfflinePage;

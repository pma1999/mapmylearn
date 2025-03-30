import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  Typography,
  Box,
  Paper,
  Container,
  LinearProgress,
  CircularProgress,
  Alert,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Card,
  CardContent,
  Stack,
  Chip,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  FormControlLabel,
  Checkbox,
  InputAdornment,
  IconButton,
  useTheme,
  useMediaQuery
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DownloadIcon from '@mui/icons-material/Download';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import HomeIcon from '@mui/icons-material/Home';
import ErrorIcon from '@mui/icons-material/Error';
import AddIcon from '@mui/icons-material/Add';
import SaveIcon from '@mui/icons-material/Save';
import StorageIcon from '@mui/icons-material/Storage';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';

// Import shared MarkdownRenderer component
import MarkdownRenderer from '../components/MarkdownRenderer';

// Import API service
import { getLearningPath, getProgressUpdates, saveToHistory, updateHistoryEntry, getHistoryEntry } from '../services/api';

// Import new components
import LearningPathHeader from '../components/organisms/LearningPathHeader';
import ModuleGrid from '../components/organisms/ModuleGrid';
import RelatedResourcesSection from '../components/organisms/RelatedResourcesSection';
import LearningPathSkeleton from '../components/molecules/LearningPathSkeleton';
import ErrorState from '../components/molecules/ErrorState';
import ProgressUpdates from '../components/molecules/ProgressUpdates';

// Styled chip component for tags
const StyledChip = ({ label, onDelete }) => (
  <Chip
    label={label}
    onDelete={onDelete}
    size="small"
    sx={{ margin: 0.5 }}
  />
);

function ResultPage(props) {
  // Add theme and media query hooks for responsive design
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isMedium = useMediaQuery(theme.breakpoints.down('md'));
  
  const { taskId, entryId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const isFromHistory = location.pathname.startsWith('/history/') || props.source === 'history';
  const [learningPath, setLearningPath] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [progressMessages, setProgressMessages] = useState([]);
  const progressEventSourceRef = useRef(null);
  const [savedToHistory, setSavedToHistory] = useState(false);
  
  // Save to history dialog state
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [tags, setTags] = useState([]);
  const [newTag, setNewTag] = useState('');
  const [favorite, setFavorite] = useState(false);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });

  // Auto-save preference from session storage
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(false);
  const [initialTags, setInitialTags] = useState([]);
  const [initialFavorite, setInitialFavorite] = useState(false);

  // Feature flag for future extensions
  const [showRelatedResources, setShowRelatedResources] = useState(false);

  // Load auto-save preferences from session storage when component mounts
  useEffect(() => {
    try {
      const autoSavePreference = sessionStorage.getItem('autoSaveToHistory');
      const savedTags = sessionStorage.getItem('initialTags');
      const savedFavorite = sessionStorage.getItem('initialFavorite');
      
      setAutoSaveEnabled(autoSavePreference === 'true');
      
      if (savedTags) {
        try {
          setInitialTags(JSON.parse(savedTags));
        } catch (e) {
          console.error('Failed to parse saved tags:', e);
          setInitialTags([]);
        }
      }
      
      setInitialFavorite(savedFavorite === 'true');
      
      // Clear the preferences from session storage after retrieving them
      // to avoid affecting future learning path generations
      sessionStorage.removeItem('autoSaveToHistory');
      sessionStorage.removeItem('initialTags');
      sessionStorage.removeItem('initialFavorite');
    } catch (e) {
      console.error('Error loading auto-save preferences:', e);
    }
  }, []);

  useEffect(() => {
    const loadLearningPath = async () => {
      setLoading(true);
      setError(null);
      
      try {
        if (isFromHistory) {
          // Load from history API
          const historyResponse = await getHistoryEntry(entryId);
          if (!historyResponse || !historyResponse.entry) {
            throw new Error('Learning path not found in history. It may have been deleted or not properly migrated.');
          }
          const pathData = historyResponse.entry.path_data;
          setLearningPath(pathData);
          setSavedToHistory(true);
          setLoading(false);
        } else {
          // Load from task API
          const response = await getLearningPath(taskId);
          
          if (response.status === 'completed' && response.learning_path) {
            setLearningPath(response.learning_path);
            setSavedToHistory(true);
            setLoading(false);
            
            // Close event source if it's open
            if (progressEventSourceRef.current) {
              progressEventSourceRef.current.close();
              progressEventSourceRef.current = null;
            }
          } else if (response.status === 'failed') {
            // Task failed
            setError(response.error?.message || 'Learning path generation failed');
            setLoading(false);
          } else if (response.status === 'pending' || response.status === 'in_progress') {
            // Start listening for updates since task is still in progress
            setupProgressUpdates();
          }
        }
      } catch (err) {
        console.error('Error loading learning path:', err);
        setError(err.message || 'Error loading learning path. Please try again.');
        setLoading(false);
      }
    };
    
    // Only load data if we have a task ID or entry ID
    if (taskId || (isFromHistory && entryId)) {
      loadLearningPath();
    }
    
    // Cleanup function
    return () => {
      if (progressEventSourceRef.current) {
        progressEventSourceRef.current.close();
        progressEventSourceRef.current = null;
      }
    };
  }, [taskId, entryId, isFromHistory, getLearningPath, getHistoryEntry]);

  const setupProgressUpdates = () => {
    try {
      const eventSource = getProgressUpdates(
        taskId,
        (data) => {
          if (data.message) {
            setProgressMessages((prev) => [...prev, data]);
          }
        },
        (error) => {
          console.error('SSE Error:', error);
        },
        () => {
          // On complete - will trigger the polling to fetch final result
        }
      );
      
      progressEventSourceRef.current = eventSource;
    } catch (err) {
      console.error('Error setting up progress updates:', err);
    }
  };

  const handleDownloadJSON = () => {
    if (!learningPath) return;
    
    try {
      const json = JSON.stringify(learningPath, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `learning_path_${learningPath.topic.replace(/\s+/g, '_').substring(0, 30)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      showNotification('Learning path downloaded successfully', 'success');
    } catch (err) {
      console.error('Error downloading JSON:', err);
      showNotification('Failed to download learning path', 'error');
    }
  };

  const handleHomeClick = () => {
    navigate('/');
  };

  const handleNewLearningPathClick = () => {
    navigate('/generator');
  };
  
  const handleSaveToHistory = () => {
    if (savedToHistory) {
      showNotification('This learning path is already saved to history', 'info');
      return;
    }
    setSaveDialogOpen(true);
  };
  
  const handleSaveDialogClose = () => {
    setSaveDialogOpen(false);
  };
  
  const handleSaveConfirm = async () => {
    if (!learningPath) return;
    
    try {
      const result = await saveToHistory(learningPath, 'generated');
      
      if (result.success) {
        setSavedToHistory(true);
        showNotification('Learning path saved to history successfully', 'success');
        
        // If tags or favorite are set, update the entry
        if (tags.length > 0 || favorite) {
          try {
            await updateHistoryEntry(result.entry_id, { tags, favorite });
          } catch (error) {
            console.error('Error updating history entry:', error);
          }
        }
      } else {
        showNotification('Failed to save learning path to history', 'error');
      }
      
      setSaveDialogOpen(false);
    } catch (error) {
      console.error('Error saving to history:', error);
      showNotification('Failed to save learning path to history', 'error');
      setSaveDialogOpen(false);
    }
  };
  
  // Tag management functions
  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag('');
    }
  };
  
  const handleDeleteTag = (tagToDelete) => {
    setTags(tags.filter(tag => tag !== tagToDelete));
  };
  
  const handleTagKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };
  
  // Notification helper
  const showNotification = (message, severity = 'success') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };
  
  const handleNotificationClose = (event, reason) => {
    if (reason === 'clickaway') return;
    setNotification({ ...notification, open: false });
  };

  // Loading state
  if (loading) {
    // Retrieve the topic from sessionStorage
    const storedTopic = sessionStorage.getItem('currentTopic');
    
    return (
      <Container maxWidth="lg" sx={{ py: { xs: 3, md: 4 } }}>
        {progressMessages.length > 0 ? (
          <Box>
            <Paper
              elevation={0}
              sx={{
                p: { xs: 2, md: 3 },
                borderRadius: 3,
                bgcolor: 'background.paper',
                mb: 3
              }}
            >
              <Typography variant="h4" component="h1" gutterBottom color="primary" fontWeight="500">
                Generating Learning Path
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                We're creating a comprehensive learning path for "{storedTopic || 'your topic'}". 
                The AI is analyzing the topic, researching content, and structuring the perfect learning journey for you.
              </Typography>
            </Paper>
            
            <ProgressUpdates progressMessages={progressMessages} />
          </Box>
        ) : (
          <LearningPathSkeleton />
        )}
      </Container>
    );
  }

  // Error state
  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: { xs: 3, md: 4 } }}>
        <Paper
          elevation={3}
          sx={{
            p: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            maxWidth: '600px',
            mx: 'auto',
            mt: 4
          }}
        >
          <ErrorIcon color="error" sx={{ fontSize: 60, mb: 2 }} />
          
          <Typography variant="h5" component="h2" gutterBottom fontWeight="bold">
            Error Generating Learning Path
          </Typography>
          
          <Typography variant="body1" sx={{ mb: 3 }}>
            {error.includes("not found") 
              ? "The learning path you're looking for couldn't be found. It may have been deleted or not properly migrated from your local storage."
              : error
            }
          </Typography>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
            We recommend trying one of the following options:
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
            <Button 
              variant="contained" 
              color="primary" 
              startIcon={<HomeIcon />}
              onClick={handleHomeClick}
            >
              Go to Home
            </Button>
            
            <Button 
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={handleNewLearningPathClick}
            >
              Create New Path
            </Button>
          </Box>
        </Paper>
      </Container>
    );
  }

  // Success state - show learning path
  return (
    <Container maxWidth="lg" sx={{ py: { xs: 3, md: 4 } }}>
      {/* Header Section */}
      <LearningPathHeader 
        topic={learningPath.topic}
        savedToHistory={savedToHistory}
        onDownload={handleDownloadJSON}
        onSaveToHistory={handleSaveToHistory}
        onNewLearningPath={handleNewLearningPathClick}
      />
      
      {/* Modules Section */}
      <ModuleGrid modules={learningPath.modules} />
      
      {/* Related Resources Section - placeholder for future features */}
      <RelatedResourcesSection enabled={showRelatedResources} />
      
      {/* Save to History Dialog */}
      <Dialog 
        open={saveDialogOpen}
        onClose={handleSaveDialogClose}
        maxWidth="sm"
        fullWidth
        aria-modal="true"
        disablePortal={false}
        PaperProps={{
          sx: { 
            m: { xs: 2, sm: 3 },
            width: { xs: 'calc(100% - 16px)', sm: 'auto' },
            borderRadius: 2
          }
        }}
        aria-labelledby="save-dialog-title"
        BackdropProps={{
          "aria-hidden": "true"
        }}
        slots={{
          backdrop: 'div'
        }}
      >
        <DialogTitle id="save-dialog-title">
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <StorageIcon sx={{ mr: 1, color: theme.palette.primary.main }} />
            <Typography variant="h6" sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
              Save to Local History
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <DialogContentText sx={{ mb: 2, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
            This learning path will be saved to your browser's local storage. It will be available only on this device and browser.
          </DialogContentText>
          
          <FormControlLabel
            control={
              <Checkbox
                icon={<StarBorderIcon />}
                checkedIcon={<StarIcon />}
                checked={favorite}
                onChange={(e) => setFavorite(e.target.checked)}
                color="primary"
              />
            }
            label={
              <Typography sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                Mark as favorite
              </Typography>
            }
            sx={{ mb: 2 }}
          />
          
          <Typography variant="subtitle2" gutterBottom sx={{ fontSize: { xs: '0.8125rem', sm: '0.875rem' } }}>
            Tags:
          </Typography>
          
          <Box sx={{ display: 'flex', flexWrap: 'wrap', mb: 1 }}>
            {tags.map((tag) => (
              <StyledChip
                key={tag}
                label={tag}
                onDelete={() => handleDeleteTag(tag)}
              />
            ))}
          </Box>
          
          <Box sx={{ display: 'flex' }}>
            <TextField
              size="small"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyDown={handleTagKeyDown}
              placeholder="Add tag..."
              variant="outlined"
              fullWidth
              sx={{ mr: 1 }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton 
                      onClick={handleAddTag} 
                      disabled={!newTag.trim()}
                      size="small"
                      aria-label="add tag"
                    >
                      <AddIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: { xs: 2, sm: 3 }, pb: { xs: 2, sm: 2 } }}>
          <Button onClick={handleSaveDialogClose} size={isMobile ? "small" : "medium"}>
            Cancel
          </Button>
          <Button 
            onClick={handleSaveConfirm}
            color="primary"
            variant="contained"
            startIcon={<SaveIcon />}
            size={isMobile ? "small" : "medium"}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleNotificationClose}
        anchorOrigin={{ 
          vertical: 'bottom', 
          horizontal: isMobile ? 'center' : 'right' 
        }}
        sx={{
          bottom: { xs: 16, sm: 24 }
        }}
      >
        <Alert 
          onClose={handleNotificationClose} 
          severity={notification.severity}
          sx={{ width: { xs: '100%', sm: 'auto' } }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}

export default ResultPage; 
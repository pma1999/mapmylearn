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

  // Feature flag for future extensions
  const [showRelatedResources, setShowRelatedResources] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        if (isFromHistory) {
          // Load from history
          const historyEntryId = entryId || location.pathname.split('/history/')[1];
          const data = await getHistoryEntry(historyEntryId);
          
          if (data && data.entry) {
            setLearningPath(data.entry.path_data);
            setSavedToHistory(true); // It's already in history
            setLoading(false);
          } else {
            setError('Learning path not found in history.');
            setLoading(false);
          }
        } else {
          // Load from API (existing code)
          const data = await getLearningPath(taskId);
          
          if (data.status === 'completed') {
            setLearningPath(data.result);
            setLoading(false);
          } else if (data.status === 'error') {
            setError(data.error || 'An error occurred while generating your learning path.');
            setLoading(false);
          } else if (data.status === 'running') {
            // If still running, set up event source for progress updates
            setupProgressUpdates();
            
            // Poll for completion every 5 seconds
            const interval = setInterval(async () => {
              try {
                const updatedData = await getLearningPath(taskId);
                if (updatedData.status !== 'running') {
                  clearInterval(interval);
                  if (progressEventSourceRef.current) {
                    progressEventSourceRef.current.close();
                  }
                  
                  if (updatedData.status === 'completed') {
                    setLearningPath(updatedData.result);
                  } else if (updatedData.status === 'error') {
                    setError(updatedData.error || 'An error occurred while generating your learning path.');
                  }
                  setLoading(false);
                }
              } catch (err) {
                console.error('Error polling for learning path:', err);
              }
            }, 5000);
            
            return () => {
              clearInterval(interval);
              if (progressEventSourceRef.current) {
                progressEventSourceRef.current.close();
              }
            };
          }
        }
      } catch (err) {
        console.error('Error fetching learning path:', err);
        setError('Failed to fetch learning path. Please try again later.');
        setLoading(false);
      }
    };
    
    fetchData();
  }, [taskId, entryId, isFromHistory, location.pathname]);

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
    return (
      <Container maxWidth="lg" sx={{ py: { xs: 3, md: 4 } }}>
        {progressMessages.length > 0 ? (
          <ProgressUpdates progressMessages={progressMessages} />
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
        <ErrorState 
          error={error} 
          onHomeClick={handleHomeClick} 
          onTryAgainClick={handleNewLearningPathClick} 
        />
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
        PaperProps={{
          sx: { 
            m: { xs: 2, sm: 3 },
            width: { xs: 'calc(100% - 16px)', sm: 'auto' },
            borderRadius: 2
          }
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <StorageIcon sx={{ mr: 1, color: theme.palette.primary.main }} />
            <Typography variant="h6" sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
              Save to Local History
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
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
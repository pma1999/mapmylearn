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
      <Container maxWidth="md" sx={{ px: { xs: 2, sm: 3 } }}>
        <Paper elevation={3} sx={{ p: { xs: 2, sm: 3, md: 4 }, borderRadius: 2, mb: 4 }}>
          <Box sx={{ textAlign: 'center', my: 3 }}>
            <CircularProgress color="primary" />
            <Typography variant="h5" sx={{ mt: 2, fontSize: { xs: '1.2rem', sm: '1.5rem' } }}>
              Generating Your Learning Path
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 1, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
              This may take a few minutes depending on the complexity of the topic.
            </Typography>
            <LinearProgress sx={{ mt: 4, mb: 2 }} />
          </Box>
          
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              Progress Updates:
            </Typography>
            {progressMessages.length === 0 ? (
              <Typography color="text.secondary" sx={{ fontStyle: 'italic' }}>
                Waiting for updates...
              </Typography>
            ) : (
              <Box sx={{ maxHeight: '300px', overflow: 'auto', p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
                {progressMessages.map((msg, index) => (
                  <Typography key={index} sx={{ mb: 1, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                    <span style={{ color: '#555', fontWeight: 'bold' }}>
                      {new Date(msg.timestamp).toLocaleTimeString()}: 
                    </span> {msg.message}
                  </Typography>
                ))}
              </Box>
            )}
          </Box>
        </Paper>
      </Container>
    );
  }

  // Error state
  if (error) {
    return (
      <Container maxWidth="md" sx={{ px: { xs: 2, sm: 3 } }}>
        <Paper elevation={3} sx={{ p: { xs: 2, sm: 3, md: 4 }, borderRadius: 2, mb: 4 }}>
          <Box sx={{ textAlign: 'center', my: 3 }}>
            <ErrorIcon color="error" sx={{ fontSize: { xs: 48, sm: 64 } }} />
            <Typography variant="h5" color="error" sx={{ mt: 2, fontSize: { xs: '1.2rem', sm: '1.5rem' } }}>
              Error Generating Learning Path
            </Typography>
            <Alert severity="error" sx={{ mt: 3, mb: 3 }}>
              {error}
            </Alert>
            <Stack direction="row" spacing={2} justifyContent="center" sx={{ mt: 4 }}>
              <Button
                variant="outlined"
                startIcon={<HomeIcon />}
                onClick={handleHomeClick}
                size={isMobile ? "small" : "medium"}
              >
                Go to Homepage
              </Button>
              <Button
                variant="contained"
                color="primary"
                onClick={handleNewLearningPathClick}
                size={isMobile ? "small" : "medium"}
              >
                Try Again
              </Button>
            </Stack>
          </Box>
        </Paper>
      </Container>
    );
  }

  // Success state - show learning path
  return (
    <Container maxWidth="lg" sx={{ px: { xs: 2, sm: 3 } }}>
      <Paper elevation={3} sx={{ p: { xs: 2, sm: 3, md: 4 }, borderRadius: 2, mb: 4 }}>
        {/* Header - Learning Path title and action buttons */}
        <Box sx={{ mb: 3 }}>
          <Typography 
            variant="h4" 
            component="h1" 
            sx={{ 
              fontWeight: 'bold', 
              mb: { xs: 2, md: 1 },
              fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' }
            }}
          >
            Learning Path
          </Typography>
          
          {/* Mobile view - Stack buttons vertically */}
          {isMedium ? (
            <Stack direction="column" spacing={1.5} sx={{ width: '100%' }}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<DownloadIcon />}
                onClick={handleDownloadJSON}
                size={isMobile ? "small" : "medium"}
              >
                Download JSON
              </Button>
              <Button
                variant="outlined"
                fullWidth
                color="secondary"
                startIcon={<SaveIcon />}
                onClick={handleSaveToHistory}
                disabled={savedToHistory}
                size={isMobile ? "small" : "medium"}
              >
                {savedToHistory ? 'Saved' : 'Save to History'}
              </Button>
              <Button
                variant="contained"
                fullWidth
                color="primary"
                startIcon={<BookmarkIcon />}
                onClick={handleNewLearningPathClick}
                size={isMobile ? "small" : "medium"}
              >
                Create New Path
              </Button>
            </Stack>
          ) : (
            /* Desktop view - Horizontal button layout */
            <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={handleDownloadJSON}
              >
                Download JSON
              </Button>
              <Button
                variant="outlined"
                color="secondary"
                startIcon={<SaveIcon />}
                onClick={handleSaveToHistory}
                disabled={savedToHistory}
              >
                {savedToHistory ? 'Saved' : 'Save to History'}
              </Button>
              <Button
                variant="contained"
                color="primary"
                startIcon={<BookmarkIcon />}
                onClick={handleNewLearningPathClick}
              >
                Create New Path
              </Button>
            </Stack>
          )}
        </Box>
        
        <Typography 
          variant="h5" 
          sx={{ 
            mb: 3,
            fontSize: { xs: '1.25rem', sm: '1.5rem' },
            wordBreak: 'break-word'
          }}
        >
          {learningPath.topic}
        </Typography>
        
        <Divider sx={{ mb: 4 }} />
        
        {learningPath.modules?.length > 0 ? (
          <Box>
            {learningPath.modules.map((module, moduleIndex) => (
              <Accordion key={moduleIndex} defaultExpanded={moduleIndex === 0} sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography 
                    variant="h6" 
                    sx={{ 
                      fontSize: { xs: '1rem', sm: '1.25rem' },
                      lineHeight: 1.4,
                      pr: { xs: 2, sm: 0 } // Add padding-right on mobile to prevent text overlap with icon
                    }}
                  >
                    Module {moduleIndex + 1}: {module.title}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails sx={{ px: { xs: 2, sm: 3 } }}>
                  <Box sx={{ mb: 3 }}>
                    <Typography 
                      variant="body1" 
                      paragraph 
                      sx={{ 
                        fontSize: { xs: '0.875rem', sm: '1rem' },
                        lineHeight: 1.6 
                      }}
                    >
                      {module.description}
                    </Typography>
                    
                    {module.prerequisites && module.prerequisites.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography 
                          variant="subtitle1" 
                          sx={{ 
                            fontWeight: 'bold',
                            fontSize: { xs: '0.875rem', sm: '1rem' }
                          }}
                        >
                          Prerequisites:
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                          {module.prerequisites.map((prereq, idx) => (
                            <Chip key={idx} label={prereq} size="small" color="primary" variant="outlined" />
                          ))}
                        </Box>
                      </Box>
                    )}
                    
                    {module.submodules && module.submodules.length > 0 ? (
                      <Box sx={{ mt: 3 }}>
                        <Typography 
                          variant="subtitle1" 
                          sx={{ 
                            fontWeight: 'bold', 
                            mb: 2,
                            fontSize: { xs: '0.875rem', sm: '1rem' }
                          }}
                        >
                          Submodules:
                        </Typography>
                        
                        {module.submodules.map((submodule, subIndex) => (
                          <Card key={subIndex} variant="outlined" sx={{ mb: 2 }}>
                            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                              <Typography 
                                variant="h6" 
                                sx={{ 
                                  mb: 1,
                                  fontSize: { xs: '1rem', sm: '1.25rem' } 
                                }}
                              >
                                {submodule.title}
                              </Typography>
                              <Typography 
                                variant="body2" 
                                color="text.secondary" 
                                sx={{ 
                                  mb: 2,
                                  fontSize: { xs: '0.8125rem', sm: '0.875rem' },
                                  lineHeight: 1.5
                                }}
                              >
                                {submodule.description}
                              </Typography>
                              
                              {submodule.content && (
                                <Box sx={{ mt: 2 }}>
                                  <Divider sx={{ mb: 2 }} />
                                  <Box 
                                    sx={{ 
                                      fontSize: { xs: '0.875rem', sm: '1rem' },
                                      '& img': { maxWidth: '100%', height: 'auto' } // Ensure images are responsive
                                    }}
                                  >
                                    <MarkdownRenderer>
                                      {submodule.content}
                                    </MarkdownRenderer>
                                  </Box>
                                </Box>
                              )}
                            </CardContent>
                          </Card>
                        ))}
                      </Box>
                    ) : (
                      module.content && (
                        <Box 
                          sx={{ 
                            mt: 3,
                            fontSize: { xs: '0.875rem', sm: '1rem' },
                            '& img': { maxWidth: '100%', height: 'auto' } // Ensure images are responsive
                          }}
                        >
                          <MarkdownRenderer>
                            {module.content}
                          </MarkdownRenderer>
                        </Box>
                      )
                    )}
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        ) : (
          <Alert severity="warning">
            No modules found in the learning path.
          </Alert>
        )}
      </Paper>
      
      {/* Save to History Dialog */}
      <Dialog 
        open={saveDialogOpen}
        onClose={handleSaveDialogClose}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: { 
            m: { xs: 2, sm: 3 },
            width: { xs: 'calc(100% - 16px)', sm: 'auto' }
          }
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <StorageIcon sx={{ mr: 1 }} />
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
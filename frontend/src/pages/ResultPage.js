import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  IconButton
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
import { getLearningPath, getProgressUpdates, saveToHistory, updateHistoryEntry } from '../services/api';

// Styled chip component for tags
const StyledChip = ({ label, onDelete }) => (
  <Chip
    label={label}
    onDelete={onDelete}
    size="small"
    sx={{ margin: 0.5 }}
  />
);

function ResultPage() {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const [learningPath, setLearningPath] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [progressMessages, setProgressMessages] = useState([]);
  const progressEventSourceRef = useRef(null);
  
  // Save to history dialog state
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [tags, setTags] = useState([]);
  const [newTag, setNewTag] = useState('');
  const [favorite, setFavorite] = useState(false);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });

  useEffect(() => {
    const fetchData = async () => {
      try {
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
      } catch (err) {
        console.error('Error fetching learning path:', err);
        setError('Failed to fetch learning path. Please try again later.');
        setLoading(false);
      }
    };
    
    fetchData();
  }, [taskId]);

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
      <Container maxWidth="md">
        <Paper elevation={3} sx={{ p: 4, borderRadius: 2, mb: 4 }}>
          <Box sx={{ textAlign: 'center', my: 3 }}>
            <CircularProgress color="primary" />
            <Typography variant="h5" sx={{ mt: 2 }}>
              Generating Your Learning Path
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              This may take a few minutes depending on the complexity of the topic.
            </Typography>
            <LinearProgress sx={{ mt: 4, mb: 2 }} />
          </Box>
          
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom>
              Progress Updates:
            </Typography>
            {progressMessages.length === 0 ? (
              <Typography color="text.secondary" sx={{ fontStyle: 'italic' }}>
                Waiting for updates...
              </Typography>
            ) : (
              <Box sx={{ maxHeight: '300px', overflow: 'auto', p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
                {progressMessages.map((msg, index) => (
                  <Typography key={index} sx={{ mb: 1 }}>
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
      <Container maxWidth="md">
        <Paper elevation={3} sx={{ p: 4, borderRadius: 2, mb: 4 }}>
          <Box sx={{ textAlign: 'center', my: 3 }}>
            <ErrorIcon color="error" sx={{ fontSize: 64 }} />
            <Typography variant="h5" color="error" sx={{ mt: 2 }}>
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
              >
                Go to Homepage
              </Button>
              <Button
                variant="contained"
                color="primary"
                onClick={handleNewLearningPathClick}
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
    <Container maxWidth="lg">
      <Paper elevation={3} sx={{ p: 4, borderRadius: 2, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap' }}>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold' }}>
            Learning Path
          </Typography>
          <Stack direction="row" spacing={2}>
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
            >
              Save to History
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
        </Box>
        
        <Typography variant="h5" sx={{ mb: 3 }}>
          {learningPath.topic}
        </Typography>
        
        <Divider sx={{ mb: 4 }} />
        
        {learningPath.modules?.length > 0 ? (
          <Box>
            {learningPath.modules.map((module, moduleIndex) => (
              <Accordion key={moduleIndex} defaultExpanded={moduleIndex === 0} sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">
                    Module {moduleIndex + 1}: {module.title}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="body1" paragraph>
                      {module.description}
                    </Typography>
                    
                    {module.prerequisites && module.prerequisites.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
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
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>
                          Submodules:
                        </Typography>
                        
                        {module.submodules.map((submodule, subIndex) => (
                          <Card key={subIndex} variant="outlined" sx={{ mb: 2 }}>
                            <CardContent>
                              <Typography variant="h6" sx={{ mb: 1 }}>
                                {submodule.title}
                              </Typography>
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                {submodule.description}
                              </Typography>
                              
                              {submodule.content && (
                                <Box sx={{ mt: 2 }}>
                                  <Divider sx={{ mb: 2 }} />
                                  <MarkdownRenderer>
                                    {submodule.content}
                                  </MarkdownRenderer>
                                </Box>
                              )}
                            </CardContent>
                          </Card>
                        ))}
                      </Box>
                    ) : (
                      module.content && (
                        <Box sx={{ mt: 3 }}>
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
      <Dialog open={saveDialogOpen} onClose={handleSaveDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <StorageIcon sx={{ mr: 1 }} />
            Save to Local History
          </Box>
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
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
            label="Mark as favorite"
            sx={{ mb: 2 }}
          />
          
          <Typography variant="subtitle2" gutterBottom>
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
        <DialogActions>
          <Button onClick={handleSaveDialogClose}>
            Cancel
          </Button>
          <Button onClick={handleSaveConfirm} color="primary" variant="contained" startIcon={<SaveIcon />}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleNotificationClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleNotificationClose} severity={notification.severity}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}

export default ResultPage; 
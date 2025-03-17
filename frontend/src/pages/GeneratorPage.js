import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  TextField,
  Button,
  Paper,
  Container,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider,
  Grid,
  Alert,
  CircularProgress,
  Stack,
  FormControlLabel,
  Checkbox,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Snackbar,
  IconButton,
  InputAdornment
} from '@mui/material';
import { styled } from '@mui/material/styles';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import BoltIcon from '@mui/icons-material/Bolt';
import AutorenewIcon from '@mui/icons-material/Autorenew';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import CloseIcon from '@mui/icons-material/Close';
import AddIcon from '@mui/icons-material/Add';

// Import API service
import { generateLearningPath, saveToHistory } from '../services/api';

const StyledChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
}));

function GeneratorPage() {
  const navigate = useNavigate();
  const [topic, setTopic] = useState('');
  const [parallelCount, setParallelCount] = useState(2);
  const [searchParallelCount, setSearchParallelCount] = useState(3);
  const [submoduleParallelCount, setSubmoduleParallelCount] = useState(2);
  const [advancedSettingsOpen, setAdvancedSettingsOpen] = useState(false);
  const [error, setError] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  
  // History states
  const [autoSaveToHistory, setAutoSaveToHistory] = useState(true);
  const [initialTags, setInitialTags] = useState([]);
  const [initialFavorite, setInitialFavorite] = useState(false);
  const [newTag, setNewTag] = useState('');
  
  // Save dialog states
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [saveDialogTags, setSaveDialogTags] = useState([]);
  const [saveDialogFavorite, setSaveDialogFavorite] = useState(false);
  const [saveDialogNewTag, setSaveDialogNewTag] = useState('');
  const [generatedPath, setGeneratedPath] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
  const [taskId, setTaskId] = useState(null);

  // Handle tag addition
  const handleAddTag = () => {
    if (newTag.trim() && !initialTags.includes(newTag.trim())) {
      setInitialTags([...initialTags, newTag.trim()]);
      setNewTag('');
    }
  };

  // Handle tag deletion
  const handleDeleteTag = (tagToDelete) => {
    setInitialTags(initialTags.filter(tag => tag !== tagToDelete));
  };

  // Handle tag keydown (Enter)
  const handleTagKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  // Handle dialog tag addition
  const handleAddDialogTag = () => {
    if (saveDialogNewTag.trim() && !saveDialogTags.includes(saveDialogNewTag.trim())) {
      setSaveDialogTags([...saveDialogTags, saveDialogNewTag.trim()]);
      setSaveDialogNewTag('');
    }
  };

  // Handle dialog tag deletion
  const handleDeleteDialogTag = (tagToDelete) => {
    setSaveDialogTags(saveDialogTags.filter(tag => tag !== tagToDelete));
  };

  // Handle dialog tag keydown (Enter)
  const handleDialogTagKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddDialogTag();
    }
  };

  // Show notification
  const showNotification = (message, severity = 'success') => {
    setNotification({
      open: true,
      message,
      severity,
    });
  };

  // Save to history
  const saveToHistoryHandler = async (learningPath, tags = [], favorite = false) => {
    try {
      await saveToHistory(learningPath, 'generated');
      
      // If tags or favorite are set, update the entry
      if (tags.length > 0 || favorite) {
        // Note: In a real implementation, you would get the entry ID from the saveToHistory response
        // and then update it. For now, we'll just show a success message.
      }
      
      showNotification('Learning path saved to history successfully!', 'success');
      return true;
    } catch (error) {
      console.error('Error saving to history:', error);
      showNotification('Failed to save to history. Please try again.', 'error');
      return false;
    }
  };

  // Handle save dialog confirmation
  const handleSaveConfirm = async () => {
    if (generatedPath) {
      await saveToHistoryHandler(generatedPath, saveDialogTags, saveDialogFavorite);
    }
    setSaveDialogOpen(false);
    
    // Navigate to result page after save attempt (regardless of success/failure)
    if (taskId) {
      navigate(`/result/${taskId}`);
    }
  };

  // Handle save dialog cancellation
  const handleSaveCancel = () => {
    setSaveDialogOpen(false);
    
    // Navigate to result page without saving
    if (taskId) {
      navigate(`/result/${taskId}`);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!topic.trim()) {
      setError('Please enter a topic');
      return;
    }
    
    setError('');
    setIsGenerating(true);
    
    try {
      const response = await generateLearningPath(topic, {
        parallelCount,
        searchParallelCount,
        submoduleParallelCount
      });
      
      setTaskId(response.task_id);
      
      // Fetch the generated learning path (in a production app, we'd fetch the result)
      // For demo purposes, we'll create a mock learning path
      const mockLearningPath = {
        topic: topic,
        modules: [],
        metadata: {
          generatedAt: new Date().toISOString()
        }
      };
      
      setGeneratedPath(mockLearningPath);
      
      // Handle auto-save logic
      if (autoSaveToHistory) {
        const saved = await saveToHistoryHandler(mockLearningPath, initialTags, initialFavorite);
        
        // Proceed to result page
        navigate(`/result/${response.task_id}`);
      } else {
        // Open save dialog if auto-save is disabled
        setSaveDialogTags(initialTags);
        setSaveDialogFavorite(initialFavorite);
        setSaveDialogOpen(true);
      }
    } catch (err) {
      console.error('Error generating learning path:', err);
      setError('Failed to generate learning path. Please try again.');
      setIsGenerating(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
          <Typography
            variant="h4"
            component="h1"
            gutterBottom
            sx={{ fontWeight: 'bold', textAlign: 'center', mb: 3 }}
          >
            Generate Learning Path
          </Typography>
          
          <Typography variant="body1" sx={{ mb: 4, textAlign: 'center' }}>
            Enter any topic you want to learn about and we'll create a personalized learning path for you.
          </Typography>
          
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          <TextField
            label="What do you want to learn about?"
            variant="outlined"
            fullWidth
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Enter a topic (e.g., Machine Learning, Spanish Cooking, Digital Marketing)"
            sx={{ mb: 3 }}
            inputProps={{ maxLength: 100 }}
            required
            disabled={isGenerating}
            autoFocus
          />
          
          <Divider sx={{ my: 3 }} />
          
          <Accordion
            expanded={advancedSettingsOpen}
            onChange={() => setAdvancedSettingsOpen(!advancedSettingsOpen)}
            sx={{ mb: 3 }}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'medium' }}>
                Advanced Settings
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={4}>
                <Grid item xs={12}>
                  <Typography gutterBottom>
                    Parallel Module Processing: {parallelCount}
                  </Typography>
                  <Slider
                    value={parallelCount}
                    min={1}
                    max={4}
                    step={1}
                    marks
                    onChange={(_, value) => setParallelCount(value)}
                    valueLabelDisplay="auto"
                    disabled={isGenerating}
                  />
                  <Typography variant="body2" color="text.secondary">
                    Higher values may generate learning paths faster but could use more resources.
                  </Typography>
                </Grid>
                
                <Grid item xs={12}>
                  <Typography gutterBottom>
                    Search Parallel Count: {searchParallelCount}
                  </Typography>
                  <Slider
                    value={searchParallelCount}
                    min={1}
                    max={5}
                    step={1}
                    marks
                    onChange={(_, value) => setSearchParallelCount(value)}
                    valueLabelDisplay="auto"
                    disabled={isGenerating}
                  />
                  <Typography variant="body2" color="text.secondary">
                    Controls how many searches run in parallel during research phase.
                  </Typography>
                </Grid>
                
                <Grid item xs={12}>
                  <Typography gutterBottom>
                    Submodule Parallel Count: {submoduleParallelCount}
                  </Typography>
                  <Slider
                    value={submoduleParallelCount}
                    min={1}
                    max={4}
                    step={1}
                    marks
                    onChange={(_, value) => setSubmoduleParallelCount(value)}
                    valueLabelDisplay="auto"
                    disabled={isGenerating}
                  />
                  <Typography variant="body2" color="text.secondary">
                    Controls how many submodules are processed in parallel.
                  </Typography>
                </Grid>
                
                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 'medium', mb: 2 }}>
                    History Settings
                  </Typography>
                  
                  <FormControlLabel
                    control={
                      <Checkbox 
                        checked={autoSaveToHistory} 
                        onChange={(e) => setAutoSaveToHistory(e.target.checked)}
                        disabled={isGenerating}
                      />
                    }
                    label="Automatically save to history"
                  />
                  
                  {autoSaveToHistory && (
                    <Box sx={{ mt: 2 }}>
                      <Grid container spacing={2}>
                        <Grid item xs={12}>
                          <FormControlLabel
                            control={
                              <Checkbox 
                                icon={<StarBorderIcon />}
                                checkedIcon={<StarIcon />}
                                checked={initialFavorite} 
                                onChange={(e) => setInitialFavorite(e.target.checked)}
                                disabled={isGenerating}
                              />
                            }
                            label="Mark as favorite"
                          />
                        </Grid>
                        
                        <Grid item xs={12}>
                          <Typography variant="body2" gutterBottom>
                            Tags:
                          </Typography>
                          
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', mb: 1 }}>
                            {initialTags.map((tag) => (
                              <StyledChip
                                key={tag}
                                label={tag}
                                onDelete={() => handleDeleteTag(tag)}
                                size="small"
                                disabled={isGenerating}
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
                              disabled={isGenerating}
                              InputProps={{
                                endAdornment: (
                                  <InputAdornment position="end">
                                    <IconButton 
                                      onClick={handleAddTag} 
                                      disabled={!newTag.trim() || isGenerating}
                                      size="small"
                                    >
                                      <AddIcon />
                                    </IconButton>
                                  </InputAdornment>
                                ),
                              }}
                            />
                          </Box>
                        </Grid>
                      </Grid>
                    </Box>
                  )}
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
          
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              size="large"
              disabled={isGenerating || !topic.trim()}
              startIcon={isGenerating ? <CircularProgress size={20} color="inherit" /> : <BoltIcon />}
              sx={{ py: 1.5, px: 4, borderRadius: 2, fontWeight: 'bold', fontSize: '1.1rem' }}
            >
              {isGenerating ? 'Generating...' : 'Generate Learning Path'}
            </Button>
          </Box>
          
          {isGenerating && (
            <Box sx={{ mt: 4, textAlign: 'center' }}>
              <Stack direction="row" spacing={2} alignItems="center" justifyContent="center">
                <AutorenewIcon sx={{ animation: 'spin 2s linear infinite' }} />
                <Typography>
                  Researching your topic and creating your personalized learning path...
                </Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                This may take a few minutes depending on the complexity of the topic.
              </Typography>
            </Box>
          )}
        </Box>
      </Paper>
      
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Our AI will research your topic and create a comprehensive learning path
          with modules and submodules to help you master the subject efficiently.
        </Typography>
      </Box>
      
      {/* Save Dialog */}
      <Dialog open={saveDialogOpen} onClose={handleSaveCancel}>
        <DialogTitle>Save to History</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Do you want to save this learning path to your history?
          </DialogContentText>
          
          <Box sx={{ mt: 3 }}>
            <FormControlLabel
              control={
                <Checkbox 
                  icon={<StarBorderIcon />}
                  checkedIcon={<StarIcon />}
                  checked={saveDialogFavorite} 
                  onChange={(e) => setSaveDialogFavorite(e.target.checked)}
                />
              }
              label="Mark as favorite"
            />
          </Box>
          
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" gutterBottom>
              Tags:
            </Typography>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', mb: 1 }}>
              {saveDialogTags.map((tag) => (
                <StyledChip
                  key={tag}
                  label={tag}
                  onDelete={() => handleDeleteDialogTag(tag)}
                  size="small"
                />
              ))}
            </Box>
            
            <Box sx={{ display: 'flex' }}>
              <TextField
                size="small"
                value={saveDialogNewTag}
                onChange={(e) => setSaveDialogNewTag(e.target.value)}
                onKeyDown={handleDialogTagKeyDown}
                placeholder="Add tag..."
                variant="outlined"
                fullWidth
                sx={{ mr: 1 }}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton 
                        onClick={handleAddDialogTag} 
                        disabled={!saveDialogNewTag.trim()}
                        size="small"
                      >
                        <AddIcon />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleSaveCancel}>
            Skip & Continue
          </Button>
          <Button onClick={handleSaveConfirm} variant="contained" color="primary">
            Save to History
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setNotification({ ...notification, open: false })}
          severity={notification.severity}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}

export default GeneratorPage; 
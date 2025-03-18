import React, { useState, useEffect } from 'react';
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
  InputAdornment,
  useMediaQuery,
  useTheme
} from '@mui/material';
import { styled } from '@mui/material/styles';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import BoltIcon from '@mui/icons-material/Bolt';
import AutorenewIcon from '@mui/icons-material/Autorenew';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import CloseIcon from '@mui/icons-material/Close';
import AddIcon from '@mui/icons-material/Add';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import KeyIcon from '@mui/icons-material/Key';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import StorageIcon from '@mui/icons-material/Storage';

// Import components
import ApiKeySettings from '../components/organisms/ApiKeySettings';
import AdvancedSettings from '../components/organisms/AdvancedSettings';
import HistorySettings from '../components/organisms/HistorySettings';
import SaveDialog from '../components/molecules/SaveDialog';
import NotificationSystem from '../components/molecules/NotificationSystem';

// Import API service
import { 
  generateLearningPath, 
  saveToHistory,
  validateApiKeys,
  saveApiKeys,
  getSavedApiKeys,
  clearSavedApiKeys
} from '../services/api';

const StyledChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
}));

const ResponsiveContainer = styled(Container)(({ theme }) => ({
  [theme.breakpoints.down('sm')]: {
    padding: theme.spacing(1),
  },
}));

function GeneratorPage() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  const [topic, setTopic] = useState('');
  const [parallelCount, setParallelCount] = useState(2);
  const [searchParallelCount, setSearchParallelCount] = useState(3);
  const [submoduleParallelCount, setSubmoduleParallelCount] = useState(2);
  const [advancedSettingsOpen, setAdvancedSettingsOpen] = useState(false);
  const [apiSettingsOpen, setApiSettingsOpen] = useState(false);
  const [error, setError] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Module and Submodule count states
  const [autoModuleCount, setAutoModuleCount] = useState(true);
  const [desiredModuleCount, setDesiredModuleCount] = useState(5);
  const [autoSubmoduleCount, setAutoSubmoduleCount] = useState(true);
  const [desiredSubmoduleCount, setDesiredSubmoduleCount] = useState(3);
  
  // API Key states
  const [openaiApiKey, setOpenaiApiKey] = useState('');
  const [pplxApiKey, setPplxApiKey] = useState('');
  const [showOpenaiKey, setShowOpenaiKey] = useState(false);
  const [showPplxKey, setShowPplxKey] = useState(false);
  const [rememberApiKeys, setRememberApiKeys] = useState(false);
  const [openaiKeyValid, setOpenaiKeyValid] = useState(null);
  const [pplxKeyValid, setPplxKeyValid] = useState(null);
  const [validatingKeys, setValidatingKeys] = useState(false);
  
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

  // Load saved API keys on component mount
  useEffect(() => {
    const { openaiKey, pplxKey, remember } = getSavedApiKeys();
    if (openaiKey) setOpenaiApiKey(openaiKey);
    if (pplxKey) setPplxApiKey(pplxKey);
    if (remember) setRememberApiKeys(remember);
    
    // Auto-expand API settings section to make it more obvious to users
    setApiSettingsOpen(true);
  }, []);

  // Handle validation of API keys
  const handleValidateApiKeys = async () => {
    if (!openaiApiKey.trim() && !pplxApiKey.trim()) {
      showNotification('Please enter at least one API key to validate', 'warning');
      return;
    }
    
    // Check basic format before sending to backend
    if (openaiApiKey.trim() && !openaiApiKey.trim().startsWith("sk-")) {
      showNotification('Invalid OpenAI API key format. The key should start with "sk-".', 'error');
      setOpenaiKeyValid(false);
      return;
    }
    
    if (pplxApiKey.trim() && !pplxApiKey.trim().startsWith("pplx-")) {
      showNotification('Invalid Perplexity API key format. The key should start with "pplx-".', 'error');
      setPplxKeyValid(false);
      return;
    }
    
    setValidatingKeys(true);
    setOpenaiKeyValid(null);
    setPplxKeyValid(null);
    
    try {
      showNotification('Validating API keys...', 'info');
      console.log("Sending API keys for validation");
      
      const trimmedOpenaiKey = openaiApiKey.trim();
      const trimmedPplxKey = pplxApiKey.trim();
      
      const result = await validateApiKeys(trimmedOpenaiKey, trimmedPplxKey);
      
      // Update validation status
      if (trimmedOpenaiKey) {
        setOpenaiKeyValid(result.openai?.valid || false);
        if (!result.openai?.valid) {
          showNotification(`OpenAI API key invalid: ${result.openai?.error || 'Unknown error'}`, 'error');
        } else {
          showNotification('OpenAI API key validation successful!', 'success');
        }
      }
      
      if (trimmedPplxKey) {
        setPplxKeyValid(result.perplexity?.valid || false);
        if (!result.perplexity?.valid) {
          showNotification(`Perplexity API key invalid: ${result.perplexity?.error || 'Unknown error'}`, 'error');
        } else {
          showNotification('Perplexity API key validation successful!', 'success');
        }
      }
      
      // Show success notification if all provided keys are valid
      const openaiSuccess = trimmedOpenaiKey ? result.openai?.valid : true;
      const pplxSuccess = trimmedPplxKey ? result.perplexity?.valid : true;
      
      if (openaiSuccess && pplxSuccess) {
        if (trimmedOpenaiKey && trimmedPplxKey) {
          showNotification('Both API keys validated successfully!', 'success');
        }
        
        // Save keys if remember is checked
        if (rememberApiKeys) {
          saveApiKeys(trimmedOpenaiKey, trimmedPplxKey, true);
          showNotification('API keys saved for this session', 'info');
        }
      }
    } catch (error) {
      console.error('Error during API key validation:', error);
      showNotification('Network error validating API keys. Please check your internet connection and try again.', 'error');
      setOpenaiKeyValid(false);
      setPplxKeyValid(false);
    } finally {
      setValidatingKeys(false);
    }
  };

  // Clear API keys
  const handleClearApiKeys = () => {
    setOpenaiApiKey('');
    setPplxApiKey('');
    setOpenaiKeyValid(null);
    setPplxKeyValid(null);
    clearSavedApiKeys();
    setRememberApiKeys(false);
    showNotification('API keys cleared', 'success');
  };

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
    // Adjust duration based on message type
    const duration = severity === 'error' ? 10000 : 6000;
    
    // Format error messages for better readability
    let formattedMessage = message;
    if (severity === 'error' && (message.includes('API key') || message.includes('Perplexity'))) {
      formattedMessage = message.replace('. ', '.\n\n');
    }
    
    setNotification({
      open: true,
      message: formattedMessage,
      severity,
      duration
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

    // Check if API keys are provided
    if (!openaiApiKey.trim() || !pplxApiKey.trim()) {
      setError('Both OpenAI and Perplexity API keys are required. Please enter them in the API Key Settings section.');
      setApiSettingsOpen(true); // Open the API settings accordion
      return;
    }
    
    // Validate API keys before proceeding
    if (openaiKeyValid !== true || pplxKeyValid !== true) {
      setError('Please validate your API keys before generating a learning path.');
      setApiSettingsOpen(true);
      showNotification('API keys must be validated before proceeding.', 'warning');
      return;
    }

    // Additional API key format validation
    if (!openaiApiKey.startsWith("sk-")) {
      setError('Invalid OpenAI API key format. The key should start with "sk-".');
      setApiSettingsOpen(true);
      return;
    }

    if (!pplxApiKey.startsWith("pplx-")) {
      setError('Invalid Perplexity API key format. The key should start with "pplx-".');
      setApiSettingsOpen(true);
      return;
    }
    
    // Save API keys if remember option is checked
    if (rememberApiKeys && (openaiApiKey || pplxApiKey)) {
      saveApiKeys(openaiApiKey, pplxApiKey, true);
    }
    
    setError('');
    setIsGenerating(true);
    
    try {
      console.log("Generating learning path with user-provided API keys");
      
      // Prepare the request data, including the new module and submodule count parameters
      const requestData = {
        parallelCount,
        searchParallelCount,
        submoduleParallelCount,
        openaiApiKey: openaiApiKey.trim(),
        pplxApiKey: pplxApiKey.trim()
      };
      
      // Only include module count if automatic mode is disabled
      if (!autoModuleCount) {
        requestData.desiredModuleCount = desiredModuleCount;
      }
      
      // Only include submodule count if automatic mode is disabled
      if (!autoSubmoduleCount) {
        requestData.desiredSubmoduleCount = desiredSubmoduleCount;
      }
      
      const response = await generateLearningPath(topic, requestData);
      
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
      
      // Check if this is an API key validation error
      if (err.response && err.response.status === 400 && err.response.data.detail) {
        if (err.response.data.detail.includes('OpenAI API key') || 
            err.response.data.detail.includes('Perplexity API key')) {
          setError(err.response.data.detail);
          setApiSettingsOpen(true);
          
          // Reset validation status as the keys were rejected by the backend
          if (err.response.data.detail.includes('OpenAI API key')) {
            setOpenaiKeyValid(false);
          }
          if (err.response.data.detail.includes('Perplexity API key')) {
            setPplxKeyValid(false);
          }
        } else {
          setError(err.response.data.detail);
        }
      } else {
        setError('Failed to generate learning path. Please try again.');
      }
      
      setIsGenerating(false);
    }
  };

  // Handle notification close
  const handleNotificationClose = () => {
    setNotification({ ...notification, open: false });
  };

  return (
    <ResponsiveContainer maxWidth="md">
      <Paper elevation={3} sx={{ 
        p: { xs: 2, sm: 3, md: 4 }, 
        borderRadius: 2 
      }}>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
          <Typography
            variant="h4"
            component="h1"
            gutterBottom
            sx={{ 
              fontWeight: 'bold', 
              textAlign: 'center', 
              mb: 3,
              fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' }
            }}
          >
            Generate Learning Path
          </Typography>
          
          <Typography variant="body1" sx={{ 
            mb: 4, 
            textAlign: 'center',
            fontSize: { xs: '0.875rem', sm: '1rem' }
          }}>
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
          
          {/* Advanced Settings */}
          <AdvancedSettings 
            advancedSettingsOpen={advancedSettingsOpen}
            setAdvancedSettingsOpen={setAdvancedSettingsOpen}
            parallelCount={parallelCount}
            setParallelCount={setParallelCount}
            searchParallelCount={searchParallelCount}
            setSearchParallelCount={setSearchParallelCount}
            submoduleParallelCount={submoduleParallelCount}
            setSubmoduleParallelCount={setSubmoduleParallelCount}
            autoModuleCount={autoModuleCount}
            setAutoModuleCount={setAutoModuleCount}
            desiredModuleCount={desiredModuleCount}
            setDesiredModuleCount={setDesiredModuleCount}
            autoSubmoduleCount={autoSubmoduleCount}
            setAutoSubmoduleCount={setAutoSubmoduleCount}
            desiredSubmoduleCount={desiredSubmoduleCount}
            setDesiredSubmoduleCount={setDesiredSubmoduleCount}
            isGenerating={isGenerating}
            isMobile={isMobile}
          />
          
          {/* API Key Settings */}
          <ApiKeySettings 
            apiSettingsOpen={apiSettingsOpen}
            setApiSettingsOpen={setApiSettingsOpen}
            openaiApiKey={openaiApiKey}
            setOpenaiApiKey={setOpenaiApiKey}
            pplxApiKey={pplxApiKey}
            setPplxApiKey={setPplxApiKey}
            showOpenaiKey={showOpenaiKey}
            setShowOpenaiKey={setShowOpenaiKey}
            showPplxKey={showPplxKey}
            setShowPplxKey={setShowPplxKey}
            rememberApiKeys={rememberApiKeys}
            setRememberApiKeys={setRememberApiKeys}
            openaiKeyValid={openaiKeyValid}
            setOpenaiKeyValid={setOpenaiKeyValid}
            pplxKeyValid={pplxKeyValid}
            setPplxKeyValid={setPplxKeyValid}
            validatingKeys={validatingKeys}
            isGenerating={isGenerating}
            handleValidateApiKeys={handleValidateApiKeys}
            handleClearApiKeys={handleClearApiKeys}
            isMobile={isMobile}
          />
          
          {/* History Settings */}
          <HistorySettings 
            autoSaveToHistory={autoSaveToHistory}
            setAutoSaveToHistory={setAutoSaveToHistory}
            initialFavorite={initialFavorite}
            setInitialFavorite={setInitialFavorite}
            initialTags={initialTags}
            setInitialTags={setInitialTags}
            newTag={newTag}
            setNewTag={setNewTag}
            handleAddTag={handleAddTag}
            handleDeleteTag={handleDeleteTag}
            handleTagKeyDown={handleTagKeyDown}
            isGenerating={isGenerating}
            isMobile={isMobile}
          />
          
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            mt: 3,
            flexDirection: { xs: 'column', sm: 'row' },
            gap: { xs: 2, sm: 0 }
          }}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              size={isMobile ? "medium" : "large"}
              disabled={isGenerating || !topic.trim() || !openaiApiKey.trim() || !pplxApiKey.trim() || openaiKeyValid !== true || pplxKeyValid !== true}
              startIcon={isGenerating ? <CircularProgress size={20} color="inherit" /> : <BoltIcon />}
              sx={{ 
                py: { xs: 1, sm: 1.5 }, 
                px: { xs: 2, sm: 4 }, 
                borderRadius: 2, 
                fontWeight: 'bold', 
                fontSize: { xs: '0.9rem', sm: '1.1rem' },
                width: { xs: '100%', sm: 'auto' }
              }}
            >
              {isGenerating ? 'Generating...' : 'Generate Learning Path'}
            </Button>
          </Box>
          
          {(!openaiApiKey.trim() || !pplxApiKey.trim()) && !isGenerating && (
            <Typography color="error" variant="body2" sx={{ 
              mt: 2, 
              textAlign: 'center',
              fontSize: { xs: '0.75rem', sm: '0.875rem' }
            }}>
              Please provide both OpenAI and Perplexity API keys in the API Key Settings section to generate a learning path.
            </Typography>
          )}
          
          {(openaiApiKey.trim() && pplxApiKey.trim() && (openaiKeyValid !== true || pplxKeyValid !== true)) && !isGenerating && (
            <Typography color="error" variant="body2" sx={{ 
              mt: 2, 
              textAlign: 'center',
              fontSize: { xs: '0.75rem', sm: '0.875rem' } 
            }}>
              Please validate your API keys before generating a learning path.
            </Typography>
          )}
          
          {isGenerating && (
            <Box sx={{ mt: 4, textAlign: 'center' }}>
              <Stack 
                direction={isMobile ? "column" : "row"} 
                spacing={isMobile ? 1 : 2} 
                alignItems="center" 
                justifyContent="center"
              >
                <AutorenewIcon sx={{ animation: 'spin 2s linear infinite' }} />
                <Typography>
                  Researching your topic and creating your personalized learning path...
                </Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary" sx={{ 
                mt: 2,
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>
                This may take a few minutes depending on the complexity of the topic.
              </Typography>
            </Box>
          )}
        </Box>
      </Paper>
      
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary" sx={{
          fontSize: { xs: '0.75rem', sm: '0.875rem' },
          px: { xs: 2, sm: 0 }
        }}>
          Our AI will research your topic and create a comprehensive learning path
          with modules and submodules to help you master the subject efficiently.
        </Typography>
      </Box>
      
      {/* Save Dialog */}
      <SaveDialog 
        open={saveDialogOpen}
        onClose={handleSaveCancel}
        onSave={handleSaveConfirm}
        onCancel={handleSaveCancel}
        tags={saveDialogTags}
        setTags={setSaveDialogTags}
        favorite={saveDialogFavorite}
        setFavorite={setSaveDialogFavorite}
        newTag={saveDialogNewTag}
        setNewTag={setSaveDialogNewTag}
        handleAddTag={handleAddDialogTag}
        handleDeleteTag={handleDeleteDialogTag}
        handleTagKeyDown={handleDialogTagKeyDown}
        isMobile={isMobile}
      />
      
      {/* Notification System */}
      <NotificationSystem 
        notification={notification}
        onClose={handleNotificationClose}
      />
    </ResponsiveContainer>
  );
}

export default GeneratorPage; 
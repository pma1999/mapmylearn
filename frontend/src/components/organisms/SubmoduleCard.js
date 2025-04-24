import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Divider,
  useTheme,
  useMediaQuery,
  Fade,
  Badge,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Snackbar,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import CollectionsBookmarkIcon from '@mui/icons-material/CollectionsBookmark';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import GraphicEqIcon from '@mui/icons-material/GraphicEq';
import MarkdownRenderer from '../MarkdownRenderer';
import { motion } from 'framer-motion';
import ResourcesSection from '../shared/ResourcesSection';

// Import quiz components
import { QuizContainer } from '../quiz';

// Import placeholders for future content types
import PlaceholderContent from '../shared/PlaceholderContent';

// Import the new Chat component
import SubmoduleChat from '../chat/SubmoduleChat';

// Import useAuth hook instead of AuthContext
import { useAuth } from '../../services/authContext';

// Import the configured axios instance
import { api, API_URL } from '../../services/api';

// TabPanel component for the tabbed interface
const TabPanel = (props) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ 
          p: index === 3 ? 0 : { xs: 1, sm: 2 } 
        }}>
          {children}
        </Box>
      )}
    </div>
  );
};

// Define supported languages (should match backend)
const supportedLanguages = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Español' },
  { code: 'fr', name: 'Français' },
  { code: 'de', name: 'Deutsch' },
  { code: 'it', name: 'Italiano' },
  { code: 'pt', name: 'Português' },
];
const defaultLanguageCode = 'en';

const SubmoduleCard = ({ submodule, index, moduleIndex, pathId, isTemporaryPath, actualPathData }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const fullScreen = useMediaQuery(theme.breakpoints.down('md'));
  
  // Use the useAuth hook to get user information and credit refresh function
  const { user, fetchUserCredits } = useAuth();
  
  // Check if this submodule has quiz questions
  const hasQuizQuestions = submodule.quiz_questions && submodule.quiz_questions.length > 0;
  
  // --- Helper function to construct absolute URL ---
  const getAbsoluteAudioUrl = (relativeUrl) => {
      if (!relativeUrl) return null;
      if (relativeUrl.startsWith('http')) return relativeUrl; // Already absolute
      if (relativeUrl.startsWith('/static/')) {
          // Find the base API URL (remove /api suffix if present)
          const baseUrl = API_URL.replace(/\/api$/, ''); 
          return `${baseUrl}${relativeUrl}`;
      }
      // If it's not absolute and doesn't start with /static, return as is (might be incorrect)
      console.warn('Could not construct absolute URL for audio:', relativeUrl);
      return relativeUrl; 
  };

  // --- Audio state --- 
  const [audioUrl, setAudioUrl] = useState(() => getAbsoluteAudioUrl(submodule.audio_url)); // Use helper for initial state
  const [isAudioLoading, setIsAudioLoading] = useState(false);
  const [audioError, setAudioError] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  
  // --- Language State --- 
  const getInitialLanguage = () => {
    const pathLang = actualPathData?.language; // Get language from the full path data
    if (pathLang && supportedLanguages.some(l => l.code === pathLang)) {
      return pathLang;
    }
    return defaultLanguageCode; // Fallback to default
  };
  const [selectedLanguage, setSelectedLanguage] = useState(getInitialLanguage);
  
  // Update language if actualPathData changes (e.g., after initial load)
  useEffect(() => {
    setSelectedLanguage(getInitialLanguage());
  }, [actualPathData?.language]); // Dependency on path language

  const handleOpenModal = () => {
    setModalOpen(true);
  };
  
  const handleCloseModal = () => {
    setModalOpen(false);
  };
  
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
    // Reset audio error when switching tabs
    if (newValue !== 4) { 
      setAudioError(null);
    }
  };

  const handleLanguageChange = (event) => {
    setSelectedLanguage(event.target.value);
    // Optionally reset audio URL and error if language changes?
    // setAudioUrl(null);
    // setAudioError(null);
  };

  const handleGenerateAudio = async () => {
    setIsAudioLoading(true);
    setAudioError(null);
    setNotification({ open: false, message: '', severity: 'info' });

    const requestBody = {
      // Send path_data only if it's a temporary path
      path_data: isTemporaryPath ? actualPathData : undefined,
      language: selectedLanguage // Add the selected language code
    };

    try {
      const response = await api.post(
        `/v1/learning-paths/${pathId}/modules/${moduleIndex}/submodules/${index}/audio`,
        requestBody // Send the updated body
      );
      
      if (response.data && response.data.audio_url) {
        // Use helper function to get absolute URL
        const fullUrl = getAbsoluteAudioUrl(response.data.audio_url);
        if (fullUrl) {
             setAudioUrl(fullUrl);
             setNotification({ open: true, message: 'Audio generated successfully!', severity: 'success' });
             // Fetch updated credits after successful generation
             if (fetchUserCredits) { // Check if function exists
               fetchUserCredits(); 
               console.log('Fetched updated credits after audio generation.');
             }
        } else {
            throw new Error("Failed to construct absolute audio URL");
        }
      } else {
        throw new Error("Invalid response from server");
      }
    } catch (err) {
      console.error("Audio generation failed:", err);
      let errorMsg;
      let errorSeverity = 'error'; // Default to error

      if (err.response?.status === 403) {
        // Specific handling for insufficient credits
        errorMsg = err.response?.data?.error?.message || "Insufficient credits to generate audio.";
        // Optionally change severity for credit errors, e.g., 'warning'
        // errorSeverity = 'warning'; 
      } else {
        // Generic error handling
        errorMsg = err.response?.data?.error?.message || err.message || 'Failed to generate audio. Please try again later.';
      }
      
      setAudioError(errorMsg);
      setNotification({ open: true, message: errorMsg, severity: errorSeverity });
    } finally {
      setIsAudioLoading(false);
    }
  };
  
  const handleNotificationClose = (event, reason) => {
    if (reason === 'clickaway') {
      return;
    }
    setNotification({ ...notification, open: false });
  };

  // Animation variants for the card
  const cardVariants = {
    hidden: { opacity: 0, x: -10 },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: { 
        duration: 0.3,
        delay: index * 0.05 
      }
    }
  };

  // Ensure pathId is passed; provide a fallback or handle error if missing
  if (!pathId) {
    console.error("Error: pathId prop is missing in SubmoduleCard");
    // Optionally return null or an error message component
    return null; 
  }

  // Determine number of tabs
  const tabCount = 3 + (hasQuizQuestions ? 1 : 0) + 1; // Content, Resources, Chat + Quiz? + Audio
  let quizTabIndex = hasQuizQuestions ? 1 : -1; 
  let resourcesTabIndex = 1 + (hasQuizQuestions ? 1 : 0);
  let chatTabIndex = resourcesTabIndex + 1;
  let audioTabIndex = chatTabIndex + 1;

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={cardVariants}
    >
      <Card 
        variant="outlined" 
        sx={{ 
          borderRadius: 2,
          transition: 'all 0.3s ease',
          borderWidth: 1,
          borderColor: 'grey.300',
          '&:hover': {
            borderColor: theme.palette.primary.light,
            boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.08)'
          }
        }}
      >
        <CardContent sx={{ p: { xs: 2, sm: 2.5 } }}>
          <Box 
            sx={{ 
              display: 'flex', 
              alignItems: 'flex-start',
              justifyContent: 'space-between'
            }}
          >
            <Box sx={{ flex: 1 }}>
              <Typography 
                variant="h6" 
                sx={{ 
                  fontWeight: 500,
                  fontSize: { xs: '1rem', sm: '1.1rem' },
                  mb: 1,
                  lineHeight: 1.4,
                  color: theme.palette.text.primary,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
                }}
              >
                {submodule.title}
              </Typography>
              
              <Typography 
                variant="body2" 
                color="text.secondary"
                sx={{ 
                  mb: 2,
                  fontSize: { xs: '0.85rem', sm: '0.9rem' },
                  lineHeight: 1.5
                }}
              >
                {submodule.description}
              </Typography>
            </Box>
          </Box>
          
          <Box 
            sx={{ 
              display: 'flex', 
              justifyContent: 'flex-end',
              alignItems: 'center',
              mt: 1
            }}
          >
            <Button
              size="small"
              color="primary"
              variant="outlined"
              startIcon={<MenuBookIcon />}
              onClick={handleOpenModal}
            >
              View Content
            </Button>
          </Box>
        </CardContent>
      </Card>
      
      {/* Enhanced Full Content Modal with Tabs */}
      <Dialog
        open={modalOpen}
        onClose={handleCloseModal}
        fullScreen={fullScreen}
        maxWidth="md"
        fullWidth
        TransitionComponent={Fade}
        transitionDuration={300}
        scroll="paper"
        PaperProps={{
          sx: {
            borderRadius: { xs: 0, sm: 2 },
            maxHeight: '90vh'
          }
        }}
      >
        <DialogTitle
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            px: { xs: 2, sm: 3 },
            py: { xs: 1.5, sm: 2 },
            bgcolor: 'primary.main',
            color: 'white',
          }}
        >
          <Typography variant="h6" component="div" sx={{ flex: 1, pr: 2 }}>
            Module {moduleIndex + 1}.{index + 1}: {submodule.title}
          </Typography>
          <IconButton
            edge="end"
            color="inherit"
            onClick={handleCloseModal}
            aria-label="close"
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        
        <DialogContent 
          dividers 
          sx={{ 
            p: 0, 
            display: 'flex', 
            flexDirection: 'column' 
          }}
        >
          {/* Submodule description */}
          <Box sx={{ px: { xs: 2, sm: 3 }, pt: { xs: 2, sm: 3 } }}>
            <Typography 
              variant="subtitle1" 
              color="text.secondary"
              paragraph
              sx={{ 
                mb: 3, 
                fontStyle: 'italic',
                borderLeft: '4px solid',
                borderColor: 'primary.light',
                pl: 2,
                py: 1,
                bgcolor: 'grey.50',
                borderRadius: '0 4px 4px 0'
              }}
            >
              {submodule.description}
            </Typography>
          </Box>
          
          {/* Tabbed interface */}
          <Box sx={{ width: '100%', flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
            {/* Tabs navigation */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper', position: 'sticky', top: 0, zIndex: 1 }}>
              <Tabs 
                value={activeTab} 
                onChange={handleTabChange} 
                aria-label="submodule content tabs"
                variant={isMobile ? "scrollable" : "fullWidth"}
                scrollButtons={isMobile ? "auto" : false}
                allowScrollButtonsMobile
              >
                <Tab label="Content" icon={<MenuBookIcon />} iconPosition="start" id="tab-0" aria-controls="tabpanel-0" />
                {hasQuizQuestions && (
                  <Tab label="Quiz" icon={<FitnessCenterIcon />} iconPosition="start" id={`tab-${quizTabIndex}`} aria-controls={`tabpanel-${quizTabIndex}`} />
                )}
                <Tab label="Resources" icon={<CollectionsBookmarkIcon />} iconPosition="start" id={`tab-${resourcesTabIndex}`} aria-controls={`tabpanel-${resourcesTabIndex}`} />
                <Tab label="Chat" icon={<QuestionAnswerIcon />} iconPosition="start" id={`tab-${chatTabIndex}`} aria-controls={`tabpanel-${chatTabIndex}`} />
                {/* New Audio Tab */}
                <Tab label="Audio" icon={<GraphicEqIcon />} iconPosition="start" id={`tab-${audioTabIndex}`} aria-controls={`tabpanel-${audioTabIndex}`} />
              </Tabs>
            </Box>
            
            {/* Content tab panel */}
            <TabPanel value={activeTab} index={0}>
              <MarkdownRenderer>
                {submodule.content || "No content available for this submodule."}
              </MarkdownRenderer>
            </TabPanel>
            
            {/* Exercises tab panel - now shows quiz if available */}
            {hasQuizQuestions && (
              <TabPanel value={activeTab} index={quizTabIndex}>
                <QuizContainer 
                  quizQuestions={submodule.quiz_questions}
                  submoduleId={`${moduleIndex}-${index}`}
                  pathId={pathId} 
                  isTemporaryPath={isTemporaryPath}
                />
              </TabPanel>
            )}
            
            {/* Resources tab panel */}
            <TabPanel value={activeTab} index={resourcesTabIndex}>
              <ResourcesSection resources={submodule.resources} title="Submodule Resources" type="submodule" />
            </TabPanel>

            {/* Chatbot tab panel */}
            <TabPanel value={activeTab} index={chatTabIndex}>
              <SubmoduleChat 
                pathId={pathId} 
                moduleIndex={moduleIndex} 
                submoduleIndex={index}
                isTemporaryPath={isTemporaryPath}
                actualPathData={actualPathData} // Pass the full data if needed by chat for temp paths
                submoduleTitle={submodule.title}
              />
            </TabPanel>

            {/* New Audio Tab Panel */}
            <TabPanel value={activeTab} index={audioTabIndex}>
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-start', minHeight: '200px', p: 3, gap: 2 }}>
                
                {/* Language Selector */}
                <FormControl fullWidth sx={{ mb: 2, maxWidth: '300px' }} disabled={isAudioLoading}>
                  <InputLabel id={`language-select-label-${index}`}>Script Language</InputLabel>
                  <Select
                    labelId={`language-select-label-${index}`}
                    id={`language-select-${index}`}
                    value={selectedLanguage}
                    label="Script Language"
                    onChange={handleLanguageChange}
                  >
                    {supportedLanguages.map((lang) => (
                      <MenuItem key={lang.code} value={lang.code}>
                        {lang.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {isAudioLoading && (
                  <CircularProgress sx={{ mb: 2 }} />
                )}
                {audioError && !isAudioLoading && (
                  <Alert severity="error" sx={{ width: '100%', mb: 2 }}>{audioError}</Alert>
                )}
                {audioUrl && !isAudioLoading && (
                  <audio controls src={audioUrl} style={{ width: '100%', maxWidth: '500px' }}>
                    Your browser does not support the audio element.
                  </audio>
                )}
                {!audioUrl && !isAudioLoading && (
                  <Button
                    variant="contained"
                    onClick={handleGenerateAudio}
                    disabled={isAudioLoading}
                    startIcon={<GraphicEqIcon />}
                    sx={{ mt: 1 }} // Add some margin
                  >
                    Generate Audio
                  </Button>
                )}
                {/* Show Generate button even if audio exists, to allow re-generation in different language? */}
                {/* Or maybe change button text to 'Re-generate Audio'? */} 
                {audioUrl && !isAudioLoading && (
                    <Button 
                        variant="outlined" 
                        onClick={handleGenerateAudio} 
                        disabled={isAudioLoading}
                        startIcon={<GraphicEqIcon />}
                        sx={{ mt: 1 }} 
                    >
                        Re-generate in {supportedLanguages.find(l => l.code === selectedLanguage)?.name || selectedLanguage}
                    </Button>
                )}
              </Box>
            </TabPanel>
          </Box>
        </DialogContent>
        
        <DialogActions sx={{ p: { xs: 1, sm: 2 } }}>
          <Button onClick={handleCloseModal}>Close</Button>
        </DialogActions>
      </Dialog>
      
      {/* Snackbar for notifications */}
      <Snackbar 
        open={notification.open} 
        autoHideDuration={6000} 
        onClose={handleNotificationClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleNotificationClose} severity={notification.severity} sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </motion.div>
  );
};

export default SubmoduleCard; 
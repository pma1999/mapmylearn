import React, { useState, useEffect, useCallback, forwardRef } from 'react';
import PropTypes from 'prop-types';
import { 
  Box, 
  Typography, 
  Paper, 
  Tabs, 
  Tab, 
  CircularProgress, 
  Alert, 
  Snackbar, 
  Button, 
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tooltip,
  Zoom,
  useTheme,
  Grid,
  Divider,
  Checkbox,
  FormControlLabel
} from '@mui/material';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import CollectionsBookmarkIcon from '@mui/icons-material/CollectionsBookmark';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import GraphicEqIcon from '@mui/icons-material/GraphicEq';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import SkipNextIcon from '@mui/icons-material/SkipNext'; // For next module

// Shared components
import MarkdownRenderer from '../../MarkdownRenderer';
import ResourcesSection from '../../shared/ResourcesSection';
import SubmoduleChat from '../../chat/SubmoduleChat';
import { QuizContainer } from '../../quiz';

// Hooks & API
import { useAuth } from '../../../services/authContext';
import { api, API_URL } from '../../../services/api';
import { helpTexts } from '../../../constants/helpTexts';

// TabPanel component (can be kept internal or moved to shared utils)
const TabPanel = (props) => {
  const { children, value, index, sx, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`submodule-tabpanel-${index}`}
      aria-labelledby={`submodule-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: { xs: 2, sm: 3 }, ...sx }}>{children}</Box>}
    </div>
  );
};

TabPanel.propTypes = {
  children: PropTypes.node,
  index: PropTypes.number.isRequired,
  value: PropTypes.number.isRequired,
  sx: PropTypes.object,
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
const AUDIO_CREDIT_COST = 1; // Define or import this

// Wrap component definition with forwardRef
const ContentPanel = forwardRef(({ 
  module, 
  moduleIndex, 
  submodule, 
  submoduleIndex, 
  pathId, 
  isTemporaryPath, 
  actualPathData,
  onNavigate, // Callback: (direction: 'prev' | 'next' | 'nextModule') => void
  totalModules,
  totalSubmodulesInModule,
  isMobileLayout, // <-- Accept new prop
  activeTab,      
  setActiveTab,
  sx, // Accept sx prop to allow styling from parent (e.g., height)
  progressMap, // New prop
  onToggleProgress // New prop
}, ref) => { // <-- Accept ref as second argument
  const theme = useTheme();
  const { user, fetchUserCredits } = useAuth();

  // --- Audio state logic extracted from SubmoduleCard ---
  const getAbsoluteAudioUrl = useCallback((relativeUrl) => {
      if (!relativeUrl) return null;
      if (relativeUrl.startsWith('http')) return relativeUrl;
      if (relativeUrl.startsWith('/static/')) {
          const baseUrl = API_URL.replace(/\/api$/, ''); 
          return `${baseUrl}${relativeUrl}`;
      }
      console.warn('Could not construct absolute URL for audio:', relativeUrl);
      return relativeUrl; 
  }, []);

  const [audioUrl, setAudioUrl] = useState(null); 
  const [isAudioLoading, setIsAudioLoading] = useState(false);
  const [audioError, setAudioError] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });

  // --- Language State ---
  const getInitialLanguage = useCallback(() => {
    const pathLang = actualPathData?.language;
    if (pathLang && supportedLanguages.some(l => l.code === pathLang)) {
      return pathLang;
    }
    return defaultLanguageCode;
  }, [actualPathData?.language]);

  const [selectedLanguage, setSelectedLanguage] = useState(getInitialLanguage);

  // Effect to update audioUrl and language when submodule changes
  useEffect(() => {
      setAudioUrl(getAbsoluteAudioUrl(submodule?.audio_url));
      setSelectedLanguage(getInitialLanguage());
      setAudioError(null); // Reset error on submodule change
  }, [submodule, getAbsoluteAudioUrl, getInitialLanguage]);

  // --- Audio Generation Logic ---
  const handleGenerateAudio = async () => {
      if (!submodule || !pathId) return; // Safety check

      setIsAudioLoading(true);
      setAudioError(null);
      setNotification({ open: false, message: '', severity: 'info' });

      const requestBody = {
          path_data: isTemporaryPath ? actualPathData : undefined,
          language: selectedLanguage
      };

      try {
          const response = await api.post(
              `/v1/learning-paths/${pathId}/modules/${moduleIndex}/submodules/${submoduleIndex}/audio`,
              requestBody
          );
          
          if (response.data?.audio_url) {
              const fullUrl = getAbsoluteAudioUrl(response.data.audio_url);
              if (fullUrl) {
                   setAudioUrl(fullUrl);
                   setNotification({ open: true, message: 'Audio generated successfully!', severity: 'success' });
                   if (fetchUserCredits) {
                       fetchUserCredits();
                       console.log('Fetched updated credits after audio generation.');
                   }
                   // Update the submodule data in the main state if possible? Or rely on refresh?
                   // This part is tricky without a direct way to update actualPathData here.
                   // For now, the URL is updated locally. A full refresh might be needed elsewhere
                   // to persist this audio_url if the user navigates away and comes back.
              } else {
                  throw new Error("Failed to construct absolute audio URL");
              }
          } else {
              throw new Error("Invalid response from server");
          }
      } catch (err) {
          console.error("Audio generation failed:", err);
          let errorMsg = err.response?.data?.error?.message || err.message || 'Failed to generate audio.';
          let errorSeverity = err.response?.status === 403 ? 'warning' : 'error'; // Handle insufficient credits specifically
          setAudioError(errorMsg);
          setNotification({ open: true, message: errorMsg, severity: errorSeverity });
      } finally {
          setIsAudioLoading(false);
      }
  };
  
  const handleLanguageChange = (event) => {
    setSelectedLanguage(event.target.value);
    // Reset audio URL when language changes to force re-generation if desired
    // setAudioUrl(null); 
    setAudioError(null); 
  };

  const handleNotificationClose = (event, reason) => {
    if (reason === 'clickaway') return;
    setNotification({ ...notification, open: false });
  };

  // --- Render Logic ---
  if (!submodule) {
    return (
      <Paper 
        ref={ref} // Attach ref here for placeholder case as well
        elevation={2} 
        sx={{ 
          p: 3, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100%', // Use 100% height
          textAlign: 'center',
          overflowY: 'auto', // Ensure placeholder is also scrollable if needed
           ...sx 
        }}
      >
        <Box>
           <MenuBookIcon sx={{ fontSize: 60, color: 'grey.400', mb: 2 }} />
           <Typography variant="h6" color="text.secondary">
              Select a submodule from the left to view its content.
           </Typography>
        </Box>
      </Paper>
    );
  }

  // Determine available tabs
  const hasQuiz = submodule.quiz_questions && submodule.quiz_questions.length > 0;
  const hasResources = submodule.resources && submodule.resources.length > 0;
  
  let tabIndexCounter = 0;
  const tabsConfig = [
      { index: tabIndexCounter++, label: 'Content', icon: <MenuBookIcon />, component: 'Content', tooltip: null },
      ...(hasQuiz ? [{ index: tabIndexCounter++, label: 'Quiz', icon: <FitnessCenterIcon />, component: 'Quiz', tooltip: helpTexts.submoduleTabQuiz }] : []),
      ...(hasResources ? [{ index: tabIndexCounter++, label: 'Resources', icon: <CollectionsBookmarkIcon />, component: 'Resources', tooltip: null }] : []),
      { index: tabIndexCounter++, label: 'Chat', icon: <QuestionAnswerIcon />, component: 'Chat', tooltip: helpTexts.submoduleTabChat },
      { index: tabIndexCounter++, label: 'Audio', icon: <GraphicEqIcon />, component: 'Audio', tooltip: helpTexts.submoduleTabAudio(AUDIO_CREDIT_COST) },
  ];
  
  // Get current completion status for checkbox
  const progressKey = `${moduleIndex}_${submoduleIndex}`;
  const isCompleted = progressMap && progressMap[progressKey] || false;

  const handleCheckboxToggle = () => {
      if (onToggleProgress) {
          onToggleProgress(moduleIndex, submoduleIndex);
      }
  };

  return (
    // Attach ref to the main Paper component
    <Paper 
      ref={ref} 
      variant="outlined"
      sx={{ 
        display: 'flex',
        flexDirection: 'column',
        borderColor: theme.palette.divider, 
        height: '100%', // Ensure Paper takes full height of its container
        overflowY: 'auto', // Make the Paper itself scrollable
        ...sx // Apply parent styles
      }}
    >
      {/* Submodule Header */}
      <Box sx={{ p: { xs: 2, sm: 2.5 }, borderBottom: `1px solid ${theme.palette.divider}`, bgcolor: 'transparent' }}>
          <Typography variant="h6" component="h3" sx={{ fontWeight: theme.typography.fontWeightMedium, mb: 0.5 }}>
              {moduleIndex + 1}.{submoduleIndex + 1}: {submodule.title}
          </Typography>
          {submodule.description && (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  {submodule.description}
              </Typography>
          )}
      </Box>

      {/* MOVED: Navigation Controls - Conditionally hide on mobile */}
      {!isMobileLayout && (
        <Box sx={{ p: 1, borderBottom: `1px solid ${theme.palette.divider}`, bgcolor: 'transparent' }}>
           <Grid container justifyContent="space-between" alignItems="center">
              <Grid item>
                 <Button 
                    size="small"
                    variant="text"
                    startIcon={<NavigateBeforeIcon />} 
                    onClick={() => onNavigate('prev')}
                    disabled={moduleIndex === 0 && submoduleIndex === 0}
                 >
                    Previous
                 </Button>
              </Grid>
              <Grid item>
                   <Typography variant="caption" color="text.secondary">
                      Module {moduleIndex + 1}/{totalModules} | Submodule {submoduleIndex + 1}/{totalSubmodulesInModule}
                   </Typography>
              </Grid>
              <Grid item>
                 <Button 
                    size="small"
                    variant="text"
                    endIcon={<NavigateNextIcon />} 
                    onClick={() => onNavigate('next')}
                    disabled={moduleIndex === totalModules - 1 && submoduleIndex === totalSubmodulesInModule - 1}
                    sx={{ mr: 1 }}
                 >
                    Next
                 </Button>
                 <Button 
                    size="small"
                    variant="outlined"
                    endIcon={<SkipNextIcon />} 
                    onClick={() => onNavigate('nextModule')}
                    disabled={moduleIndex === totalModules - 1} // Disable if last module
                 >
                    Next Module
                 </Button>
              </Grid>
           </Grid>
        </Box>
      )}

      {/* Tabs Navigation - Only show on Desktop */}
      {!isMobileLayout && (
        <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'transparent' }}>
          <Tabs 
            value={activeTab} 
            onChange={(event, newValue) => setActiveTab(newValue)} 
            aria-label="submodule content tabs"
            variant="scrollable"
            scrollButtons="auto"
            allowScrollButtonsMobile
          >
            {tabsConfig.map((tab) => (
              <Tab
                key={tab.index}
                icon={tab.icon}
                iconPosition="start"
                label={
                   <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {tab.label}
                      {tab.tooltip &&
                        <Tooltip title={tab.tooltip} arrow placement="top" TransitionComponent={Zoom} enterDelay={300}>
                           <InfoOutlinedIcon sx={{ ml: 0.5, fontSize: 'small', verticalAlign: 'middle', color: 'text.secondary' }}/>
                        </Tooltip>
                      }
                   </Box>
                }
                id={`submodule-tab-${tab.index}`}
                aria-controls={`submodule-tabpanel-${tab.index}`}
                sx={{ 
                   py: 1.5 
                }}
              />
            ))}
          </Tabs>
        </Box>
      )}

      {/* Tab Content Area */}
      <Box sx={{ flexGrow: 1, overflowY: 'auto' }} > {/* Make content area scrollable */}
         {tabsConfig.map((tab) => {
             const tabContentSx = tab.component === 'Chat' ? { p: 0, height: '100%' } : {}; 
             return (
                <TabPanel key={tab.index} value={activeTab} index={tab.index} sx={tabContentSx}>
                   {tab.component === 'Content' && (
                       <>
                          <MarkdownRenderer>{submodule.content || "No content available."}</MarkdownRenderer>
                          {/* Add Progress Checkbox at the end of content */} 
                          <Divider sx={{ my: 2 }} />
                          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1, mb: 1 }}>
                              <FormControlLabel
                                  control={
                                      <Checkbox 
                                          checked={isCompleted} 
                                          onChange={handleCheckboxToggle}
                                          name="progressCheckbox"
                                          color="primary"
                                          sx={{ 
                                              color: isCompleted ? theme.palette.success.main : theme.palette.action.active,
                                              '&.Mui-checked': {
                                                  color: theme.palette.success.main,
                                              },
                                          }}
                                      />
                                  }
                                  label={isCompleted ? "Mark as Incomplete" : "Mark as Complete"}
                                  sx={{ 
                                      color: isCompleted ? theme.palette.text.secondary : theme.palette.text.primary
                                  }}
                              />
                          </Box>
                       </>
                   )}
                   {tab.component === 'Quiz' && hasQuiz && (
                       <QuizContainer 
                         quizQuestions={submodule.quiz_questions}
                         submoduleId={`${moduleIndex}-${submoduleIndex}`} // Consistent ID
                         pathId={pathId} 
                         isTemporaryPath={isTemporaryPath}
                       />
                   )}
                   {tab.component === 'Resources' && hasResources && (
                       <ResourcesSection 
                           resources={submodule.resources} 
                           title="Submodule Resources" 
                           type="submodule" 
                           collapsible={false}
                       />
                   )}
                   {tab.component === 'Chat' && (
                       <SubmoduleChat 
                           pathId={pathId} 
                           moduleIndex={moduleIndex} 
                           submoduleIndex={submoduleIndex}
                           isTemporaryPath={isTemporaryPath}
                           actualPathData={actualPathData} 
                           submoduleTitle={submodule.title}
                       />
                   )}
                   {tab.component === 'Audio' && (
                       <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, p: 2 }}>
                           <FormControl fullWidth sx={{ maxWidth: '300px' }} disabled={isAudioLoading}>
                               <InputLabel id={`language-select-label-panel`}>Script Language</InputLabel>
                               <Select
                                   labelId={`language-select-label-panel`}
                                   value={selectedLanguage}
                                   label="Script Language"
                                   onChange={handleLanguageChange}
                                   variant="outlined"
                                   size="small"
                               >
                                   {supportedLanguages.map((lang) => (
                                       <MenuItem key={lang.code} value={lang.code}>{lang.name}</MenuItem>
                                   ))}
                               </Select>
                           </FormControl>

                           {isAudioLoading && <CircularProgress sx={{ my: 2 }} />}
                           {audioError && !isAudioLoading && <Alert severity="error" sx={{ width: '100%', mb: 1 }}>{audioError}</Alert>}
                           
                           {audioUrl && !isAudioLoading && (
                               <audio controls src={audioUrl} style={{ width: '100%', maxWidth: '500px' }}>
                                   Your browser does not support the audio element.
                               </audio>
                           )}

                           <Button
                               variant={audioUrl ? "outlined" : "contained"}
                               onClick={handleGenerateAudio}
                               disabled={isAudioLoading || !pathId} // Disable if no pathId
                               startIcon={<GraphicEqIcon />}
                               sx={{ mt: 1 }}
                           >
                               {isAudioLoading ? 'Generating...' : (audioUrl ? `Re-generate in ${supportedLanguages.find(l => l.code === selectedLanguage)?.name || selectedLanguage}` : 'Generate Audio')}
                           </Button>
                       </Box>
                   )}
                </TabPanel>
             );
         })}
      </Box>
      
      {/* Snackbar for notifications (e.g., audio) */}
      <Snackbar 
        open={notification.open} 
        autoHideDuration={6000} 
        onClose={handleNotificationClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleNotificationClose} severity={notification.severity} sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Paper>
  );
}); // <-- Close the forwardRef HOC

ContentPanel.propTypes = {
  module: PropTypes.object, // Can be null if no module selected
  moduleIndex: PropTypes.number, // Index of the active module
  submodule: PropTypes.object, // Can be null if no submodule selected
  submoduleIndex: PropTypes.number, // Index of the active submodule within the module
  pathId: PropTypes.string,
  isTemporaryPath: PropTypes.bool,
  actualPathData: PropTypes.object, // Full path data needed for context (e.g., audio generation)
  onNavigate: PropTypes.func.isRequired, // Navigation callback
  totalModules: PropTypes.number.isRequired,
  totalSubmodulesInModule: PropTypes.number.isRequired,
  isMobileLayout: PropTypes.bool, // Add new propType
  activeTab: PropTypes.number.isRequired,
  setActiveTab: PropTypes.func.isRequired,
  sx: PropTypes.object, // Add sx propType
  progressMap: PropTypes.object, // Added prop type
  onToggleProgress: PropTypes.func, // Added prop type (optional here? Maybe required)
};

// Add display name for DevTools
ContentPanel.displayName = 'ContentPanel';

export default ContentPanel; 
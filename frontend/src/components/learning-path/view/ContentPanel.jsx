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
  FormControlLabel,
  FormHelperText
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
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver'; // Standard
import CampaignIcon from '@mui/icons-material/Campaign'; // Engaging
import MicNoneIcon from '@mui/icons-material/MicNone'; // Calm Narrator
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline'; // Conversational
import PsychologyAltIcon from '@mui/icons-material/PsychologyAlt';

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

// Define audio style configurations
const audioStyleConfig = {
  standard: {
    label: 'Standard Tutor',
    description: 'Clear, encouraging, and informative delivery with a balanced pace.',
    icon: <RecordVoiceOverIcon sx={{ mr: 1.5, verticalAlign: 'middle' }} fontSize="small" />
  },
  engaging: {
    label: 'Engaging & Energetic',
    description: 'A more enthusiastic and dynamic delivery, suitable for motivating learners.',
    icon: <CampaignIcon sx={{ mr: 1.5, verticalAlign: 'middle' }} fontSize="small" />
  },
  calm_narrator: {
    label: 'Calm Narrator',
    description: 'A measured, clear, and calm delivery, like a documentary narrator.',
    icon: <MicNoneIcon sx={{ mr: 1.5, verticalAlign: 'middle' }} fontSize="small" />
  },
  conversational: {
    label: 'Friendly & Conversational',
    description: 'A relaxed, informal, and friendly style, as if explaining to a friend.',
    icon: <ChatBubbleOutlineIcon sx={{ mr: 1.5, verticalAlign: 'middle' }} fontSize="small" />
  },
  grumpy_genius: {
    label: 'Grumpy Genius Mode',
    description: 'Accurate explanations delivered with comedic reluctance and intellectual sighs.',
    icon: <PsychologyAltIcon sx={{ mr: 1.5, verticalAlign: 'middle' }} fontSize="small" />
  },
};

// Wrap component definition with forwardRef
const ContentPanel = forwardRef(({ 
  displayType, // New prop: 'submodule' or 'module_resources'
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
  onToggleProgress, // New prop
  isPublicView = false // Add prop with default
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

  // Audio Style State
  const [selectedAudioStyle, setSelectedAudioStyle] = useState('standard');

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
    if (displayType === 'submodule' && submodule) {
      setAudioUrl(getAbsoluteAudioUrl(submodule?.audio_url));
      setSelectedLanguage(getInitialLanguage());
      setAudioError(null); // Reset error on submodule change
    } else {
      // Reset audio related state if not viewing a submodule or submodule is null
      setAudioUrl(null);
      setAudioError(null);
    }
  }, [submodule, displayType, getAbsoluteAudioUrl, getInitialLanguage]);

  // --- Audio Generation Logic ---
  const handleGenerateAudio = async () => {
      // --- Disable for public view ---
      if (isPublicView) {
          setNotification({ open: true, message: 'Audio generation is disabled for public views.', severity: 'info' });
          return;
      }
      if (displayType !== 'submodule' || !submodule || !pathId || !selectedLanguage || !selectedAudioStyle) {
          console.error('Missing required data for audio generation:', { displayType, submodule, pathId, selectedLanguage, selectedAudioStyle });
          setNotification({ open: true, message: 'Cannot generate audio. Missing required submodule data.', severity: 'error' });
          return;
      }

      setIsAudioLoading(true);
      setAudioError(null);
      setNotification({ open: false, message: '', severity: 'info' });

      const isRegeneration = !!audioUrl; // Check if we are regenerating

      const requestBody = {
          path_data: isTemporaryPath ? actualPathData : undefined,
          language: selectedLanguage,
          audio_style: selectedAudioStyle, // Include selected audio style
          force_regenerate: isRegeneration // Add the flag
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

  const handleAudioStyleChange = (event) => {
    setSelectedAudioStyle(event.target.value);
    setAudioError(null); // Reset error if style changes
  };

  const handleNotificationClose = (event, reason) => {
    if (reason === 'clickaway') return;
    setNotification({ ...notification, open: false });
  };

  // --- Conditional Rendering based on displayType ---

  // Case 1: Displaying Module Resources
  if (displayType === 'module_resources' && module && module.resources && module.resources.length > 0) {
    return (
      <Paper 
        ref={ref} 
        variant="outlined"
        data-tut="content-panel" // Keep for general tutorial reference if needed
        sx={{ 
          display: 'flex',
          flexDirection: 'column',
          borderColor: theme.palette.divider, 
          height: '100%',
          overflowY: 'auto',
          ...sx 
        }}
      >
        <Box sx={{ p: { xs: 2, sm: 2.5 }, borderBottom: `1px solid ${theme.palette.divider}`, bgcolor: 'transparent' }}>
            <Typography variant="h6" component="h3" sx={{ fontWeight: theme.typography.fontWeightMedium }}>
                Module Resources: {module.title} (Module {moduleIndex + 1})
            </Typography>
            {module.description && (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', mt: 0.5 }}>
                  {module.description}
              </Typography>
            )}
        </Box>
        <Box sx={{ flexGrow: 1, overflowY: 'auto', p: { xs: 2, sm: 3 } }}>
            <ResourcesSection 
                resources={module.resources} 
                title={`Resources for "${module.title}"`} // More specific title
                type="module" 
                collapsible={false} 
                compact={false} // Or true based on desired density
            />
        </Box>
         {/* No tabs, no submodule navigation, no progress checkbox for module resources */}
      </Paper>
    );
  }

  // Case 2: No submodule selected OR (module resources selected but module has no resources)
  // displayType might be 'submodule' but submodule is null, or 'module_resources' but module.resources is empty
  if (!submodule && displayType === 'submodule') { // Specifically show placeholder when expecting submodule but none is selected
    return (
      <Paper 
        ref={ref} 
        elevation={2} 
        sx={{ 
          p: 3, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100%', 
          textAlign: 'center',
          overflowY: 'auto', 
           ...sx 
        }}
      >
        <Box>
           <MenuBookIcon sx={{ fontSize: 60, color: 'grey.400', mb: 2 }} />
           <Typography variant="h6" color="text.secondary">
              Select a submodule from the left to view its content.
           </Typography>
           {displayType === 'module_resources' && module && (!module.resources || module.resources.length === 0) && (
             <Typography variant="body1" color="text.secondary" sx={{mt: 1}}>
                This module has no additional resources.
             </Typography>
           )}
        </Box>
      </Paper>
    );
  }

  // Case 3: Displaying Submodule Content (default and main case)
  // This implies displayType === 'submodule' AND submodule is valid.
  if (displayType === 'submodule' && submodule) {
    const hasQuiz = submodule.quiz_questions && submodule.quiz_questions.length > 0;
    const hasResources = submodule.resources && submodule.resources.length > 0;
    
    let tabIndexCounter = 0;
    const tabsConfig = [
        { index: tabIndexCounter++, label: 'Content', icon: <MenuBookIcon />, component: 'Content', tooltip: null, dataTut: 'content-panel-tab-content' },
        ...(hasQuiz ? [{ index: tabIndexCounter++, label: 'Quiz', icon: <FitnessCenterIcon />, component: 'Quiz', tooltip: helpTexts.submoduleTabQuiz, dataTut: 'content-panel-tab-quiz' }] : []),
        ...(hasResources ? [{ index: tabIndexCounter++, label: 'Resources', icon: <CollectionsBookmarkIcon />, component: 'Resources', tooltip: null, dataTut: 'content-panel-tab-resources' }] : []),
        { index: tabIndexCounter++, label: 'Chat', icon: <QuestionAnswerIcon />, component: 'Chat', tooltip: helpTexts.submoduleTabChat, dataTut: 'content-panel-tab-chat' },
        { index: tabIndexCounter++, label: 'Audio', icon: <GraphicEqIcon />, component: 'Audio', tooltip: helpTexts.submoduleTabAudio(AUDIO_CREDIT_COST), dataTut: 'content-panel-tab-audio' },
    ];
    
    const progressKey = `${moduleIndex}_${submoduleIndex}`;
    const isCompleted = progressMap && progressMap[progressKey] || false;

    const handleCheckboxToggle = () => {
        if (onToggleProgress && !isPublicView) {
            onToggleProgress(moduleIndex, submoduleIndex);
        }
    };

    return (
      <Paper 
        ref={ref} 
        variant="outlined"
        data-tut="content-panel"
        sx={{ 
          display: 'flex',
          flexDirection: 'column',
          borderColor: theme.palette.divider, 
          height: '100%', 
          overflowY: 'auto', 
          ...sx 
        }}
      >
        {/* Submodule Header - Stays for submodule view */}
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

        {/* Navigation Controls - Only for submodule view on Desktop */}
        {!isMobileLayout && (
          <Box sx={{ p: 1, borderBottom: `1px solid ${theme.palette.divider}`, bgcolor: 'transparent' }}>
             <Grid container justifyContent="space-between" alignItems="center">
                <Grid item data-tut="content-panel-prev-button">
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
                <Grid item data-tut="content-panel-next-button">
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
                      data-tut="content-panel-next-module-button"
                      size="small"
                      variant="outlined"
                      endIcon={<SkipNextIcon />} 
                      onClick={() => onNavigate('nextModule')}
                      disabled={moduleIndex === totalModules - 1} 
                   >
                      Next Module
                   </Button>
                </Grid>
             </Grid>
          </Box>
        )}

        {/* Tabs Navigation - Only for submodule view on Desktop */}
        {!isMobileLayout && (
          <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'transparent' }} data-tut="content-panel-tabs">
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
                  data-tut={tab.dataTut} // Add data-tut here
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
                  sx={{ py: 1.5 }}
                />
              ))}
            </Tabs>
          </Box>
        )}

        {/* Tab Content Area - Only for submodule view */}
        <Box sx={{ flexGrow: 1, overflowY: 'auto' }} >
           {tabsConfig.map((tab) => {
               const tabContentSx = tab.component === 'Chat' ? { p: 0, height: '100%' } : {}; 
               return (
                  <TabPanel key={tab.index} value={activeTab} index={tab.index} sx={tabContentSx} >
                     {tab.component === 'Content' && (
                         <Box data-tut="content-panel-tab-content">
                             <MarkdownRenderer>{submodule.content || "No content available."}</MarkdownRenderer>
                             <Divider sx={{ my: 2 }} />
                             <Box 
                               sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }} 
                               data-tut="content-panel-progress-checkbox-container"
                             >
                               <Tooltip title={isPublicView ? "Progress tracking disabled for public view" : (isCompleted ? "Mark as Incomplete" : "Mark as Complete")}>
                                 <span> 
                                   <FormControlLabel
                                     control={
                                       <Checkbox
                                         checked={isCompleted}
                                         onChange={handleCheckboxToggle}
                                         disabled={isPublicView} 
                                         inputProps={{ 'aria-label': isCompleted ? 'Mark as incomplete' : 'Mark as complete' }}
                                         size="small"
                                       />
                                     }
                                     label={<Typography variant="body2" sx={{ fontSize: '0.8rem' }}>Complete</Typography>}
                                     sx={{ ml: 0 }}
                                     data-tut={`progress-checkbox-${moduleIndex}-${submoduleIndex}`}
                                   />
                                 </span>
                               </Tooltip>
                             </Box>
                         </Box>
                     )}
                     {tab.component === 'Quiz' && hasQuiz && (
                         <QuizContainer 
                           data-tut="content-panel-tab-quiz"
                           quizQuestions={submodule.quiz_questions}
                           submoduleId={`${moduleIndex}-${submoduleIndex}`}
                           pathId={pathId} 
                           isTemporaryPath={isTemporaryPath}
                           disabled={isPublicView} 
                         />
                     )}
                     {tab.component === 'Resources' && hasResources && (
                         <ResourcesSection 
                             data-tut="content-panel-tab-resources"
                             resources={submodule.resources} 
                             title="Submodule Resources" 
                             type="submodule" 
                             collapsible={false}
                         />
                     )}
                     {tab.component === 'Chat' && (
                         <SubmoduleChat 
                             data-tut="content-panel-tab-chat"
                             pathId={pathId} 
                             moduleIndex={moduleIndex} 
                             submoduleIndex={submoduleIndex}
                             isTemporaryPath={isTemporaryPath}
                             actualPathData={actualPathData} 
                             submoduleTitle={submodule.title}
                             disabled={isPublicView} 
                         />
                     )}
                     {tab.component === 'Audio' && (
                         <Box data-tut="content-panel-tab-audio" sx={{ display: 'flex', flexDirection: 'column', alignItems: 'stretch', gap: 2.5, p: { xs: 2, sm: 3 } }}>
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
                                 <FormHelperText>Language used for the audio script and voice.</FormHelperText>
                             </FormControl>

                             <FormControl fullWidth sx={{ maxWidth: '300px' }} disabled={isAudioLoading}>
                                 <InputLabel id="audio-style-select-label">Audio Style</InputLabel>
                                 <Select
                                     labelId="audio-style-select-label"
                                     value={selectedAudioStyle}
                                     label="Audio Style"
                                     onChange={handleAudioStyleChange}
                                     variant="outlined"
                                     size="small"
                                     sx={{ '.MuiSelect-select': { display: 'flex', alignItems: 'center' } }} 
                                 >
                                     {Object.entries(audioStyleConfig).map(([styleKey, config]) => (
                                         <MenuItem key={styleKey} value={styleKey}>
                                             {config.icon} {config.label}
                                         </MenuItem>
                                     ))}
                                     { !audioStyleConfig.grumpy_genius && (
                                         <MenuItem key="grumpy_genius" value="grumpy_genius">
                                             <PsychologyAltIcon sx={{ mr: 1.5, verticalAlign: 'middle' }} fontSize="small" /> Grumpy Genius Mode
                                         </MenuItem>
                                     ) }
                                 </Select>
                                 <FormHelperText>{audioStyleConfig[selectedAudioStyle]?.description || 'Select an audio delivery style.'}</FormHelperText>
                             </FormControl>

                             {isAudioLoading && <CircularProgress sx={{ my: 2, alignSelf: 'center' }} />}
                             {audioError && !isAudioLoading && <Alert severity="error" sx={{ width: '100%', mb: 1 }}>{audioError}</Alert>}
                             
                             {audioUrl && !isAudioLoading && (
                                 <audio controls src={audioUrl} style={{ width: '100%', maxWidth: '500px' }}>
                                     Your browser does not support the audio element.
                                 </audio>
                             )}

                             <Button
                                 variant={audioUrl ? "outlined" : "contained"}
                                 onClick={handleGenerateAudio}
                                 disabled={isAudioLoading || !pathId || isPublicView} 
                                 startIcon={<GraphicEqIcon />}
                                 sx={{ mt: 1 }}
                             >
                                 {isAudioLoading ? 'Generating...' : 
                                   (audioUrl ? 
                                     `Re-generate in ${supportedLanguages.find(l => l.code === selectedLanguage)?.name || selectedLanguage} (${AUDIO_CREDIT_COST} ${AUDIO_CREDIT_COST === 1 ? 'credit' : 'credits'})` : 
                                     `Generate Audio (${AUDIO_CREDIT_COST} ${AUDIO_CREDIT_COST === 1 ? 'credit' : 'credits'})`
                                   )
                                 }
                             </Button>
                         </Box>
                     )}
                  </TabPanel>
               );
           })}
        </Box>
        
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
  }

  // Fallback: If displayType is not recognized or data is inconsistent
  // This should ideally not be reached if LearningPathView logic is correct.
  return (
      <Paper ref={ref} elevation={2} sx={{ p:3, display:'flex', alignItems:'center', justifyContent:'center', height:'100%', ...sx }}>
          <Typography>Loading content or an unexpected view state has occurred.</Typography>
      </Paper>
  );
}); // <-- Close the forwardRef HOC

ContentPanel.propTypes = {
  displayType: PropTypes.string.isRequired, // Added prop type
  module: PropTypes.object, 
  moduleIndex: PropTypes.number, 
  submodule: PropTypes.object, 
  submoduleIndex: PropTypes.number, 
  pathId: PropTypes.string,
  isTemporaryPath: PropTypes.bool,
  actualPathData: PropTypes.object, 
  onNavigate: PropTypes.func.isRequired, 
  totalModules: PropTypes.number.isRequired,
  totalSubmodulesInModule: PropTypes.number.isRequired,
  isMobileLayout: PropTypes.bool, 
  activeTab: PropTypes.number.isRequired,
  setActiveTab: PropTypes.func.isRequired,
  sx: PropTypes.object, 
  progressMap: PropTypes.object, 
  onToggleProgress: PropTypes.func, 
  isPublicView: PropTypes.bool, 
};

// Add display name for DevTools
ContentPanel.displayName = 'ContentPanel';

export default ContentPanel; 
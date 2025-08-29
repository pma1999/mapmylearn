import React, { useState, useEffect, useCallback, forwardRef, useRef } from 'react';
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
  FormHelperText,
  Drawer,
  IconButton
} from '@mui/material';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import CollectionsBookmarkIcon from '@mui/icons-material/CollectionsBookmark';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import GraphicEqIcon from '@mui/icons-material/GraphicEq';
import VisibilityIcon from '@mui/icons-material/Visibility'; // For visualization tab
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import SkipNextIcon from '@mui/icons-material/SkipNext'; // For next module
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver'; // Standard
import CampaignIcon from '@mui/icons-material/Campaign'; // Engaging
import MicNoneIcon from '@mui/icons-material/MicNone'; // Calm Narrator
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline'; // Conversational
import PsychologyAltIcon from '@mui/icons-material/PsychologyAlt';
import CloseIcon from '@mui/icons-material/Close';

// Shared components
import MarkdownRenderer from '../../MarkdownRenderer';
import ResourcesSection from '../../shared/ResourcesSection';
import SubmoduleChat from '../../chat/SubmoduleChat';
import { QuizContainer } from '../../quiz';

// TOC components
import useMarkdownTOC from '../hooks/useMarkdownTOC';
import SubmoduleTableOfContents from '../components/SubmoduleTableOfContents';
import TOCFloatingButton from '../components/TOCFloatingButton';
import useInViewport from '../hooks/useInViewport';

// Visualization component for interactive diagrams
import MermaidVisualization from '../../visualization/MermaidVisualization';

// Hooks & API
import { useAuth } from '../../../services/authContext';
import { api, API_URL } from '../../../services/api';
import { generateSubmoduleVisualization } from '../../../services/api';
import { helpTexts } from '../../../constants/helpTexts';

// TabPanel component
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

const supportedLanguages = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Español' },
  { code: 'fr', name: 'Français' },
  { code: 'de', name: 'Deutsch' },
  { code: 'it', name: 'Italiano' },
  { code: 'pt', name: 'Português' },
  { code: 'ca', name: 'Català' },
];
const defaultLanguageCode = 'en';
const AUDIO_CREDIT_COST = 1;
const VISUALIZATION_CREDIT_COST = 1;

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

const ContentPanel = forwardRef(({ 
  displayType, 
  module, 
  moduleIndex, 
  submodule, 
  submoduleIndex, 
  pathId, 
  isTemporaryPath, 
  actualPathData,
  onNavigate, 
  totalModules,
  totalSubmodulesInModule,
  isMobileLayout, 
  activeTab,      
  setActiveTab,
  sx, 
  progressMap, 
  onToggleProgress, 
  isPublicView = false
}, ref) => {
  const theme = useTheme();
  const { fetchUserCredits, user } = useAuth();

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
  const [selectedAudioStyle, setSelectedAudioStyle] = useState('standard');

  // Visualization state
  const [isVisualizationLoading, setIsVisualizationLoading] = useState(false);
  const [visualizationError, setVisualizationError] = useState(null);
  const [mermaidSyntax, setMermaidSyntax] = useState(null);
  const [visualizationMessage, setVisualizationMessage] = useState(null);

  // TOC state
  const [tocCollapsed, setTocCollapsed] = useState(false);
  const [tocDrawerOpen, setTocDrawerOpen] = useState(false);

  const getInitialLanguage = useCallback(() => {
    const pathLang = actualPathData?.language;
    if (pathLang && supportedLanguages.some(l => l.code === pathLang)) {
      return pathLang;
    }
    return defaultLanguageCode;
  }, [actualPathData?.language]);

  const [selectedLanguage, setSelectedLanguage] = useState(getInitialLanguage);
  const [selectedVizLanguage, setSelectedVizLanguage] = useState(getInitialLanguage);

  // Initialize TOC hook for current submodule content
  const tocHook = useMarkdownTOC(
    displayType === 'submodule' && submodule ? submodule.content : '',
    {
      enableActiveDetection: true,
      scrollOffset: 100,
      debounceDelay: 150
    }
  );

  // Refs for viewport detection of desktop TOC and scroll container
  const contentScrollContainerRef = useRef(null);
  const desktopTocRef = useRef(null);

  // Helper: find nearest scrollable ancestor (vertical)
  const getScrollParent = (node) => {
    if (!node) return null;
    let el = node.parentElement;
    while (el) {
      const style = window.getComputedStyle(el);
      const overflowY = style.overflowY;
      const canScrollY = (overflowY === 'auto' || overflowY === 'scroll');
      if (canScrollY && el.scrollHeight > el.clientHeight) {
        return el;
      }
      el = el.parentElement;
    }
    return null;
  };

  // Determine actual scroll root (Paper vs inner Box) for accurate IntersectionObserver root
  const [scrollRoot, setScrollRoot] = useState(null);
  useEffect(() => {
    // Prefer the desktop TOC's ancestor for precise context; fall back to content scroll Box if it scrolls
    const target = desktopTocRef.current ?? contentScrollContainerRef.current;
    const rootEl = target ? getScrollParent(target) : null;

    let fallbackRoot = null;
    if (contentScrollContainerRef.current && (contentScrollContainerRef.current.scrollHeight > contentScrollContainerRef.current.clientHeight)) {
      fallbackRoot = contentScrollContainerRef.current;
    }

    setScrollRoot(rootEl || fallbackRoot || null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [desktopTocRef, contentScrollContainerRef]);

  // Determine if desktop TOC sidebar is visible within the REAL scroll container
  const isDesktopTocInView = useInViewport(desktopTocRef, {
    root: scrollRoot ?? null,
    // Negative bottom margin makes the "visible" zone slightly smaller to avoid flicker at edges
    rootMargin: '0px 0px -40% 0px',
    threshold: 0
  });

  useEffect(() => {
    if (displayType === 'submodule' && submodule) {
      setAudioUrl(getAbsoluteAudioUrl(submodule?.audio_url));
      setSelectedLanguage(getInitialLanguage());
      setSelectedVizLanguage(getInitialLanguage());
      setAudioError(null);
      // Clear visualization state
      setMermaidSyntax(null);
      setVisualizationError(null);
      setVisualizationMessage(null);
      setIsVisualizationLoading(false);
    } else {
      setAudioUrl(null);
      setAudioError(null);
      // Clear visualization state
      setMermaidSyntax(null);
      setVisualizationError(null);
      setVisualizationMessage(null);
      setIsVisualizationLoading(false);
      setSelectedVizLanguage(getInitialLanguage());
    }
  }, [submodule, displayType, getAbsoluteAudioUrl, getInitialLanguage]);

  const handleGenerateAudio = async () => {
      if (isPublicView) {
          setNotification({ open: true, message: 'Audio generation is disabled for public views.', severity: 'info' });
          return;
      }
      if (displayType !== 'submodule' || !submodule || !pathId || !selectedLanguage || !selectedAudioStyle) {
          console.error('Missing required data for audio generation:', { displayType, submodule, pathId, selectedLanguage, selectedAudioStyle });
          setNotification({ open: true, message: 'Cannot generate audio. Missing required submodule data.', severity: 'error' });
          return;
      }

      // Ensure any open dropdowns are closed and focus is properly managed
      // This prevents accessibility violations with aria-hidden elements retaining focus
      if (document.activeElement && document.activeElement.blur) {
          document.activeElement.blur();
      }

      // Small delay to ensure blur completes before state changes
      await new Promise(resolve => setTimeout(resolve, 50));

      setIsAudioLoading(true);
      setAudioError(null);
      setNotification({ open: false, message: '', severity: 'info' });

      const isRegeneration = !!audioUrl;
      const requestBody = {
          path_data: isTemporaryPath ? actualPathData : undefined,
          language: selectedLanguage,
          audio_style: selectedAudioStyle, 
          force_regenerate: isRegeneration 
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
              } else {
                  throw new Error("Failed to construct absolute audio URL");
              }
          } else {
              throw new Error("Invalid response from server");
          }
      } catch (err) {
          console.error("Audio generation failed:", err);
          let errorMsg = err.response?.data?.error?.message || err.message || 'Failed to generate audio.';
          let errorSeverity = err.response?.status === 403 ? 'warning' : 'error'; 
          setAudioError(errorMsg);
          setNotification({ open: true, message: errorMsg, severity: errorSeverity });
      } finally {
          setIsAudioLoading(false);
      }
  };
  
  const handleLanguageChange = (event) => {
    setSelectedLanguage(event.target.value);
    setAudioError(null);
  };

  const handleVizLanguageChange = (event) => {
    setSelectedVizLanguage(event.target.value);
    setVisualizationError(null);
  };

  const handleAudioStyleChange = (event) => {
    setSelectedAudioStyle(event.target.value);
    setAudioError(null); 
  };

  // Visualization generation function
  const handleGenerateVisualization = async () => {
    if (!submodule || isVisualizationLoading || isPublicView) return;

    // Check credits
    if (user?.credits < VISUALIZATION_CREDIT_COST) {
      setNotification({ open: true, message: 'Insufficient credits for visualization generation', severity: 'error' });
      return;
    }

    // Ensure any open dropdowns are closed and focus is properly managed
    // This prevents accessibility violations with aria-hidden elements retaining focus
    if (document.activeElement && document.activeElement.blur) {
      document.activeElement.blur();
    }

    // Small delay to ensure blur completes before state changes
    await new Promise(resolve => setTimeout(resolve, 50));

    setIsVisualizationLoading(true);
    setVisualizationError(null);
    setVisualizationMessage(null);
    setMermaidSyntax(null);

    try {
      console.log('Generating visualization for submodule:', submodule.title);

      // Determine request data based on path type (temporary vs persisted)
      const requestData = isTemporaryPath && actualPathData ? { path_data: actualPathData, language: selectedVizLanguage } : { language: selectedVizLanguage };

      const response = await generateSubmoduleVisualization(
        pathId,
        moduleIndex,
        submoduleIndex,
        requestData
      );

      if (response.mermaid_syntax) {
        setMermaidSyntax(response.mermaid_syntax);
        setNotification({ open: true, message: 'Visualization generated successfully!', severity: 'success' });
        console.log('Visualization generated:', response.mermaid_syntax);
        if (fetchUserCredits) {
          fetchUserCredits();
          console.log('Fetched updated credits after visualization generation.');
        }
      } else if (response.message) {
        setVisualizationMessage(response.message);
        setNotification({ open: true, message: response.message, severity: 'info' });
      } else {
        setVisualizationError('Failed to generate visualization');
        setNotification({ open: true, message: 'Failed to generate visualization', severity: 'error' });
      }

    } catch (error) {
      console.error('Error generating visualization:', error);
      let errorMsg = error.response?.data?.error?.message || error.message || 'Failed to generate visualization.';
      let errorSeverity = error.response?.status === 403 ? 'warning' : 'error';
      setVisualizationError(errorMsg);
      setNotification({ open: true, message: 'Failed to generate visualization: ' + errorMsg, severity: errorSeverity });
    } finally {
      setIsVisualizationLoading(false);
    }
  };

  const handleNotificationClose = (event, reason) => {
    if (reason === 'clickaway') return;
    setNotification({ ...notification, open: false });
  };

  // TOC handlers
  const handleTocHeaderClick = useCallback((headerId) => {
    tocHook.scrollToHeader(headerId);
    // Close mobile drawer after navigation
    if (isMobileLayout) {
      setTocDrawerOpen(false);
    }
  }, [tocHook, isMobileLayout]);

  const handleTocToggleCollapse = useCallback(() => {
    setTocCollapsed(prev => !prev);
  }, []);

  const handleTocDrawerOpen = useCallback(() => {
    setTocDrawerOpen(true);
  }, []);

  const handleTocDrawerClose = useCallback(() => {
    setTocDrawerOpen(false);
  }, []);

  if (displayType === 'module_resources' && module && module.resources && module.resources.length > 0) {
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
        <Box sx={{ p: { xs: 2, sm: 2.5 }, borderBottom: `1px solid ${theme.palette.divider}`, bgcolor: 'transparent', flexShrink: 0 }}>
            <Typography variant="h6" component="h3" sx={{ fontWeight: theme.typography.fontWeightMedium }}>
                Module Resources: {module.title} (Module {moduleIndex + 1})
            </Typography>
            {module.description && (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', mt: 0.5 }}>
                  {module.description}
              </Typography>
            )}
        </Box>
        {/* Content area for module resources - allow natural height, Paper handles scroll */}
        <Box sx={{ overflowY: 'auto', p: { xs: 2, sm: 3 } }}> 
            <ResourcesSection 
                resources={module.resources} 
                title={`Resources for "${module.title}"`} 
                type="module" 
                collapsible={false} 
                compact={false} 
            />
        </Box>
      </Paper>
    );
  }

  if (!submodule && displayType === 'submodule') { 
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
        </Box>
      </Paper>
    );
  }

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
        { index: tabIndexCounter++, label: 'Visualization', icon: <VisibilityIcon />, component: 'Visualization', tooltip: helpTexts.submoduleTabVisualization(VISUALIZATION_CREDIT_COST), dataTut: 'content-panel-tab-visualization' },
    ];
    
    const progressKey = `${moduleIndex}_${submoduleIndex}`;
    const isCompleted = (progressMap && progressMap[progressKey]) || false;

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
        <Box sx={{ p: { xs: 2, sm: 2.5 }, borderBottom: `1px solid ${theme.palette.divider}`, bgcolor: 'transparent', flexShrink: 0 }}>
            <Typography variant="h6" component="h3" sx={{ fontWeight: theme.typography.fontWeightMedium, mb: 0.5 }}>
                {moduleIndex + 1}.{submoduleIndex + 1}: {submodule.title}
            </Typography>
            {submodule.description && (
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    {submodule.description}
                </Typography>
            )}
        </Box>

        {!isMobileLayout && (
          <Box sx={{ p: 1, borderBottom: `1px solid ${theme.palette.divider}`, bgcolor: 'transparent', flexShrink: 0 }}>
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

        {!isMobileLayout && (
          <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'transparent', flexShrink: 0 }} data-tut="content-panel-tabs">
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
                  data-tut={tab.dataTut} 
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

        <Box sx={{ flexGrow: 1, overflowY: 'auto' }} ref={contentScrollContainerRef} >
           {tabsConfig.map((tab) => {
               const tabContentSx = tab.component === 'Chat' ? { p: 0, height: '100%' } : {}; 
               return (
                  <TabPanel key={tab.index} value={activeTab} index={tab.index} sx={tabContentSx} >
                     {tab.component === 'Content' && (
                         <Box data-tut="content-panel-tab-content">
                             {/* TOC and Content Layout */}
                             <Box sx={{ 
                               display: 'flex', 
                               gap: 2, 
                               flexDirection: isMobileLayout ? 'column' : 'row',
                               height: '100%'
                             }}>
                               {/* Main Content Area */}
                               <Box sx={{ 
                                 flex: 1,
                                 minWidth: 0,
                                 position: 'relative'
                               }}>
                                 <MarkdownRenderer 
                                   enableTocIds={true}
                                   headerIdMap={tocHook.headerIdMap}
                                 >
                                   {submodule.content || "No content available."}
                                 </MarkdownRenderer>
                                 
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

                               {/* Desktop TOC Sidebar */}
                               {!isMobileLayout && tocHook.hasHeaders && (
                                 <Box ref={desktopTocRef} sx={{ 
                                   width: tocCollapsed ? '80px' : '280px',
                                   flexShrink: 0,
                                   transition: 'width 0.3s ease-in-out',
                                   position: 'sticky',
                                   top: theme.spacing(2),
                                   alignSelf: 'flex-start',
                                   maxHeight: 'calc(100vh - 200px)',
                                   overflow: 'hidden',
                                   minWidth: { xs: '60px', sm: '80px' }
                                 }}>
                                   <SubmoduleTableOfContents
                                     headers={tocHook.headers}
                                     activeHeaderId={tocHook.activeHeaderId}
                                     onHeaderClick={handleTocHeaderClick}
                                     isMobile={false}
                                     isCollapsed={tocCollapsed}
                                     onToggleCollapse={handleTocToggleCollapse}
                                     title="Content Outline"
                                     maxHeight="100%"
                                   />
                                 </Box>
                               )}
                             </Box>

                             {/* Mobile TOC Floating Button */}
                             {isMobileLayout && tocHook.hasHeaders && (
                               <TOCFloatingButton
                                 onOpen={handleTocDrawerOpen}
                                 hasHeaders={tocHook.hasHeaders}
                                 headerCount={tocHook.headers.length}
                                 isVisible={true}
                                 position="bottom-right"
                               />
                             )}
                             {/* Desktop TOC Floating Button (appears when sidebar TOC is not visible) */}
                             {!isMobileLayout && tocHook.hasHeaders && !isDesktopTocInView && (
                               <TOCFloatingButton
                                 onOpen={handleTocDrawerOpen}
                                 hasHeaders={tocHook.hasHeaders}
                                 headerCount={tocHook.headers.length}
                                 isVisible={true}
                                 variant="secondary"
                                 size="small"
                                 position="top-right"
                               />
                             )}
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
                    {tab.component === 'Visualization' && (
                        <Box data-tut="content-panel-tab-visualization" sx={{ display: 'flex', flexDirection: 'column', alignItems: 'stretch', gap: 2.5, p: { xs: 2, sm: 3 } }}>
                            <FormControl fullWidth sx={{ maxWidth: '300px' }} disabled={isVisualizationLoading}>
                                <InputLabel id={`viz-language-select-label`}>Diagram Language</InputLabel>
                                <Select
                                    labelId={`viz-language-select-label`}
                                    value={selectedVizLanguage}
                                    label="Diagram Language"
                                    onChange={handleVizLanguageChange}
                                    variant="outlined"
                                    size="small"
                                >
                                    {supportedLanguages.map((lang) => (
                                        <MenuItem key={lang.code} value={lang.code}>{lang.name}</MenuItem>
                                    ))}
                                </Select>
                                <FormHelperText>Language used for visualization labels.</FormHelperText>
                            </FormControl>
                            {isVisualizationLoading && <CircularProgress sx={{ my: 2, alignSelf: 'center' }} />}
                             {visualizationError && !isVisualizationLoading && <Alert severity="error" sx={{ width: '100%', mb: 1 }}>{visualizationError}</Alert>}
                             {visualizationMessage && !isVisualizationLoading && <Alert severity="info" sx={{ width: '100%', mb: 1 }}>{visualizationMessage}</Alert>}
                             
                             {mermaidSyntax && !isVisualizationLoading && (
                                 <MermaidVisualization 
                                     mermaidSyntax={mermaidSyntax}
                                     title="Interactive Visualization"
                                     sx={{ mb: 2 }}
                                 />
                             )}

                             <Button
                                 variant={mermaidSyntax ? "outlined" : "contained"}
                                 onClick={handleGenerateVisualization}
                                 disabled={isVisualizationLoading || !pathId || isPublicView} 
                                 startIcon={<VisibilityIcon />}
                                 sx={{ mt: 1 }}
                             >
                                 {isVisualizationLoading ? 'Generating...' : 
                                   (mermaidSyntax ? 
                                     `Re-generate Visualization (${VISUALIZATION_CREDIT_COST} ${VISUALIZATION_CREDIT_COST === 1 ? 'credit' : 'credits'})` : 
                                     `Generate Visualization (${VISUALIZATION_CREDIT_COST} ${VISUALIZATION_CREDIT_COST === 1 ? 'credit' : 'credits'})`
                                   )
                                 }
                             </Button>
                         </Box>
                     )}
                  </TabPanel>
               );
           })}
        </Box>

        {/* TOC Drawer (mobile and desktop) */}
        {tocHook.hasHeaders && (
          <Drawer
            anchor="right"
            open={tocDrawerOpen}
            onClose={handleTocDrawerClose}
            ModalProps={{ keepMounted: true }}
            PaperProps={{
              sx: {
                width: isMobileLayout ? '85%' : 360,
                maxWidth: isMobileLayout ? '400px' : 'unset',
                borderTopLeftRadius: theme.spacing(2),
                borderBottomLeftRadius: theme.spacing(2)
              }
            }}
          >
            <Box sx={{
              p: 2,
              borderBottom: `1px solid ${theme.palette.divider}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <Typography variant="h6" sx={{ fontWeight: theme.typography.fontWeightMedium }}>
                Content Outline
              </Typography>
              <IconButton onClick={handleTocDrawerClose} size="small">
                <CloseIcon />
              </IconButton>
            </Box>
            <Box sx={{ overflow: 'auto', flex: 1 }}>
              <SubmoduleTableOfContents
                headers={tocHook.headers}
                activeHeaderId={tocHook.activeHeaderId}
                onHeaderClick={(id) => { handleTocHeaderClick(id); handleTocDrawerClose(); }}
                isMobile={isMobileLayout}
                title=""
              />
            </Box>
          </Drawer>
        )}
        
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

  return (
      <Paper ref={ref} elevation={2} sx={{ p:3, display:'flex', alignItems:'center', justifyContent:'center', height:'100%', ...sx }}>
          <Typography>Loading content or an unexpected view state has occurred.</Typography>
      </Paper>
  );
}); 

ContentPanel.propTypes = {
  displayType: PropTypes.string.isRequired, 
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

ContentPanel.displayName = 'ContentPanel';

export default ContentPanel;

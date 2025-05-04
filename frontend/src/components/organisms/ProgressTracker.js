import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, 
  Typography, 
  LinearProgress, 
  Stack, 
  Paper, 
  Fade, 
  Grow,
  Slide,
  Chip,
  Divider,
  Card,
  CardContent,
  useTheme,
  useMediaQuery,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  alpha
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import SearchIcon from '@mui/icons-material/Search';
import PublicIcon from '@mui/icons-material/Public';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import ExtensionIcon from '@mui/icons-material/Extension';
import CreateIcon from '@mui/icons-material/Create';
import DoneIcon from '@mui/icons-material/Done';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import AutoAwesomeMotionIcon from '@mui/icons-material/AutoAwesomeMotion';
import TerminalIcon from '@mui/icons-material/Terminal';

// Define phase information with icons, descriptions and expected durations (for weighted progress)
const PHASES = {
  initialization: {
    icon: <TerminalIcon />,
    title: 'Initializing',
    description: 'Setting up the course pipeline',
    weight: 0.05,
    color: '#607D8B', // blue grey
    typicalDuration: 10 // seconds
  },
  search_queries: {
    icon: <SearchIcon />,
    title: 'Search Query Generation',
    description: 'Analyzing your topic to generate optimal search queries',
    weight: 0.10,
    color: '#5C6BC0', // indigo
    typicalDuration: 20 // seconds
  },
  web_searches: {
    icon: <PublicIcon />,
    title: 'Web Research',
    description: 'Searching the web for high-quality learning materials',
    weight: 0.10,
    color: '#26A69A', // teal
    typicalDuration: 40 // seconds
  },
  modules: {
    icon: <MenuBookIcon />,
    title: 'Module Creation',
    description: 'Organizing research into a logical course structure',
    weight: 0.10,
    color: '#66BB6A', // green
    typicalDuration: 45 // seconds
  },
  submodule_planning: {
    icon: <ExtensionIcon />,
    title: 'Submodule Planning',
    description: 'Breaking down modules into detailed learning components',
    weight: 0.10,
    color: '#FFA726', // orange
    typicalDuration: 45 // seconds
  },
  submodule_research: {
    icon: <SearchIcon />,
    title: 'Targeted Research',
    description: 'Researching specific content for each submodule',
    weight: 0.15,
    color: '#42A5F5', // blue
    typicalDuration: 60 // seconds
  },
  content_development: {
    icon: <CreateIcon />,
    title: 'Content Development',
    description: 'Creating comprehensive content for each learning component',
    weight: 0.30,
    color: '#EF5350', // red
    typicalDuration: 90 // seconds
  },
  final_assembly: {
    icon: <AutoAwesomeMotionIcon />,
    title: 'Final Assembly',
    description: 'Assembling all components into your complete course',
    weight: 0.10,
    color: '#8E24AA', // purple
    typicalDuration: 20 // seconds
  },
  completion: {
    icon: <AutoAwesomeIcon />,
    title: 'Completed',
    description: 'Your course is ready',
    weight: 0,
    color: '#2E7D32', // dark green
    typicalDuration: 0 // seconds
  },
  unknown: {
    icon: <AutoAwesomeIcon />,
    title: 'Processing',
    description: 'Creating your course',
    weight: 1,
    color: '#757575', // grey
    typicalDuration: 300 // seconds
  }
};

// Helper function to format time remaining
function formatTimeRemaining(seconds) {
  if (seconds < 60) return `${Math.round(seconds)}s remaining`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes}m ${remainingSeconds}s remaining`;
}

// Calculate the typical total duration based on phase weights and their typical durations
const calculateTypicalTotalDuration = () => {
  return Object.values(PHASES).reduce((total, phase) => total + phase.typicalDuration, 0);
};

const ProgressTracker = ({ progressMessages, estimatedTotalTime = 300 }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isMedium = useMediaQuery(theme.breakpoints.down('md'));
  
  // Get the topic from session storage
  const storedTopic = sessionStorage.getItem('currentTopic') || 'your topic';
  
  // State for current phase and progress
  const [currentPhase, setCurrentPhase] = useState('initialization');
  const [phaseProgress, setPhaseProgress] = useState(0);
  const [overallProgress, setOverallProgress] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(estimatedTotalTime);
  const [startTime] = useState(Date.now());
  const [previewData, setPreviewData] = useState(null);
  const [completedPhases, setCompletedPhases] = useState([]);
  const [activePhases, setActivePhases] = useState(['initialization']);
  
  // Advanced time estimation refs and state
  const phasesStartTimeRef = useRef({});
  const phasesDurationRef = useRef({});
  const lastEstimateRef = useRef(estimatedTotalTime);
  const estimateHistoryRef = useRef([]);
  const smoothingFactorRef = useRef(0.3);
  const [phaseTimingData, setPhaseTimingData] = useState({});
  
  // Process progress updates
  useEffect(() => {
    if (!progressMessages || progressMessages.length === 0) return;
    
    // Get the latest message
    const latestMessage = progressMessages[progressMessages.length - 1];
    
    if (!latestMessage) return;
    
    // Extract structured data if available
    const phase = latestMessage.phase || 'unknown';
    const phaseProgress = latestMessage.phase_progress !== undefined ? latestMessage.phase_progress : null;
    const overall = latestMessage.overall_progress !== undefined ? latestMessage.overall_progress : null;
    const preview = latestMessage.preview_data || null;
    const action = latestMessage.action || 'processing';
    
    // Update preview data if available
    if (preview) {
      setPreviewData(preview);
    }
    
    // Track phase start times and transitions
    if (phase && phase !== currentPhase) {
      // Record the start time of this new phase
      const now = Date.now();
      phasesStartTimeRef.current[phase] = now;
      
      // If we're transitioning from a previous phase, record its duration
      if (currentPhase && phasesStartTimeRef.current[currentPhase]) {
        const phaseDuration = (now - phasesStartTimeRef.current[currentPhase]) / 1000;
        phasesDurationRef.current[currentPhase] = phaseDuration;
        
        setPhaseTimingData(prev => ({
          ...prev,
          [currentPhase]: phaseDuration
        }));
        
        // console.log(`Phase ${currentPhase} completed in ${phaseDuration}s`);
      }
      
      // Add previous phase to completed phases if not already there
      if (currentPhase && !completedPhases.includes(currentPhase)) {
        setCompletedPhases(prev => [...prev, currentPhase]);
      }
      
      setCurrentPhase(phase);
      
      // Update active phases
      if (!activePhases.includes(phase)) {
        setActivePhases(prev => [...prev, phase]);
      }
    }
    
    // Update progress values if provided
    if (phaseProgress !== null) {
      setPhaseProgress(phaseProgress);
    }
    
    if (overall !== null) {
      setOverallProgress(overall);
      
      // Advanced time remaining calculation that combines multiple approaches
      calculateTimeRemaining(overall, phase, phaseProgress);
    }
    
    // Handle completion of a phase
    if (action === 'completed' && phase) {
      if (!completedPhases.includes(phase)) {
        setCompletedPhases(prev => [...prev, phase]);
      }
    }
  }, [progressMessages, currentPhase, completedPhases, activePhases, startTime]);
  
  const calculateTimeRemaining = (overallProgress, currentPhase, phaseProgress) => {
    const elapsedMs = Date.now() - startTime;
    const elapsedSeconds = elapsedMs / 1000;
    
    // Get typical durations and phase weights
    const phaseInfo = PHASES[currentPhase] || PHASES.unknown;
    // Add a safeguard to check if a phase exists in the PHASES object
    const completedPhasesWeight = completedPhases.reduce((sum, phase) => 
      sum + (PHASES[phase]?.weight || 0), 0);
    
    // Calculate remaining time using multiple approaches and then apply smoothing

    // Approach 1: Simple linear projection (the original method)
    const linearEstimate = (elapsedSeconds / Math.max(0.01, overallProgress)) - elapsedSeconds;
    
    // Approach 2: Phase-weighted estimation
    let phaseWeightedEstimate;
    if (phaseInfo && phaseProgress !== null) {
      // Calculate how much progress we've made within current phase
      const currentPhaseContribution = phaseInfo.weight * phaseProgress;
      
      // Calculate effective progress considering phase weights
      const effectiveProgress = completedPhasesWeight + currentPhaseContribution;
      const remainingProgressWeighted = 1 - effectiveProgress;
      
      // Use a combination of observed timings and typical durations
      let remainingTime = 0;
      
      // For the current phase:
      if (phaseProgress > 0) {
        const phaseTimeElapsed = (elapsedSeconds - (phasesDurationRef.current[currentPhase] || 0));
        const phaseEstimatedTotal = phaseTimeElapsed / phaseProgress;
        const phaseTimeRemaining = phaseEstimatedTotal - phaseTimeElapsed;
        remainingTime += Math.max(0, phaseTimeRemaining);
      } else {
        remainingTime += phaseInfo.typicalDuration;
      }
      
      // For upcoming phases - use a mix of observed phase durations and typical durations
      const upcomingPhases = Object.keys(PHASES).filter(p => 
        !completedPhases.includes(p) && p !== currentPhase && p !== 'unknown' && p !== 'completion'
      );
      
      upcomingPhases.forEach(phase => {
        // Ensure we're accessing a valid phase
        if (PHASES[phase]) {
          // If we have observed timing data for this phase from previous similar generations,
          // we could use that here
          remainingTime += PHASES[phase].typicalDuration;
        }
      });
      
      phaseWeightedEstimate = remainingTime;
    } else {
      // Fallback if we don't have phase info
      phaseWeightedEstimate = linearEstimate;
    }
    
    // Approach 3: Adaptive estimation based on observed progress rate
    const adaptiveEstimate = elapsedSeconds * (1 - overallProgress) / overallProgress;
    
    // Combine the estimates, with different weights at different stages
    let combinedEstimate;
    
    // Handle early estimate differently to avoid unrealistic values
    if (overallProgress < 0.05) {
      // Very early in the process, use mainly the typical durations
      const typicalTotal = calculateTypicalTotalDuration();
      combinedEstimate = typicalTotal * 0.9; // Small discount to typical time
    } else if (overallProgress < 0.2) {
      // Early phase - weight more towards phase-based and typical durations
      combinedEstimate = (phaseWeightedEstimate * 0.7) + (adaptiveEstimate * 0.3);
    } else {
      // Later phases - weight more towards observed progress
      combinedEstimate = (phaseWeightedEstimate * 0.4) + (adaptiveEstimate * 0.6);
    }
    
    // Apply guardrails to prevent extreme estimates
    const minEstimate = 5; // Minimum 5 seconds
    const maxEstimate = estimatedTotalTime * 3; // Maximum 3x the initial estimate
    combinedEstimate = Math.max(minEstimate, Math.min(maxEstimate, combinedEstimate));
    
    // Apply exponential smoothing to avoid jumpy estimates
    // Adjust smoothing factor based on progress - more smoothing early, less smoothing later
    const adaptiveSmoothingFactor = 0.2 + (overallProgress * 0.5);
    const lastEstimate = lastEstimateRef.current;
    
    let smoothedEstimate;
    if (lastEstimate) {
      smoothedEstimate = (adaptiveSmoothingFactor * combinedEstimate) + 
                           ((1 - adaptiveSmoothingFactor) * lastEstimate);
    } else {
      smoothedEstimate = combinedEstimate;
    }
    
    // Special case for almost complete
    if (overallProgress > 0.95) {
      smoothedEstimate = Math.min(smoothedEstimate, 30); // Cap at 30 seconds when almost done
    }
    
    // Special case for early phases to prevent wild fluctuations
    if (elapsedSeconds < 10 && estimateHistoryRef.current.length < 3) {
      // For the very first few estimates, use a more conservative approach
      smoothedEstimate = estimatedTotalTime * (1 - overallProgress);
    }
    
    // Update refs for next calculation
    lastEstimateRef.current = smoothedEstimate;
    
    // Keep history of estimates for potential future use
    estimateHistoryRef.current.push({
      time: Date.now(),
      estimate: smoothedEstimate,
      progress: overallProgress,
      phase: currentPhase
    });
    
    // Cap the history length to avoid memory issues
    if (estimateHistoryRef.current.length > 20) {
      estimateHistoryRef.current.shift();
    }
    
    // Round to nearest second and set the state
    setTimeRemaining(Math.max(0, Math.round(smoothedEstimate)));
  };
  
  // Determine the ordered list of phases that should be shown
  const renderPhases = Object.keys(PHASES).filter(phase => 
    activePhases.includes(phase) || completedPhases.includes(phase)
  );
  
  // Helper function to render preview data
  const renderPreview = () => {
    if (!previewData) return null;
    
    return (
      <Fade in={!!previewData} timeout={800}>
        <Box sx={{ mt: 3, mb: 2 }}>
          <AnimatePresence>
            {currentPhase === 'search_queries' && previewData.search_queries && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
              >
                <PreviewSearchQueries queries={previewData.search_queries} />
              </motion.div>
            )}
            
            {currentPhase === 'modules' && previewData.modules && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
              >
                <PreviewModules modules={previewData.modules} />
              </motion.div>
            )}
            
            {currentPhase === 'submodule_planning' && previewData.modules && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
              >
                <PreviewModules modules={previewData.modules} showSubmodules />
              </motion.div>
            )}
            
            {currentPhase === 'content_development' && previewData.processed_submodules && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
              >
                <PreviewContent submodules={previewData.processed_submodules} />
              </motion.div>
            )}
            
            {currentPhase === 'final_assembly' && previewData.modules && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
              >
                <PreviewPath 
                  modules={previewData.modules}
                  totalModules={previewData.total_modules}
                  totalSubmodules={previewData.total_submodules}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </Box>
      </Fade>
    );
  };
  
  return (
    <Stack spacing={3} sx={{ width: '100%', mb: 4 }}>
      {/* Overall progress */}
      <Box sx={{ mb: isMobile ? 2 : 4 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
          <Typography variant={isMobile ? "h6" : "h5"} fontWeight="500" color="primary">
            {overallProgress >= 0.99 
              ? 'Learning Path Complete!' 
              : `Generating Learning Path: ${storedTopic}`}
          </Typography>
          <Chip
            label={timeRemaining > 0 ? formatTimeRemaining(timeRemaining) : "Almost done..."}
            size={isMobile ? "small" : "medium"}
            color="primary"
            variant="outlined"
            sx={{ fontWeight: 500 }}
          />
        </Stack>
        
        <Paper 
          elevation={0} 
          sx={{ 
            p: 1, 
            borderRadius: 2, 
            bgcolor: alpha(theme.palette.primary.main, 0.08),
            position: 'relative',
            overflow: 'hidden'
          }}
        >
          <LinearProgress 
            variant="determinate" 
            value={overallProgress * 100}
            sx={{ 
              height: 10, 
              borderRadius: 5,
              bgcolor: alpha(theme.palette.primary.main, 0.1),
              '& .MuiLinearProgress-bar': {
                borderRadius: 5,
                background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
              }
            }}
          />
          
          {/* Progress markers */}
          {renderPhases.map(phase => {
            const phaseInfo = PHASES[phase];
            // Calculate cumulative weight up to this phase
            const prevPhases = Object.keys(PHASES).slice(0, Object.keys(PHASES).indexOf(phase));
            const cumulativeWeight = prevPhases.reduce((sum, p) => sum + PHASES[p].weight, 0);
            
            return (
              <Box 
                key={phase}
                sx={{
                  position: 'absolute',
                  left: `${cumulativeWeight * 100}%`,
                  top: 0,
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transform: 'translateX(-50%)',
                  opacity: completedPhases.includes(phase) ? 1 : 0.5,
                  transition: 'opacity 0.3s ease'
                }}
              >
                <Box 
                  sx={{ 
                    width: 8, 
                    height: 8, 
                    borderRadius: '50%', 
                    bgcolor: completedPhases.includes(phase) ? phaseInfo.color : 'grey.400',
                    border: `2px solid ${theme.palette.background.paper}`,
                    zIndex: 2
                  }} 
                />
              </Box>
            );
          })}
        </Paper>
      </Box>
      
      {/* Current phase */}
      <Grow in={!!currentPhase} timeout={800}>
        <Paper elevation={2} sx={{ p: { xs: 2, md: 3 }, borderRadius: 2 }}>
          <Stack 
            direction={isMobile ? "column" : "row"} 
            spacing={2} 
            alignItems={isMobile ? "flex-start" : "center"}
          >
            <Box 
              sx={{ 
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                bgcolor: PHASES[currentPhase]?.color || 'primary.main',
                color: 'white',
                borderRadius: '50%',
                p: 1.5,
                width: { xs: 40, md: 56 },
                height: { xs: 40, md: 56 },
                fontSize: { xs: '1.5rem', md: '2rem' }
              }}
            >
              {PHASES[currentPhase]?.icon || <AutoAwesomeIcon />}
            </Box>
            
            <Box sx={{ flexGrow: 1 }}>
              <Typography 
                variant={isMobile ? "subtitle1" : "h6"} 
                fontWeight="bold" 
                sx={{ mb: 0.5 }}
              >
                {PHASES[currentPhase]?.title || 'Processing'}
              </Typography>
              
              <Typography 
                variant="body2" 
                color="text.secondary" 
                sx={{ mb: 1.5 }}
              >
                {PHASES[currentPhase]?.description || 'Creating your course...'}
              </Typography>
              
              <LinearProgress 
                variant="determinate" 
                value={phaseProgress * 100}
                sx={{ 
                  height: 6, 
                  borderRadius: 3,
                  bgcolor: alpha(PHASES[currentPhase]?.color || theme.palette.primary.main, 0.1),
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 3,
                    bgcolor: PHASES[currentPhase]?.color || theme.palette.primary.main
                  }
                }}
              />
              
              {/* Latest message */}
              {progressMessages && progressMessages.length > 0 && (
                <Typography 
                  variant="caption" 
                  display="block"
                  sx={{ mt: 1, color: 'text.secondary', fontStyle: 'italic' }}
                >
                  {progressMessages[progressMessages.length - 1].message}
                </Typography>
              )}
            </Box>
          </Stack>
        </Paper>
      </Grow>
      
      {/* Render dynamic preview content based on current phase */}
      {renderPreview()}
      
      {/* Phase timeline */}
      <Fade in={true} timeout={1000}>
        <Paper elevation={1} sx={{ p: 2, borderRadius: 2, bgcolor: alpha(theme.palette.background.paper, 0.7) }}>
          <Stack spacing={0.5}>
            {renderPhases.map(phase => (
              <PhaseTimelineItem 
                key={phase}
                phase={phase} 
                phaseInfo={PHASES[phase]}
                isActive={phase === currentPhase}
                isCompleted={completedPhases.includes(phase)}
                isMobile={isMobile}
              />
            ))}
          </Stack>
        </Paper>
      </Fade>
    </Stack>
  );
};

// Component for displaying phase in timeline
const PhaseTimelineItem = ({ phase, phaseInfo, isActive, isCompleted, isMobile }) => {
  const theme = useTheme();
  
  return (
    <Box
      sx={{
        display: 'flex',
        py: 1,
        borderLeft: isActive || isCompleted ? `3px solid ${phaseInfo.color}` : '3px solid transparent',
        pl: 2,
        transition: 'all 0.3s ease',
        opacity: isActive || isCompleted ? 1 : 0.6,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: isCompleted 
            ? phaseInfo.color
            : isActive 
              ? alpha(phaseInfo.color, 0.2) 
              : alpha(theme.palette.action.disabledBackground, 0.5),
          color: isCompleted 
            ? 'white' 
            : isActive 
              ? phaseInfo.color 
              : theme.palette.text.disabled,
          borderRadius: '50%',
          p: 0.7,
          mr: 1.5,
          width: 28,
          height: 28,
          fontSize: '1rem',
          transition: 'all 0.3s ease'
        }}
      >
        {isCompleted ? <DoneIcon fontSize="small" /> : phaseInfo.icon}
      </Box>
      
      <Box>
        <Typography 
          variant={isMobile ? "body2" : "body1"} 
          fontWeight={isActive || isCompleted ? 500 : 400}
          color={isActive || isCompleted ? 'text.primary' : 'text.secondary'}
        >
          {phaseInfo.title}
        </Typography>
        
        {!isMobile && (
          <Typography variant="caption" color="text.secondary">
            {phaseInfo.description}
          </Typography>
        )}
      </Box>
    </Box>
  );
};

// Preview components for different phases
const PreviewSearchQueries = ({ queries }) => {
  const theme = useTheme();
  if (!queries || queries.length === 0) return null;
  
  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent>
        <Typography variant="subtitle1" fontWeight={500} gutterBottom>
          Search Queries Generated
        </Typography>
        <Stack spacing={1}>
          {queries.map((query, index) => (
            <Chip
              key={index}
              label={query}
              icon={<SearchIcon />}
              variant="outlined"
              sx={{ 
                borderColor: alpha(theme.palette.primary.main, 0.4),
                '& .MuiChip-label': { fontWeight: 400 }
              }}
            />
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
};

const PreviewModules = ({ modules, showSubmodules = false }) => {
  const theme = useTheme();
  if (!modules || modules.length === 0) return null;
  
  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent>
        <Typography variant="subtitle1" fontWeight={500} gutterBottom>
          {showSubmodules ? 'Module Structure' : 'Learning Path Structure'}
        </Typography>
        
        <Stack spacing={1}>
          {modules.map((module, idx) => (
            <Box key={idx}>
              <Paper
                elevation={0}
                sx={{
                  p: 1.5,
                  bgcolor: alpha(theme.palette.primary.main, 0.05),
                  borderRadius: 1.5,
                  mb: showSubmodules && module.submodules ? 1 : 0
                }}
              >
                <Typography variant="body2" fontWeight={500}>
                  {idx + 1}. {module.title}
                </Typography>
                {module.description && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                    {module.description}
                  </Typography>
                )}
              </Paper>
              
              {showSubmodules && module.submodules && module.submodules.length > 0 && (
                <Box sx={{ pl: 4 }}>
                  <Stack spacing={0.5}>
                    {module.submodules.map((sub, subIdx) => (
                      <Paper
                        key={subIdx}
                        elevation={0}
                        sx={{
                          p: 1,
                          bgcolor: alpha(theme.palette.secondary.main, 0.05),
                          borderRadius: 1
                        }}
                      >
                        <Typography variant="caption" fontWeight={500}>
                          {subIdx + 1}. {sub.title}
                        </Typography>
                      </Paper>
                    ))}
                  </Stack>
                </Box>
              )}
            </Box>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
};

const PreviewContent = ({ submodules }) => {
  const theme = useTheme();
  
  if (!submodules || submodules.length === 0) return null;
  
  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent>
        <Typography variant="subtitle1" fontWeight={500} gutterBottom>
          Recent Content Development
        </Typography>
        
        <List dense>
          {submodules.map((submodule, idx) => (
            <ListItem 
              key={idx}
              disablePadding
              sx={{ 
                mb: 0.5, 
                p: 1,
                borderRadius: 1,
                bgcolor: alpha(theme.palette.primary.main, 0.04),
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                <CreateIcon fontSize="small" color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary={`${submodule.submodule_title}`}
                secondary={`In module: ${submodule.module_title}`}
                primaryTypographyProps={{
                  variant: 'body2',
                  fontWeight: 500
                }}
                secondaryTypographyProps={{
                  variant: 'caption'
                }}
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

const PreviewPath = ({ modules, totalModules, totalSubmodules }) => {
  const theme = useTheme();
  
  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
          <Typography variant="subtitle1" fontWeight={500}>
            Learning Path Summary
          </Typography>
          <Chip 
            label={`${totalModules} modules • ${totalSubmodules} submodules`}
            size="small"
            color="secondary"
          />
        </Stack>
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {modules.map((module, idx) => (
            <Chip
              key={idx}
              label={module.title}
              icon={<MenuBookIcon />}
              sx={{ 
                bgcolor: alpha(theme.palette.primary.main, 0.1),
                color: theme.palette.primary.main,
                fontWeight: 500
              }}
            />
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default ProgressTracker; 
import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  Card,
  CardContent,
  Divider,
  Chip,
  Alert,
  CircularProgress,
  useTheme,
  useMediaQuery,
  LinearProgress,
  Fade,
  Collapse,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';

// Icons
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import InfoIcon from '@mui/icons-material/Info';
import WarningIcon from '@mui/icons-material/Warning';
import PhoneIphoneIcon from '@mui/icons-material/PhoneIphone';
import DesktopWindowsIcon from '@mui/icons-material/DesktopWindows';
import TabletIcon from '@mui/icons-material/Tablet';
import ShareIcon from '@mui/icons-material/Share';
import AddToHomeScreenIcon from '@mui/icons-material/AddToHomeScreen';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import BookmarkBorderIcon from '@mui/icons-material/BookmarkBorder';
import OfflineBoltIcon from '@mui/icons-material/OfflineBolt';
import InstallDesktopIcon from '@mui/icons-material/InstallDesktop';
import DownloadIcon from '@mui/icons-material/Download';
import LaunchIcon from '@mui/icons-material/Launch';
import CelebrationIcon from '@mui/icons-material/Celebration';

// Enhanced help texts and utilities
import { helpTexts } from '../../constants/helpTexts';
import { 
  detectPWACapabilities, 
  getInstallationMethod, 
  createTutorialTracker,
  checkInstalledRelatedApps 
} from '../../utils/pwaDetection';

// Animation classes
import '../../utils/animations.css';

// Tutorial version for forcing re-display after enhancements
const TUTORIAL_VERSION = 'v2.0';

const PWA_TUTORIAL_STEPS = [
  { 
    id: 'benefits', 
    label: 'Benefits', 
    icon: '🚀',
    required: true 
  },
  { 
    id: 'install', 
    label: 'Install', 
    icon: '📱',
    required: true 
  },
  { 
    id: 'offline', 
    label: 'Offline', 
    icon: '📚',
    required: true 
  },
  { 
    id: 'complete', 
    label: 'Ready!', 
    icon: '🎉',
    required: false 
  }
];

// Icon mapping for browser-specific instructions
const INSTRUCTION_ICONS = {
  share: ShareIcon,
  add_to_home_screen: AddToHomeScreenIcon,
  check_circle: CheckCircleIcon,
  more_vert: MoreVertIcon,
  more_horiz: MoreHorizIcon,
  bookmark: BookmarkIcon,
  bookmark_border: BookmarkBorderIcon,
  offline_bolt: OfflineBoltIcon,
  install_desktop: InstallDesktopIcon,
  download: DownloadIcon,
  launch: LaunchIcon
};

const PwaIntroModal = ({ open, onClose }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [pwaCapabilities, setPwaCapabilities] = useState(null);
  const [installationMethod, setInstallationMethod] = useState('generic');
  const [isCheckingInstallation, setIsCheckingInstallation] = useState(false);
  const [installationVerified, setInstallationVerified] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const [tutorialTracker] = useState(() => createTutorialTracker(TUTORIAL_VERSION));
  
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  // Initialize PWA capabilities detection
  useEffect(() => {
    if (open) {
      const capabilities = detectPWACapabilities();
      setPwaCapabilities(capabilities);
      setInstallationMethod(getInstallationMethod(capabilities.browser, capabilities.device));
      
      // If already installed, skip install step
      if (capabilities.isInstalled) {
        setInstallationVerified(true);
        // Skip to offline step if already installed
        setActiveStep(2);
      }
    }
  }, [open]);

  // Async installation verification for supported browsers
  useEffect(() => {
    let mounted = true;
    
    const verifyInstallation = async () => {
      if (pwaCapabilities && activeStep === 3) {
        setIsCheckingInstallation(true);
        
        try {
          const isInstalled = await checkInstalledRelatedApps();
          if (mounted) {
            setInstallationVerified(isInstalled || pwaCapabilities.isInstalled);
            setIsCheckingInstallation(false);
            
            if (isInstalled && !installationVerified) {
              setShowCelebration(true);
              setTimeout(() => setShowCelebration(false), 2000);
            }
          }
        } catch (error) {
          console.warn('Installation verification failed:', error);
          if (mounted) {
            setIsCheckingInstallation(false);
          }
        }
      }
    };

    verifyInstallation();
    
    return () => {
      mounted = false;
    };
  }, [activeStep, pwaCapabilities, installationVerified]);

  const handleNext = useCallback(() => {
    if (activeStep < PWA_TUTORIAL_STEPS.length - 1) {
      setActiveStep((prev) => prev + 1);
    }
  }, [activeStep]);

  const handleBack = useCallback(() => {
    if (activeStep > 0) {
      setActiveStep((prev) => prev - 1);
    }
  }, [activeStep]);

  const handleSkip = useCallback(() => {
    tutorialTracker.markCompleted();
    onClose();
  }, [onClose, tutorialTracker]);

  const handleFinish = useCallback(() => {
    tutorialTracker.markCompleted();
    if (activeStep === PWA_TUTORIAL_STEPS.length - 1) {
      setShowCelebration(true);
      setTimeout(() => {
        onClose();
        setShowCelebration(false);
      }, 1500);
    } else {
      onClose();
    }
  }, [onClose, tutorialTracker, activeStep]);

  const handleClose = useCallback(() => {
    onClose();
    setTimeout(() => {
      setActiveStep(0);
      setInstallationVerified(false);
      setShowCelebration(false);
    }, 300);
  }, [onClose]);

  // Get device icon based on capabilities
  const getDeviceIcon = () => {
    if (!pwaCapabilities) return PhoneIphoneIcon;
    
    switch (pwaCapabilities.device) {
      case 'ios':
      case 'android':
        return PhoneIphoneIcon;
      case 'desktop':
        return DesktopWindowsIcon;
      default:
        return TabletIcon;
    }
  };

  // Render benefits step
  const renderBenefitsStep = () => {
    const { step1 } = helpTexts.pwaIntro;
    
    return (
      <Box className="pwa-step-enter">
        <Typography variant="h5" gutterBottom align="center" sx={{ mb: 2 }}>
          {step1.title}
        </Typography>
        <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 3 }}>
          {step1.subtitle}
        </Typography>
        
        <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr' }}>
          {step1.benefits.map((benefit, index) => (
            <Card 
              key={benefit.title}
              className={`pwa-benefit-card pwa-transition-smooth`}
              sx={{ 
                border: `1px solid ${theme.palette.divider}`,
                '&:hover': { 
                  borderColor: theme.palette.primary.main,
                  transform: 'translateY(-2px)',
                  boxShadow: theme.shadows[4]
                }
              }}
            >
              <CardContent sx={{ textAlign: 'center', p: 2 }}>
                <Typography variant="h3" sx={{ mb: 1 }}>
                  {benefit.icon}
                </Typography>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  {benefit.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {benefit.description}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
        
        <Box sx={{ textAlign: 'center', mt: 3 }}>
          <Typography variant="body1" color="primary" fontWeight="medium">
            {step1.callToAction}
          </Typography>
        </Box>
      </Box>
    );
  };

  // Render installation step
  const renderInstallStep = () => {
    if (!pwaCapabilities) return <CircularProgress />;
    
    const { step2 } = helpTexts.pwaIntro;
    const methodInstructions = step2[installationMethod] || step2.generic;
    const DeviceIcon = getDeviceIcon();
    
    return (
      <Box className="pwa-step-enter">
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
          <DeviceIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h5" align="center">
            {methodInstructions.title}
          </Typography>
        </Box>
        
        {pwaCapabilities.isInstalled ? (
          <Alert severity="success" sx={{ mb: 2 }}>
            <Typography variant="body1">
              {helpTexts.pwaIntro.step4.verification.alreadyInstalled.title}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {helpTexts.pwaIntro.step4.verification.alreadyInstalled.description}
            </Typography>
          </Alert>
        ) : (
          <>
            <List sx={{ mb: 2 }}>
              {methodInstructions.steps.map((step, index) => {
                const IconComponent = INSTRUCTION_ICONS[step.icon] || InfoIcon;
                
                return (
                  <ListItem key={index} className="pwa-install-step" sx={{ px: 0 }}>
                    <ListItemIcon>
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: 40,
                          height: 40,
                          borderRadius: '50%',
                          backgroundColor: 'primary.main',
                          color: 'white',
                          mr: 1
                        }}
                      >
                        <Typography variant="body2" fontWeight="bold">
                          {index + 1}
                        </Typography>
                      </Box>
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <IconComponent sx={{ mr: 1, color: 'primary.main' }} />
                          <Typography variant="body1" fontWeight="medium">
                            {step.instruction}
                          </Typography>
                        </Box>
                      }
                      secondary={step.detail}
                    />
                  </ListItem>
                );
              })}
            </List>
            
            {methodInstructions.troubleshooting && (
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Troubleshooting:</strong> {methodInstructions.troubleshooting}
                </Typography>
              </Alert>
            )}
          </>
        )}
      </Box>
    );
  };

  // Render offline benefits step
  const renderOfflineStep = () => {
    const { step3 } = helpTexts.pwaIntro;
    
    return (
      <Box className="pwa-step-enter">
        <Typography variant="h5" gutterBottom align="center">
          {step3.title}
        </Typography>
        <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 3 }}>
          {step3.subtitle}
        </Typography>
        
        <Paper sx={{ p: 2, mb: 3, backgroundColor: 'grey.50' }}>
          <Typography variant="h6" gutterBottom color="primary">
            {step3.demonstration.title}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {step3.demonstration.description}
          </Typography>
          
          <Box sx={{ display: 'grid', gap: 1.5, gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr' }}>
            {step3.demonstration.features.map((feature, index) => (
              <Box 
                key={feature.title}
                className="pwa-feature-demo"
                sx={{ display: 'flex', alignItems: 'center', p: 1 }}
              >
                <Typography variant="h6" sx={{ mr: 1.5 }}>
                  {feature.icon}
                </Typography>
                <Box>
                  <Typography variant="subtitle2" fontWeight="bold">
                    {feature.title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {feature.description}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>
        </Paper>
        
        <Card sx={{ border: `1px solid ${theme.palette.primary.main}` }}>
          <CardContent>
            <Typography variant="h6" color="primary" gutterBottom>
              {step3.howItWorks.title}
            </Typography>
            <List dense>
              {step3.howItWorks.steps.map((step, index) => (
                <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <Typography variant="body2" color="primary" fontWeight="bold">
                      {index + 1}.
                    </Typography>
                  </ListItemIcon>
                  <ListItemText 
                    primary={
                      <Typography variant="body2">
                        {step}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
        
        <Box sx={{ textAlign: 'center', mt: 2 }}>
          <Typography variant="body1" color="primary" fontWeight="medium">
            {step3.callToAction}
          </Typography>
        </Box>
      </Box>
    );
  };

  // Render completion step
  const renderCompletionStep = () => {
    const { step4 } = helpTexts.pwaIntro;
    
    return (
      <Box className="pwa-step-enter">
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          {showCelebration && (
            <Box className="pwa-confetti">
              <CelebrationIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
            </Box>
          )}
          <Typography variant="h4" gutterBottom>
            {step4.title}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {step4.subtitle}
          </Typography>
        </Box>
        
        {isCheckingInstallation ? (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', my: 3 }}>
            <CircularProgress size={24} sx={{ mr: 1 }} />
            <Typography variant="body2" color="text.secondary">
              {helpTexts.pwaIntro.status.checkingInstallation}
            </Typography>
          </Box>
        ) : (
          <Alert 
            severity={installationVerified ? "success" : "info"}
            sx={{ mb: 3 }}
          >
            <Typography variant="body1">
              {installationVerified 
                ? helpTexts.pwaIntro.status.installationDetected
                : helpTexts.pwaIntro.status.installationNotDetected
              }
            </Typography>
          </Alert>
        )}
        
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom color="primary">
            {step4.success.title}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {step4.success.description}
          </Typography>
          
          <Box sx={{ display: 'grid', gap: 1.5, gridTemplateColumns: '1fr' }}>
            {step4.success.nextSteps.map((step, index) => (
              <Box 
                key={step.title}
                className="pwa-content-reveal"
                sx={{ 
                  display: 'flex', 
                  alignItems: 'flex-start', 
                  p: 1.5,
                  backgroundColor: 'grey.50',
                  borderRadius: 1,
                  border: `1px solid ${theme.palette.divider}`
                }}
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <Typography variant="h6" sx={{ mr: 1.5, mt: 0.5 }}>
                  {step.icon}
                </Typography>
                <Box>
                  <Typography variant="subtitle2" fontWeight="bold">
                    {step.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {step.description}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>
        </Paper>
        
        <Card sx={{ backgroundColor: 'primary.main', color: 'white' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {step4.tips.title}
            </Typography>
            <List dense>
              {step4.tips.items.map((tip, index) => (
                <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 24 }}>
                    <Typography variant="body2" sx={{ color: 'inherit' }}>
                      💡
                    </Typography>
                  </ListItemIcon>
                  <ListItemText 
                    primary={
                      <Typography variant="body2" sx={{ color: 'inherit' }}>
                        {tip}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </Box>
    );
  };

  // Render current step content
  const renderCurrentStepContent = () => {
    switch (activeStep) {
      case 0:
        return renderBenefitsStep();
      case 1:
        return renderInstallStep();
      case 2:
        return renderOfflineStep();
      case 3:
        return renderCompletionStep();
      default:
        return null;
    }
  };

  const currentStep = PWA_TUTORIAL_STEPS[activeStep];
  const isLastStep = activeStep === PWA_TUTORIAL_STEPS.length - 1;
  const progressPercentage = ((activeStep + 1) / PWA_TUTORIAL_STEPS.length) * 100;

  return (
    <Dialog
      open={open}
      onClose={(event, reason) => {
        if (reason !== 'backdropClick' && reason !== 'escapeKeyDown') {
          handleClose();
        }
      }}
      maxWidth="md"
      fullWidth
      fullScreen={isMobile}
      TransitionProps={{ 
        onExited: () => {
          setActiveStep(0);
          setInstallationVerified(false);
          setShowCelebration(false);
        }
      }}
      PaperProps={{
        className: 'pwa-modal-enter',
        sx: {
          backdropFilter: 'blur(8px)',
          maxHeight: isMobile ? '100vh' : '90vh',
          height: isMobile ? '100vh' : 'auto'
        }
      }}
      BackdropProps={{
        className: 'pwa-backdrop'
      }}
    >
      {/* Header with progress */}
      <DialogTitle sx={{ 
        textAlign: 'center', 
        pt: isMobile ? 2 : 3,
        pb: 1,
        position: 'relative'
      }}>
        <Box sx={{ mb: 2 }}>
          <Typography variant={isMobile ? 'h5' : 'h4'} component="h1" gutterBottom>
            {helpTexts.pwaIntro.title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {helpTexts.pwaIntro.subtitle}
          </Typography>
        </Box>
        
        <LinearProgress 
          variant="determinate" 
          value={progressPercentage}
          className="pwa-progress-fill"
          sx={{ 
            height: 4, 
            borderRadius: 2,
            backgroundColor: 'grey.200',
            '& .MuiLinearProgress-bar': {
              borderRadius: 2,
              backgroundColor: 'primary.main'
            }
          }}
          style={{ '--progress-width': `${progressPercentage}%` }}
        />
        
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          mt: 2 
        }}>
          <Chip 
            label={`Step ${activeStep + 1} of ${PWA_TUTORIAL_STEPS.length}`}
            size="small"
            color="primary"
          />
          <Button 
            size="small" 
            onClick={handleSkip}
            sx={{ minWidth: 'auto' }}
          >
            {helpTexts.pwaIntro.skipButton}
          </Button>
        </Box>
      </DialogTitle>

      {/* Main content */}
      <DialogContent sx={{ 
        textAlign: 'center', 
        minHeight: isMobile ? '60vh' : '400px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        px: isMobile ? 2 : 3,
        py: 2
      }}>
        <Fade in={true} key={activeStep} timeout={300}>
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            {renderCurrentStepContent()}
          </Box>
        </Fade>
      </DialogContent>

      {/* Navigation footer */}
      <DialogActions sx={{ 
        p: isMobile ? 2 : 3, 
        flexDirection: 'column',
        alignItems: 'stretch'
      }}>
        {/* Step indicator */}
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center',
          mb: 2,
          gap: 1
        }}>
          {PWA_TUTORIAL_STEPS.map((step, index) => (
            <Box
              key={step.id}
              sx={{
                width: 32,
                height: 32,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: index <= activeStep ? 'primary.main' : 'grey.300',
                color: index <= activeStep ? 'white' : 'text.secondary',
                transition: 'all 0.3s ease',
                fontSize: '1rem'
              }}
              className={index === activeStep ? 'pwa-stepper-active' : ''}
            >
              {step.icon}
            </Box>
          ))}
        </Box>
        
        {/* Navigation buttons */}
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          width: '100%',
          gap: 2
        }}>
          <Button 
            onClick={handleBack} 
            disabled={activeStep === 0}
            startIcon={<NavigateBeforeIcon />}
            variant="outlined"
            className="pwa-btn-hover"
            sx={{ flex: 1 }}
          >
            {helpTexts.pwaIntro.backButton}
          </Button>
          
          {isLastStep ? (
            <Button 
              variant="contained" 
              onClick={handleFinish}
              endIcon={<CheckCircleIcon />}
              className="pwa-btn-hover pwa-glow"
              sx={{ flex: 2 }}
            >
              {helpTexts.pwaIntro.finishButton}
            </Button>
          ) : (
            <Button 
              variant="contained" 
              onClick={handleNext}
              endIcon={<NavigateNextIcon />}
              className="pwa-btn-hover"
              sx={{ flex: 2 }}
            >
              {helpTexts.pwaIntro.nextButton}
            </Button>
          )}
        </Box>
      </DialogActions>
    </Dialog>
  );
};

PwaIntroModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default PwaIntroModal;

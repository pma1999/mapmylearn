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
            const newInstallationVerified = isInstalled || pwaCapabilities.isInstalled;
            setInstallationVerified(newInstallationVerified);
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
  }, [activeStep, pwaCapabilities]);

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
        <Typography variant={isMobile ? "h6" : "h5"} gutterBottom align="center" sx={{ mb: 1.5 }}>
          {step1.title}
        </Typography>
        <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 2 }}>
          {step1.subtitle}
        </Typography>
        
        <Box sx={{ display: 'grid', gap: 1.5, gridTemplateColumns: '1fr' }}>
          {step1.benefits.map((benefit, index) => (
            <Card 
              key={benefit.title}
              className={`pwa-benefit-card pwa-transition-smooth`}
              sx={{ 
                border: `1px solid ${theme.palette.divider}`,
                '&:hover': { 
                  borderColor: theme.palette.primary.main,
                  transform: 'translateY(-1px)',
                  boxShadow: theme.shadows[2]
                }
              }}
            >
              <CardContent sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                p: 1.5,
                '&:last-child': { pb: 1.5 }
              }}>
                <Typography variant="h5" sx={{ mr: 1.5, flexShrink: 0 }}>
                  {benefit.icon}
                </Typography>
                <Box>
                  <Typography variant="subtitle2" fontWeight="bold" gutterBottom sx={{ mb: 0.5 }}>
                    {benefit.title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {benefit.description}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>
        
        <Box sx={{ textAlign: 'center', mt: 2 }}>
          <Typography variant="body2" color="primary" fontWeight="medium">
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
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1.5 }}>
          <DeviceIcon sx={{ mr: 1, color: 'primary.main', fontSize: '1.2rem' }} />
          <Typography variant={isMobile ? "h6" : "h5"} align="center">
            {methodInstructions.title}
          </Typography>
        </Box>
        
        {pwaCapabilities.isInstalled ? (
          <Alert severity="success" sx={{ mb: 2 }}>
            <Typography variant="body2">
              {helpTexts.pwaIntro.step4.verification.alreadyInstalled.title}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {helpTexts.pwaIntro.step4.verification.alreadyInstalled.description}
            </Typography>
          </Alert>
        ) : (
          <>
            <List dense sx={{ mb: 1 }}>
              {methodInstructions.steps.map((step, index) => {
                const IconComponent = INSTRUCTION_ICONS[step.icon] || InfoIcon;
                
                return (
                  <ListItem key={index} className="pwa-install-step" sx={{ px: 0, py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: 28,
                          height: 28,
                          borderRadius: '50%',
                          backgroundColor: 'primary.main',
                          color: 'white'
                        }}
                      >
                        <Typography variant="caption" fontWeight="bold">
                          {index + 1}
                        </Typography>
                      </Box>
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <IconComponent sx={{ mr: 1, color: 'primary.main', fontSize: '1rem' }} />
                          <Typography variant="body2" fontWeight="medium">
                            {step.instruction}
                          </Typography>
                        </Box>
                      }
                      secondary={
                        <Typography variant="caption" color="text.secondary">
                          {step.detail}
                        </Typography>
                      }
                    />
                  </ListItem>
                );
              })}
            </List>
            
            {methodInstructions.troubleshooting && (
              <Alert severity="info" sx={{ mt: 1 }}>
                <Typography variant="caption">
                  <strong>Tip:</strong> {methodInstructions.troubleshooting}
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
        <Typography variant={isMobile ? "h6" : "h5"} gutterBottom align="center">
          {step3.title}
        </Typography>
        <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 2 }}>
          {step3.subtitle}
        </Typography>
        
        <Paper sx={{ p: 1.5, mb: 2, backgroundColor: 'grey.50' }}>
          <Typography variant="subtitle2" gutterBottom color="primary">
            {step3.demonstration.title}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 1.5, display: 'block' }}>
            {step3.demonstration.description}
          </Typography>
          
          <Box sx={{ display: 'grid', gap: 1, gridTemplateColumns: '1fr' }}>
            {step3.demonstration.features.map((feature, index) => (
              <Box 
                key={feature.title}
                className="pwa-feature-demo"
                sx={{ display: 'flex', alignItems: 'center', py: 0.5 }}
              >
                <Typography variant="body1" sx={{ mr: 1, flexShrink: 0 }}>
                  {feature.icon}
                </Typography>
                <Box>
                  <Typography variant="caption" fontWeight="bold" display="block">
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
          <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              {step3.howItWorks.title}
            </Typography>
            <List dense>
              {step3.howItWorks.steps.map((step, index) => (
                <ListItem key={index} sx={{ px: 0, py: 0.25 }}>
                  <ListItemIcon sx={{ minWidth: 24 }}>
                    <Typography variant="caption" color="primary" fontWeight="bold">
                      {index + 1}.
                    </Typography>
                  </ListItemIcon>
                  <ListItemText 
                    primary={
                      <Typography variant="caption">
                        {step}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
        
        <Box sx={{ textAlign: 'center', mt: 1.5 }}>
          <Typography variant="body2" color="primary" fontWeight="medium">
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
        <Box sx={{ textAlign: 'center', mb: 2 }}>
          {showCelebration && (
            <Box className="pwa-confetti">
              <CelebrationIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
            </Box>
          )}
          <Typography variant={isMobile ? "h5" : "h4"} gutterBottom>
            {step4.title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {step4.subtitle}
          </Typography>
        </Box>
        
        {isCheckingInstallation ? (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', my: 2 }}>
            <CircularProgress size={20} sx={{ mr: 1 }} />
            <Typography variant="caption" color="text.secondary">
              {helpTexts.pwaIntro.status.checkingInstallation}
            </Typography>
          </Box>
        ) : (
          <Alert 
            severity={installationVerified ? "success" : "info"}
            sx={{ mb: 2 }}
          >
            <Typography variant="body2">
              {installationVerified 
                ? helpTexts.pwaIntro.status.installationDetected
                : helpTexts.pwaIntro.status.installationNotDetected
              }
            </Typography>
          </Alert>
        )}
        
        <Paper sx={{ p: 1.5, mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom color="primary">
            {step4.success.title}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 1.5, display: 'block' }}>
            {step4.success.description}
          </Typography>
          
          <Box sx={{ display: 'grid', gap: 1, gridTemplateColumns: '1fr' }}>
            {step4.success.nextSteps.slice(0, 3).map((step, index) => (
              <Box 
                key={step.title}
                className="pwa-content-reveal"
                sx={{ 
                  display: 'flex', 
                  alignItems: 'flex-start', 
                  py: 0.75,
                  px: 1,
                  backgroundColor: 'grey.50',
                  borderRadius: 0.5
                }}
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <Typography variant="body2" sx={{ mr: 1, flexShrink: 0 }}>
                  {step.icon}
                </Typography>
                <Box>
                  <Typography variant="caption" fontWeight="bold" display="block">
                    {step.title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {step.description}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>
        </Paper>
        
        <Card sx={{ backgroundColor: 'primary.main', color: 'white' }}>
          <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
            <Typography variant="subtitle2" gutterBottom>
              💡 Quick Tips:
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
              {step4.tips.items.slice(0, 2).map((tip, index) => (
                <Typography key={index} variant="caption" sx={{ color: 'inherit' }}>
                  • {tip}
                </Typography>
              ))}
            </Box>
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
      maxWidth="sm"
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
          height: isMobile ? '100vh' : 'auto',
          maxHeight: isMobile ? '100vh' : '85vh',
          margin: isMobile ? 0 : 2,
          display: 'flex',
          flexDirection: 'column'
        }
      }}
      BackdropProps={{
        className: 'pwa-backdrop'
      }}
    >
      {/* Header with progress */}
      <DialogTitle sx={{ 
        textAlign: 'center', 
        pt: isMobile ? 1.5 : 2,
        pb: 1,
        flexShrink: 0
      }}>
        <Box sx={{ mb: 1.5 }}>
          <Typography variant={isMobile ? 'h6' : 'h5'} component="h1" gutterBottom>
            {helpTexts.pwaIntro.title}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {helpTexts.pwaIntro.subtitle}
          </Typography>
        </Box>
        
        <LinearProgress 
          variant="determinate" 
          value={progressPercentage}
          className="pwa-progress-fill"
          sx={{ 
            height: 3, 
            borderRadius: 1.5,
            backgroundColor: 'grey.200',
            '& .MuiLinearProgress-bar': {
              borderRadius: 1.5,
              backgroundColor: 'primary.main'
            }
          }}
          style={{ '--progress-width': `${progressPercentage}%` }}
        />
        
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          mt: 1.5 
        }}>
          <Chip 
            label={`${activeStep + 1} / ${PWA_TUTORIAL_STEPS.length}`}
            size="small"
            color="primary"
            sx={{ fontSize: '0.7rem', height: 24 }}
          />
          <Button 
            size="small" 
            onClick={handleSkip}
            sx={{ minWidth: 'auto', fontSize: '0.75rem', py: 0.5, px: 1 }}
          >
            {helpTexts.pwaIntro.skipButton}
          </Button>
        </Box>
      </DialogTitle>

      {/* Main content with scroll */}
      <DialogContent sx={{ 
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        px: isMobile ? 2 : 3,
        py: 1,
        overflow: 'auto'
      }}>
        <Fade in={true} key={activeStep} timeout={300}>
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            {renderCurrentStepContent()}
          </Box>
        </Fade>
      </DialogContent>

      {/* Navigation footer */}
      <DialogActions sx={{ 
        p: isMobile ? 1.5 : 2, 
        flexDirection: 'column',
        alignItems: 'stretch',
        flexShrink: 0
      }}>
        {/* Step indicator */}
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center',
          mb: 1.5,
          gap: 0.75
        }}>
          {PWA_TUTORIAL_STEPS.map((step, index) => (
            <Box
              key={step.id}
              sx={{
                width: 24,
                height: 24,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: index <= activeStep ? 'primary.main' : 'grey.300',
                color: index <= activeStep ? 'white' : 'text.secondary',
                transition: 'all 0.3s ease',
                fontSize: '0.75rem'
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
          gap: 1.5
        }}>
          <Button 
            onClick={handleBack} 
            disabled={activeStep === 0}
            startIcon={<NavigateBeforeIcon sx={{ fontSize: '1rem' }} />}
            variant="outlined"
            size="small"
            className="pwa-btn-hover"
            sx={{ flex: 1, fontSize: '0.8rem' }}
          >
            {helpTexts.pwaIntro.backButton}
          </Button>
          
          {isLastStep ? (
            <Button 
              variant="contained" 
              onClick={handleFinish}
              endIcon={<CheckCircleIcon sx={{ fontSize: '1rem' }} />}
              size="small"
              className="pwa-btn-hover pwa-glow"
              sx={{ flex: 2, fontSize: '0.8rem' }}
            >
              {helpTexts.pwaIntro.finishButton}
            </Button>
          ) : (
            <Button 
              variant="contained" 
              onClick={handleNext}
              endIcon={<NavigateNextIcon sx={{ fontSize: '1rem' }} />}
              size="small"
              className="pwa-btn-hover"
              sx={{ flex: 2, fontSize: '0.8rem' }}
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

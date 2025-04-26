import React, { useState } from 'react';
import PropTypes from 'prop-types';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  IconButton,
  Stepper,
  Step,
  StepLabel,
  useTheme,
  useMediaQuery
} from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import { helpTexts } from '../../constants/helpTexts';
import { useAuth } from '../../services/authContext'; // Import useAuth

const steps = [
  { label: 'Welcome', contentKey: 'welcomeValueProp' },
  { label: 'How it Works', contentKey: 'welcomeHowItWorks' },
  { label: 'Get Started', contentKey: 'welcomeCredits' }
];

const WelcomeModal = ({ open, onClose }) => {
  const [activeStep, setActiveStep] = useState(0);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const { user } = useAuth(); // Get user from context for credits

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleClose = () => {
    onClose(); // This should set the flag in AuthContext
    // Reset step for next time if needed (though usually unmounted)
    setTimeout(() => setActiveStep(0), 300); 
  };

  // Get content for the current step
  let currentContent = '';
  const currentStepData = steps[activeStep];
  if (currentStepData) {
    if (currentStepData.contentKey === 'welcomeCredits') {
      // Pass the user's credits to the function
      const credits = user?.credits ?? 0; // Default to 0 if user or credits undefined
      currentContent = helpTexts.welcomeCredits(credits);
    } else {
      currentContent = helpTexts[currentStepData.contentKey];
    }
  }

  return (
    <Dialog 
      open={open}
      onClose={(event, reason) => {
        // Prevent closing on backdrop click or escape key
        if (reason !== 'backdropClick' && reason !== 'escapeKeyDown') {
          handleClose();
        }
      }}
      maxWidth="sm" 
      fullWidth
      TransitionProps={{ onExited: () => setActiveStep(0) }} // Reset step when closed
    >
      <DialogTitle sx={{ textAlign: 'center', pt: 3 }}>
        {activeStep === 0 ? helpTexts.welcomeTitle : steps[activeStep]?.label}
      </DialogTitle>
      <DialogContent sx={{ textAlign: 'center', minHeight: '150px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          {currentContent}
        </Typography>
      </DialogContent>
      <DialogActions sx={{ p: 2, flexDirection: 'column', alignItems: 'center' }}>
        <Stepper activeStep={activeStep} alternativeLabel={isMobile} sx={{ width: '100%', mb: 2 }}>
          {steps.map((step, index) => (
            <Step key={step.label}>
              <StepLabel sx={{ '.MuiStepLabel-label': { fontSize: '0.8rem' } }} />
            </Step>
          ))}
        </Stepper>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
          <Button
            onClick={handleBack}
            disabled={activeStep === 0}
            startIcon={<NavigateBeforeIcon />}
          >
            Back
          </Button>
          {activeStep === steps.length - 1 ? (
            <Button 
              variant="contained" 
              onClick={handleClose} 
              color="primary"
            >
              {helpTexts.welcomeGo}
            </Button>
          ) : (
            <Button 
              variant="contained" 
              onClick={handleNext} 
              endIcon={<NavigateNextIcon />}
            >
              Next
            </Button>
          )}
        </Box>
      </DialogActions>
    </Dialog>
  );
};

WelcomeModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default WelcomeModal; 
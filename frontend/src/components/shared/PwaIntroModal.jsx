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
  Stepper,
  Step,
  StepLabel,
  useTheme,
  useMediaQuery
} from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import { helpTexts } from '../../constants/helpTexts';

const steps = [
  { label: 'Install', contentKey: 'pwaInstall' },
  { label: 'Offline', contentKey: 'pwaOfflineUsage' }
];

const PwaIntroModal = ({ open, onClose }) => {
  const [activeStep, setActiveStep] = useState(0);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleNext = () => setActiveStep((prev) => prev + 1);
  const handleBack = () => setActiveStep((prev) => prev - 1);
  const handleClose = () => {
    onClose();
    setTimeout(() => setActiveStep(0), 300);
  };

  const currentContent = helpTexts[steps[activeStep].contentKey];

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
      TransitionProps={{ onExited: () => setActiveStep(0) }}
    >
      <DialogTitle sx={{ textAlign: 'center', pt: 3 }}>
        {helpTexts.pwaIntroTitle}
      </DialogTitle>
      <DialogContent sx={{ textAlign: 'center', minHeight: '150px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          {currentContent}
        </Typography>
      </DialogContent>
      <DialogActions sx={{ p: 2, flexDirection: 'column', alignItems: 'center' }}>
        <Stepper activeStep={activeStep} alternativeLabel={isMobile} sx={{ width: '100%', mb: 2 }}>
          {steps.map((step) => (
            <Step key={step.label}>
              <StepLabel sx={{ '.MuiStepLabel-label': { fontSize: '0.8rem' } }}>{step.label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
          <Button onClick={handleBack} disabled={activeStep === 0} startIcon={<NavigateBeforeIcon />}>Back</Button>
          {activeStep === steps.length - 1 ? (
            <Button variant="contained" onClick={handleClose} color="primary">
              {helpTexts.pwaIntroGotIt}
            </Button>
          ) : (
            <Button variant="contained" onClick={handleNext} endIcon={<NavigateNextIcon />}>Next</Button>
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

import React, { useState } from 'react';
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Box,
  TextField,
  Button,
  FormControlLabel,
  Checkbox,
  InputAdornment,
  IconButton,
  Grid,
  Stack,
  CircularProgress,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Link,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  Divider,
  Collapse,
  Alert,
  Chip
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import KeyIcon from '@mui/icons-material/Key';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import SecurityIcon from '@mui/icons-material/Security';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import LaunchIcon from '@mui/icons-material/Launch';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import InfoIcon from '@mui/icons-material/Info';
import CreditCardIcon from '@mui/icons-material/CreditCard';

const ApiKeySettings = ({
  apiSettingsOpen,
  setApiSettingsOpen,
  isMobile
}) => {
  const [showInstructions, setShowInstructions] = useState(true);

  return (
    <Accordion 
      expanded={apiSettingsOpen} 
      onChange={() => setApiSettingsOpen(!apiSettingsOpen)}
      sx={{ mb: 2 }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="api-key-settings-content"
        id="api-key-settings-header"
      >
        <Stack direction="row" spacing={1} alignItems="center">
          <KeyIcon color="primary" />
          <Typography variant="h6" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>API Key Settings</Typography>
          <Chip 
            label="Server Provided" 
            color="success" 
            size="small" 
            icon={<CheckCircleIcon />} 
            sx={{ ml: 1 }}
          />
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <Alert severity="success" sx={{ mb: 3 }}>
          <Typography variant="body1" fontWeight="bold">
            API keys are now provided by the server!
          </Typography>
          <Typography variant="body2">
            You no longer need to provide your own API keys. All API requests use our server keys.
          </Typography>
        </Alert>
        
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary" paragraph sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
            We've updated our service to provide API keys directly from our server. This means you can generate learning paths without having to provide your own Google or Perplexity API keys.
          </Typography>
          
          <Button 
            variant="text" 
            color="primary" 
            startIcon={<InfoIcon />}
            onClick={() => setShowInstructions(!showInstructions)}
            size={isMobile ? "small" : "medium"}
            sx={{ mb: 1 }}
          >
            {showInstructions ? "Hide Details" : "Show Details"}
          </Button>
          
          <Collapse in={showInstructions}>
            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent sx={{ p: { xs: 1.5, sm: 2 } }}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  About Server-Provided API Keys
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Typography variant="body2" paragraph>
                      We now provide API keys for both Google Gemini AI and Perplexity AI directly from our server. This makes it easier and faster for you to generate learning paths.
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined" sx={{ height: '100%' }}>
                      <CardContent>
                        <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                          <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" alt="Google Logo" width="20" />
                          <Typography variant="subtitle1" fontWeight="bold">Google AI (Gemini)</Typography>
                        </Stack>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          Google's Gemini API is used for generating personalized learning paths with accurate and well-structured content.
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined" sx={{ height: '100%' }}>
                      <CardContent>
                        <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                          <img src="https://www.perplexity.ai/favicon.ico" alt="Perplexity Logo" width="20" />
                          <Typography variant="subtitle1" fontWeight="bold">Perplexity API</Typography>
                        </Stack>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          Perplexity API is used for web search operations to enrich learning paths with up-to-date information from across the internet.
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Collapse>
          
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            bgcolor: 'info.light', 
            p: 1.5, 
            borderRadius: 1,
            color: 'info.contrastText'
          }}>
            <CreditCardIcon sx={{ mr: 1 }} />
            <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
              Coming Soon: Credit system for tracking and managing your API usage. Stay tuned for updates!
            </Typography>
          </Box>
        </Box>
        
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="info.main" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
            Note: Our server handles all API keys securely. Your requests are processed with enterprise-grade security practices.
          </Typography>
        </Box>
      </AccordionDetails>
    </Accordion>
  );
};

export default ApiKeySettings; 
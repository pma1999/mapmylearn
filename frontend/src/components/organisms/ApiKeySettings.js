import React from 'react';
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
  CircularProgress
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import KeyIcon from '@mui/icons-material/Key';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

const ApiKeySettings = ({
  apiSettingsOpen,
  setApiSettingsOpen,
  googleApiKey,
  setGoogleApiKey,
  pplxApiKey,
  setPplxApiKey,
  showGoogleKey,
  setShowGoogleKey,
  showPplxKey,
  setShowPplxKey,
  rememberApiKeys,
  setRememberApiKeys,
  googleKeyValid,
  pplxKeyValid,
  validatingKeys,
  isGenerating,
  handleValidateApiKeys,
  handleClearApiKeys,
  isMobile
}) => {
  return (
    <Accordion 
      expanded={apiSettingsOpen} 
      onChange={() => setApiSettingsOpen(!apiSettingsOpen)}
      disabled={isGenerating}
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
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <Typography variant="body2" color="text.secondary" paragraph sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
          To generate learning paths, you need to provide your own API keys. These keys are required to make requests to external AI and search services.
        </Typography>
        
        <Grid container spacing={isMobile ? 2 : 3} direction="column">
          <Grid item>
            <TextField
              label="Google API Key"
              variant="outlined"
              fullWidth
              value={googleApiKey}
              onChange={(e) => setGoogleApiKey(e.target.value)}
              type={showGoogleKey ? 'text' : 'password'}
              placeholder="AIza..."
              disabled={isGenerating}
              margin="dense"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={() => setShowGoogleKey(!showGoogleKey)}
                      edge="end"
                      size={isMobile ? "small" : "medium"}
                    >
                      {showGoogleKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                    {googleKeyValid === true && (
                      <CheckCircleIcon color="success" sx={{ ml: 1 }} />
                    )}
                    {googleKeyValid === false && (
                      <ErrorIcon color="error" sx={{ ml: 1 }} />
                    )}
                  </InputAdornment>
                ),
              }}
              helperText={
                googleKeyValid === false ? "Invalid Google API key" : 
                googleKeyValid === true ? "API key validated" : 
                "Required - Enter your Google API key (starts with AIza...)"
              }
            />
          </Grid>
          
          <Grid item>
            <TextField
              label="Perplexity API Key"
              variant="outlined"
              fullWidth
              value={pplxApiKey}
              onChange={(e) => setPplxApiKey(e.target.value)}
              type={showPplxKey ? 'text' : 'password'}
              placeholder="pplx-..."
              disabled={isGenerating}
              margin="dense"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={() => setShowPplxKey(!showPplxKey)}
                      edge="end"
                      size={isMobile ? "small" : "medium"}
                    >
                      {showPplxKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                    {pplxKeyValid === true && (
                      <CheckCircleIcon color="success" sx={{ ml: 1 }} />
                    )}
                    {pplxKeyValid === false && (
                      <ErrorIcon color="error" sx={{ ml: 1 }} />
                    )}
                  </InputAdornment>
                ),
              }}
              helperText={
                pplxKeyValid === false ? "Invalid Perplexity API key" : 
                pplxKeyValid === true ? "API key validated" : 
                "Required - Enter your Perplexity API key (starts with pplx-)"
              }
            />
          </Grid>
          
          <Grid item>
            <FormControlLabel
              control={
                <Checkbox
                  checked={rememberApiKeys}
                  onChange={(e) => setRememberApiKeys(e.target.checked)}
                  disabled={isGenerating}
                  size={isMobile ? "small" : "medium"}
                />
              }
              label={
                <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                  Remember API keys for this session
                </Typography>
              }
            />
          </Grid>
          
          <Grid item>
            <Stack 
              direction={isMobile ? "column" : "row"} 
              spacing={isMobile ? 1 : 2} 
              sx={{ mt: 1 }}
            >
              <Button
                variant="contained"
                color="primary"
                onClick={handleValidateApiKeys}
                disabled={isGenerating || validatingKeys || (!googleApiKey.trim() && !pplxApiKey.trim())}
                startIcon={validatingKeys ? <CircularProgress size={20} color="inherit" /> : null}
                fullWidth={isMobile}
                size={isMobile ? "small" : "medium"}
              >
                {validatingKeys ? "Validating..." : "Validate API Keys"}
              </Button>
              
              <Button
                variant="outlined"
                color="secondary"
                onClick={handleClearApiKeys}
                disabled={isGenerating || (!googleApiKey && !pplxApiKey)}
                fullWidth={isMobile}
                size={isMobile ? "small" : "medium"}
              >
                Clear API Keys
              </Button>
            </Stack>
          </Grid>
        </Grid>
        
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="info.main" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
            Note: Your API keys are used only for your requests and are not stored on our servers unless you choose "Remember API keys".
          </Typography>
        </Box>
      </AccordionDetails>
    </Accordion>
  );
};

export default ApiKeySettings; 
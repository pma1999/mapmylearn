import React from 'react';
import {
  Typography,
  Box,
  TextField,
  Button,
  Paper,
  Grid,
  Stack,
  FormControlLabel,
  Checkbox,
  InputAdornment,
  IconButton,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import KeyIcon from '@mui/icons-material/Key';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

function ApiKeySettings({
  apiSettingsOpen,
  setApiSettingsOpen,
  openaiApiKey,
  setOpenaiApiKey,
  tavilyApiKey,
  setTavilyApiKey,
  showOpenaiKey,
  setShowOpenaiKey,
  showTavilyKey,
  setShowTavilyKey,
  rememberApiKeys,
  setRememberApiKeys,
  openaiKeyValid,
  setOpenaiKeyValid,
  tavilyKeyValid,
  setTavilyKeyValid,
  validatingKeys,
  isGenerating,
  handleValidateApiKeys,
  handleClearApiKeys
}) {
  return (
    <Accordion
      expanded={apiSettingsOpen}
      onChange={() => setApiSettingsOpen(!apiSettingsOpen)}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" spacing={1} alignItems="center">
          <KeyIcon color="primary" />
          <Typography variant="subtitle1" sx={{ fontWeight: 'medium' }}>
            API Key Settings
          </Typography>
          <Typography variant="caption" color="error">
            (Required)
          </Typography>
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <Typography variant="body2" paragraph>
          Please provide your API keys to use for generating learning paths. Both OpenAI and Tavily API keys are required.
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              label="OpenAI API Key"
              variant="outlined"
              fullWidth
              value={openaiApiKey}
              onChange={(e) => {
                setOpenaiApiKey(e.target.value);
                setOpenaiKeyValid(null);
              }}
              placeholder="sk-..."
              disabled={isGenerating}
              type={showOpenaiKey ? 'text' : 'password'}
              required
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowOpenaiKey(!showOpenaiKey)}
                      edge="end"
                    >
                      {showOpenaiKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                    {openaiKeyValid !== null && (
                      <Box ml={1}>
                        {openaiKeyValid ? 
                          <CheckCircleIcon color="success" /> : 
                          <ErrorIcon color="error" />
                        }
                      </Box>
                    )}
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 2 }}
            />
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              label="Tavily API Key"
              variant="outlined"
              fullWidth
              value={tavilyApiKey}
              onChange={(e) => {
                setTavilyApiKey(e.target.value);
                setTavilyKeyValid(null);
              }}
              placeholder="tvly-..."
              disabled={isGenerating}
              type={showTavilyKey ? 'text' : 'password'}
              required
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowTavilyKey(!showTavilyKey)}
                      edge="end"
                    >
                      {showTavilyKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                    {tavilyKeyValid !== null && (
                      <Box ml={1}>
                        {tavilyKeyValid ? 
                          <CheckCircleIcon color="success" /> : 
                          <ErrorIcon color="error" />
                        }
                      </Box>
                    )}
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 2 }}
            />
          </Grid>
          
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Checkbox 
                  checked={rememberApiKeys} 
                  onChange={(e) => setRememberApiKeys(e.target.checked)}
                  disabled={isGenerating}
                />
              }
              label="Remember API keys for this session"
            />
            <Typography variant="caption" color="text.secondary" display="block">
              Keys are stored in browser session storage and will be cleared when you close your browser.
            </Typography>
          </Grid>
          
          <Grid item xs={12}>
            <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
              <Button 
                variant="outlined" 
                onClick={handleValidateApiKeys}
                disabled={isGenerating || validatingKeys || (!openaiApiKey && !tavilyApiKey)}
                startIcon={validatingKeys ? <CircularProgress size={20} /> : null}
                color={openaiKeyValid === true && tavilyKeyValid === true ? "success" : "primary"}
              >
                {validatingKeys ? 'Validating...' : openaiKeyValid === true && tavilyKeyValid === true ? 'Keys Validated ✓' : 'Validate API Keys'}
              </Button>
              <Button 
                variant="outlined" 
                color="error" 
                onClick={handleClearApiKeys}
                disabled={isGenerating || (!openaiApiKey && !tavilyApiKey)}
              >
                Clear Keys
              </Button>
            </Stack>
          </Grid>
        </Grid>
      </AccordionDetails>
    </Accordion>
  );
}

export default ApiKeySettings; 
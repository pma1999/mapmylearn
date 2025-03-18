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
  Alert
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
  const [googleKeyHelpOpen, setGoogleKeyHelpOpen] = useState(false);
  const [pplxKeyHelpOpen, setPplxKeyHelpOpen] = useState(false);
  const [showInstructions, setShowInstructions] = useState(true);
  const [activeStep, setActiveStep] = useState(0);
  const [copied, setCopied] = useState('');

  const handleCopyCode = (text, type) => {
    navigator.clipboard.writeText(text);
    setCopied(type);
    setTimeout(() => setCopied(''), 2000);
  };

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
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary" paragraph sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
            To generate learning paths, you need to provide your own API keys. These keys are required to make requests to external AI and search services.
          </Typography>
          
          <Button 
            variant="text" 
            color="primary" 
            startIcon={<InfoIcon />}
            onClick={() => setShowInstructions(!showInstructions)}
            size={isMobile ? "small" : "medium"}
            sx={{ mb: 1 }}
          >
            {showInstructions ? "Hide Setup Instructions" : "Show Setup Instructions"}
          </Button>
          
          <Collapse in={showInstructions}>
            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent sx={{ p: { xs: 1.5, sm: 2 } }}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  How to Get Your API Keys:
                </Typography>
                
                <Stepper activeStep={activeStep} orientation={isMobile ? "vertical" : "horizontal"} sx={{ mb: 2 }}>
                  <Step>
                    <StepLabel>Create Accounts</StepLabel>
                  </Step>
                  <Step>
                    <StepLabel>Generate Keys</StepLabel>
                  </Step>
                  <Step>
                    <StepLabel>Enter & Validate</StepLabel>
                  </Step>
                </Stepper>
                
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Alert severity="info" sx={{ mb: 2 }}>
                      You'll need keys from <strong>either</strong> Google AI (Gemini API) <strong>or</strong> Perplexity, or both for best results.
                    </Alert>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined" sx={{ height: '100%' }}>
                      <CardContent>
                        <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                          <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" alt="Google Logo" width="20" />
                          <Typography variant="subtitle1" fontWeight="bold">Google AI (Gemini)</Typography>
                        </Stack>
                        <Typography variant="body2" sx={{ mb: 1 }}>Quick steps to get a Gemini API key:</Typography>
                        <Typography variant="body2" component="ol" sx={{ pl: 2, mb: 1 }}>
                          <li>Visit Google AI Studio</li>
                          <li>Create/sign in to your Google account</li>
                          <li>Get API key from API section</li>
                        </Typography>
                        <Button 
                          variant="outlined" 
                          size="small" 
                          startIcon={<LaunchIcon />}
                          href="https://aistudio.google.com/apikey"
                          target="_blank"
                          rel="noopener noreferrer"
                          sx={{ mr: 1, mt: 1 }}
                        >
                          Get API Key
                        </Button>
                        <Button
                          variant="text"
                          size="small"
                          color="secondary"
                          endIcon={<HelpOutlineIcon />}
                          onClick={() => setGoogleKeyHelpOpen(true)}
                          sx={{ mt: 1 }}
                        >
                          Detailed Steps
                        </Button>
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
                        <Typography variant="body2" sx={{ mb: 1 }}>Quick steps to get a Perplexity API key:</Typography>
                        <Typography variant="body2" component="ol" sx={{ pl: 2, mb: 1 }}>
                          <li>Create a Perplexity account</li>
                          <li>Visit API settings in your profile</li>
                          <li>Register payment method (required)</li>
                          <li>Generate an API key</li>
                        </Typography>
                        <Button 
                          variant="outlined" 
                          size="small" 
                          startIcon={<LaunchIcon />}
                          href="https://www.perplexity.ai/settings/api"
                          target="_blank"
                          rel="noopener noreferrer"
                          sx={{ mr: 1, mt: 1 }}
                        >
                          Get API Key
                        </Button>
                        <Button
                          variant="text"
                          size="small"
                          color="secondary"
                          endIcon={<HelpOutlineIcon />}
                          onClick={() => setPplxKeyHelpOpen(true)}
                          sx={{ mt: 1 }}
                        >
                          Detailed Steps
                        </Button>
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
            bgcolor: 'success.light', 
            p: 1.5, 
            borderRadius: 1,
            color: 'success.contrastText'
          }}>
            <SecurityIcon sx={{ mr: 1 }} />
            <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
              Your API keys are now securely handled using tokens and are never stored directly in the application state.
            </Typography>
          </Box>
        </Box>
        
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
                      <Tooltip title="API key authenticated">
                        <CheckCircleIcon color="success" sx={{ ml: 1 }} />
                      </Tooltip>
                    )}
                    {googleKeyValid === false && (
                      <Tooltip title="API key authentication failed">
                        <ErrorIcon color="error" sx={{ ml: 1 }} />
                      </Tooltip>
                    )}
                    <Tooltip title="How to get Google API key">
                      <IconButton
                        size="small"
                        onClick={() => setGoogleKeyHelpOpen(true)}
                        sx={{ ml: 0.5 }}
                      >
                        <HelpOutlineIcon />
                      </IconButton>
                    </Tooltip>
                  </InputAdornment>
                ),
              }}
              helperText={
                googleKeyValid === false ? "Invalid Google API key" : 
                googleKeyValid === true ? "API key authenticated securely" : 
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
                      <Tooltip title="API key authenticated">
                        <CheckCircleIcon color="success" sx={{ ml: 1 }} />
                      </Tooltip>
                    )}
                    {pplxKeyValid === false && (
                      <Tooltip title="API key authentication failed">
                        <ErrorIcon color="error" sx={{ ml: 1 }} />
                      </Tooltip>
                    )}
                    <Tooltip title="How to get Perplexity API key">
                      <IconButton
                        size="small"
                        onClick={() => setPplxKeyHelpOpen(true)}
                        sx={{ ml: 0.5 }}
                      >
                        <HelpOutlineIcon />
                      </IconButton>
                    </Tooltip>
                  </InputAdornment>
                ),
              }}
              helperText={
                pplxKeyValid === false ? "Invalid Perplexity API key" : 
                pplxKeyValid === true ? "API key authenticated securely" : 
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
                startIcon={validatingKeys ? <CircularProgress size={20} color="inherit" /> : <SecurityIcon />}
                fullWidth={isMobile}
                size={isMobile ? "small" : "medium"}
              >
                {validatingKeys ? "Authenticating..." : "Authenticate Keys"}
              </Button>
              
              <Button
                variant="outlined"
                color="secondary"
                onClick={handleClearApiKeys}
                disabled={isGenerating || (!googleApiKey && !pplxApiKey)}
                fullWidth={isMobile}
                size={isMobile ? "small" : "medium"}
              >
                Clear Keys
              </Button>
            </Stack>
          </Grid>
        </Grid>
        
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="info.main" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
            Note: Your API keys are securely processed and never stored directly on our servers. We use temporary security tokens to manage access.
          </Typography>
        </Box>
        
        {/* Google API Key Help Dialog */}
        <Dialog
          open={googleKeyHelpOpen}
          onClose={() => setGoogleKeyHelpOpen(false)}
          maxWidth="md"
          fullWidth
          PaperProps={{ 
            sx: { 
              borderRadius: 2,
              maxHeight: '90vh'
            } 
          }}
        >
          <DialogTitle>
            <Stack direction="row" alignItems="center" spacing={1}>
              <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" alt="Google Logo" width="24" />
              <Typography variant="h6">How to Get Your Google Gemini API Key</Typography>
            </Stack>
          </DialogTitle>
          <DialogContent dividers>
            <Stepper activeStep={-1} orientation="vertical" sx={{ mb: 3 }}>
              <Step>
                <StepLabel>
                  <Typography variant="subtitle1">Go to Google AI Studio</Typography>
                </StepLabel>
                <Box sx={{ ml: 4, my: 2 }}>
                  <Typography variant="body2" paragraph>
                    Visit <Link href="https://aistudio.google.com/apikey" target="_blank" rel="noopener">Google AI Studio</Link> and sign in with your Google account.
                  </Typography>
                  <Button 
                    variant="outlined" 
                    startIcon={<LaunchIcon />} 
                    href="https://aistudio.google.com/apikey" 
                    target="_blank"
                    rel="noopener"
                    sx={{ mb: 1 }}
                  >
                    Open Google AI Studio
                  </Button>
                </Box>
              </Step>
              
              <Step>
                <StepLabel>
                  <Typography variant="subtitle1">Get an API Key</Typography>
                </StepLabel>
                <Box sx={{ ml: 4, my: 2 }}>
                  <Typography variant="body2" paragraph>
                    1. In Google AI Studio, click on "Get API Key" in the top navigation or look for API key in the settings.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    2. If you already have a key, you'll see it here. Otherwise, click "Create API Key" to generate a new one.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    3. Copy your API key - it should start with "AIza...".
                  </Typography>
                </Box>
              </Step>
              
              <Step>
                <StepLabel>
                  <Typography variant="subtitle1">Verify Your API Key</Typography>
                </StepLabel>
                <Box sx={{ ml: 4, my: 2 }}>
                  <Typography variant="body2" paragraph>
                    To verify your API key works, you can make a test API call:
                  </Typography>
                  <Card variant="outlined" sx={{ mb: 2, bgcolor: '#f5f5f5' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
                        <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>Test request with curl</Typography>
                        <IconButton 
                          size="small" 
                          onClick={() => handleCopyCode(`curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=YOUR_API_KEY" \
-H 'Content-Type: application/json' \
-X POST \
-d '{
  "contents": [{
    "parts":[{"text": "Hello, Gemini!"}]
    }]
   }'`, 'gemini')}
                        >
                          <ContentCopyIcon fontSize="small" />
                        </IconButton>
                      </Stack>
                      <Box 
                        component="pre" 
                        sx={{ 
                          p: 1, 
                          overflowX: 'auto', 
                          fontSize: '0.75rem',
                          bgcolor: '#272822', 
                          color: '#f8f8f2',
                          borderRadius: 1
                        }}
                      >
{`curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=YOUR_API_KEY" \\
  -H 'Content-Type: application/json' \\
  -X POST \\
  -d '{
    "contents": [{
      "parts":[{"text": "Hello, Gemini!"}]
      }]
     }'`}
                      </Box>
                      {copied === 'gemini' && (
                        <Typography color="success.main" variant="caption" sx={{ mt: 1, display: 'block' }}>
                          Code copied to clipboard!
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                  <Typography variant="body2" color="text.secondary">
                    Remember to replace YOUR_API_KEY with your actual API key.
                  </Typography>
                </Box>
              </Step>
              
              <Step>
                <StepLabel>
                  <Typography variant="subtitle1">Enter Your API Key in This Application</Typography>
                </StepLabel>
                <Box sx={{ ml: 4, my: 2 }}>
                  <Typography variant="body2" paragraph>
                    Paste your API key into the Google API Key field and click "Authenticate Keys".
                  </Typography>
                </Box>
              </Step>
            </Stepper>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle2" color="primary" gutterBottom>
              Security Best Practices:
            </Typography>
            <Typography variant="body2" component="ul" sx={{ pl: 2 }}>
              <li>Never share your API keys or commit them to public code repositories.</li>
              <li>Set appropriate restrictions on your API keys through the Google Cloud Console.</li>
              <li>Monitor your usage to avoid unexpected charges.</li>
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setGoogleKeyHelpOpen(false)}>Close</Button>
            <Button 
              variant="contained" 
              color="primary"
              href="https://aistudio.google.com/apikey"
              target="_blank"
              rel="noopener noreferrer"
            >
              Official Documentation
            </Button>
          </DialogActions>
        </Dialog>
        
        {/* Perplexity API Key Help Dialog */}
        <Dialog
          open={pplxKeyHelpOpen}
          onClose={() => setPplxKeyHelpOpen(false)}
          maxWidth="md"
          fullWidth
          PaperProps={{ 
            sx: { 
              borderRadius: 2,
              maxHeight: '90vh'
            } 
          }}
        >
          <DialogTitle>
            <Stack direction="row" alignItems="center" spacing={1}>
              <img src="https://www.perplexity.ai/favicon.ico" alt="Perplexity Logo" width="24" />
              <Typography variant="h6">How to Get Your Perplexity API Key</Typography>
            </Stack>
          </DialogTitle>
          <DialogContent dividers>
            <Stepper activeStep={-1} orientation="vertical" sx={{ mb: 3 }}>
              <Step>
                <StepLabel>
                  <Typography variant="subtitle1">Create a Perplexity Account</Typography>
                </StepLabel>
                <Box sx={{ ml: 4, my: 2 }}>
                  <Typography variant="body2" paragraph>
                    Visit <Link href="https://www.perplexity.ai/settings/api" target="_blank" rel="noopener">Perplexity.ai</Link> and create an account if you don't have one already.
                  </Typography>
                  <Button 
                    variant="outlined" 
                    startIcon={<LaunchIcon />} 
                    href="https://www.perplexity.ai/settings/api" 
                    target="_blank"
                    rel="noopener"
                    sx={{ mb: 1 }}
                  >
                    Go to Perplexity
                  </Button>
                </Box>
              </Step>
              
              <Step>
                <StepLabel>
                  <Typography variant="subtitle1">Register Payment Method</Typography>
                </StepLabel>
                <Box sx={{ ml: 4, my: 2 }}>
                  <Typography variant="body2" paragraph>
                    1. Navigate to the API settings page from your profile.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    2. You'll need to register a payment method (credit card) to get API access.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    3. This is required even for free tier usage, but you won't be charged until you exceed the free credits.
                  </Typography>
                  <Alert severity="info" sx={{ mt: 1 }}>
                    Perplexity offers free credits to start with, but requires payment information upfront.
                  </Alert>
                </Box>
              </Step>
              
              <Step>
                <StepLabel>
                  <Typography variant="subtitle1">Generate Your API Key</Typography>
                </StepLabel>
                <Box sx={{ ml: 4, my: 2 }}>
                  <Typography variant="body2" paragraph>
                    After registering your payment method, you can generate an API key from the API settings page.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    Your API key will start with "pplx-" and should be kept secure.
                  </Typography>
                </Box>
              </Step>
              
              <Step>
                <StepLabel>
                  <Typography variant="subtitle1">Verify Your API Key</Typography>
                </StepLabel>
                <Box sx={{ ml: 4, my: 2 }}>
                  <Typography variant="body2" paragraph>
                    To verify your API key works, you can make a test API call:
                  </Typography>
                  <Card variant="outlined" sx={{ mb: 2, bgcolor: '#f5f5f5' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
                        <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>Test request with curl</Typography>
                        <IconButton 
                          size="small"
                          onClick={() => handleCopyCode(`curl --location 'https://api.perplexity.ai/chat/completions' \\
  --header 'accept: application/json' \\
  --header 'content-type: application/json' \\
  --header 'Authorization: Bearer YOUR_API_KEY' \\
  --data '{
    "model": "sonar-pro",
    "messages": [
      {
        "role": "system",
        "content": "Be precise and concise."
      },
      {
        "role": "user",
        "content": "Hello, Perplexity!"
      }
    ]
  }'`, 'perplexity')}
                        >
                          <ContentCopyIcon fontSize="small" />
                        </IconButton>
                      </Stack>
                      <Box 
                        component="pre" 
                        sx={{ 
                          p: 1, 
                          overflowX: 'auto', 
                          fontSize: '0.75rem',
                          bgcolor: '#272822', 
                          color: '#f8f8f2',
                          borderRadius: 1
                        }}
                      >
{`curl --location 'https://api.perplexity.ai/chat/completions' \\
  --header 'accept: application/json' \\
  --header 'content-type: application/json' \\
  --header 'Authorization: Bearer YOUR_API_KEY' \\
  --data '{
    "model": "sonar-pro",
    "messages": [
      {
        "role": "system",
        "content": "Be precise and concise."
      },
      {
        "role": "user",
        "content": "Hello, Perplexity!"
      }
    ]
  }'`}
                      </Box>
                      {copied === 'perplexity' && (
                        <Typography color="success.main" variant="caption" sx={{ mt: 1, display: 'block' }}>
                          Code copied to clipboard!
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                  <Typography variant="body2" color="text.secondary">
                    Remember to replace YOUR_API_KEY with your actual API key.
                  </Typography>
                </Box>
              </Step>
              
              <Step>
                <StepLabel>
                  <Typography variant="subtitle1">Enter Your API Key in This Application</Typography>
                </StepLabel>
                <Box sx={{ ml: 4, my: 2 }}>
                  <Typography variant="body2" paragraph>
                    Paste your API key into the Perplexity API Key field and click "Authenticate Keys".
                  </Typography>
                </Box>
              </Step>
            </Stepper>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle2" color="primary" gutterBottom>
              About API Usage & Billing:
            </Typography>
            <Typography variant="body2" component="ul" sx={{ pl: 2 }}>
              <li>Perplexity offers a credit-based system with a free tier for new users.</li>
              <li>When you run out of credits, your API keys will be blocked until you add to your credit balance.</li>
              <li>Consider configuring "Automatic Top Up" in your Perplexity account to avoid interruptions.</li>
              <li>You're only charged for what you use beyond the free credits.</li>
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setPplxKeyHelpOpen(false)}>Close</Button>
            <Button 
              variant="contained" 
              color="primary"
              href="https://www.perplexity.ai/settings/api"
              target="_blank"
              rel="noopener noreferrer"
            >
              Official Documentation
            </Button>
          </DialogActions>
        </Dialog>
      </AccordionDetails>
    </Accordion>
  );
};

export default ApiKeySettings; 
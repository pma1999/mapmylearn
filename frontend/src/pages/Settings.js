import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Divider,
  Grid,
  FormControlLabel,
  Switch,
  Card,
  CardContent,
  Link,
  Alert,
  InputAdornment,
  IconButton,
  CircularProgress,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Save as SaveIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import { useSettings } from '../contexts/SettingsContext';

const Settings = ({ showNotification }) => {
  const { settings, apiKeys, updateApiKeys, updateSettings, loading } = useSettings();
  
  const [formKeys, setFormKeys] = useState({
    openaiApiKey: '',
    tavilyApiKey: '',
  });
  
  const [showOpenAIKey, setShowOpenAIKey] = useState(false);
  const [showTavilyKey, setShowTavilyKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  
  const handleFormKeyChange = (e) => {
    const { name, value } = e.target;
    setFormKeys({
      ...formKeys,
      [name]: value,
    });
    
    // Clear statuses
    setError(null);
    setSuccess(false);
  };
  
  const handleToggleOpenAIKey = () => {
    setShowOpenAIKey(!showOpenAIKey);
  };
  
  const handleToggleTavilyKey = () => {
    setShowTavilyKey(!showTavilyKey);
  };
  
  const handleSaveApiKeys = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);
      
      const result = await updateApiKeys({
        openaiApiKey: formKeys.openaiApiKey,
        tavilyApiKey: formKeys.tavilyApiKey,
      });
      
      if (result.success) {
        setSuccess(true);
        showNotification('Claves API guardadas correctamente', 'success');
        setFormKeys({
          openaiApiKey: '',
          tavilyApiKey: '',
        });
      } else {
        setError(result.error || 'Error al guardar las claves API');
        showNotification('Error al guardar las claves API', 'error');
      }
    } catch (err) {
      setError(err.message || 'Error inesperado al guardar las claves API');
      showNotification('Error inesperado al guardar las claves API', 'error');
    } finally {
      setSaving(false);
    }
  };
  
  const handleToggleDarkMode = () => {
    updateSettings({ darkMode: !settings.darkMode });
    showNotification('Configuración guardada', 'info');
  };
  
  return (
    <Box className="content-container">
      <Typography variant="h4" component="h1" gutterBottom>
        Configuración
      </Typography>
      
      <Grid container spacing={4}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, mb: 4 }}>
            <Typography variant="h5" gutterBottom>
              Claves API
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Las claves API son necesarias para la generación de rutas de aprendizaje.
            </Typography>
            
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            {success && (
              <Alert severity="success" sx={{ mb: 2 }}>
                Claves API actualizadas correctamente
              </Alert>
            )}
            
            <Box sx={{ mb: 3 }}>
              <TextField
                label="OpenAI API Key"
                name="openaiApiKey"
                value={formKeys.openaiApiKey}
                onChange={handleFormKeyChange}
                type={showOpenAIKey ? 'text' : 'password'}
                fullWidth
                margin="normal"
                placeholder={settings.openaiApiKeySet ? "••••••••••••••••••••••••••••••" : "sk-..."}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle key visibility"
                        onClick={handleToggleOpenAIKey}
                        edge="end"
                      >
                        {showOpenAIKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
              
              <TextField
                label="Tavily API Key"
                name="tavilyApiKey"
                value={formKeys.tavilyApiKey}
                onChange={handleFormKeyChange}
                type={showTavilyKey ? 'text' : 'password'}
                fullWidth
                margin="normal"
                placeholder={settings.tavilyApiKeySet ? "••••••••••••••••••••••••••••••" : "tvly-..."}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle key visibility"
                        onClick={handleToggleTavilyKey}
                        edge="end"
                      >
                        {showTavilyKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Button
                variant="contained"
                color="primary"
                startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
                onClick={handleSaveApiKeys}
                disabled={saving || (!formKeys.openaiApiKey && !formKeys.tavilyApiKey)}
              >
                {saving ? 'Guardando...' : 'Guardar Claves API'}
              </Button>
              
              <Box sx={{ ml: 2, display: 'flex', alignItems: 'center' }}>
                {settings.openaiApiKeySet && (
                  <Typography variant="body2" color="success.main" sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
                    <CheckIcon fontSize="small" sx={{ mr: 0.5 }} />
                    OpenAI
                  </Typography>
                )}
                
                {settings.tavilyApiKeySet && (
                  <Typography variant="body2" color="success.main" sx={{ display: 'flex', alignItems: 'center' }}>
                    <CheckIcon fontSize="small" sx={{ mr: 0.5 }} />
                    Tavily
                  </Typography>
                )}
              </Box>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, mb: 4 }}>
            <Typography variant="h5" gutterBottom>
              Preferencias de la Aplicación
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.darkMode}
                    onChange={handleToggleDarkMode}
                    color="primary"
                  />
                }
                label="Modo Oscuro"
              />
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle1" gutterBottom>
              Configuración Predeterminada de Generación
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Estos valores se usarán como predeterminados al generar nuevas rutas de aprendizaje.
            </Typography>
            
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2">Módulos en paralelo:</Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {settings.parallelCount}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">Búsquedas en paralelo:</Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {settings.searchParallelCount}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">Submódulos en paralelo:</Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {settings.submoduleParallelCount}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">Guardar automáticamente:</Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {settings.saveToHistory ? 'Sí' : 'No'}
                  </Typography>
                </Grid>
              </Grid>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Estos valores se pueden ajustar en la página del generador antes de cada generación.
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
      
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Información de API
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom>
            OpenAI API
          </Typography>
          <Typography variant="body2" paragraph>
            La API de OpenAI se utiliza para la generación de texto y el procesamiento del lenguaje natural.
            Puedes obtener una clave API en{' '}
            <Link href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer">
              platform.openai.com/api-keys
            </Link>
          </Typography>
          
          <Typography variant="subtitle1" gutterBottom>
            Tavily API
          </Typography>
          <Typography variant="body2" paragraph>
            La API de Tavily se utiliza para realizar búsquedas web para obtener información actualizada.
            Puedes obtener una clave API en{' '}
            <Link href="https://tavily.com/" target="_blank" rel="noopener noreferrer">
              tavily.com
            </Link>
          </Typography>
          
          <Alert severity="info" sx={{ mt: 2 }}>
            Las claves API se almacenan de forma segura en el backend y no se comparten con terceros.
          </Alert>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Settings; 
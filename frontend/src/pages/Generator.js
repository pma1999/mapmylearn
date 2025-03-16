import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Card,
  CardContent,
  Divider,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Slider,
  CircularProgress,
  Alert,
  FormControlLabel,
  Switch,
  InputAdornment,
  IconButton,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Send as SendIcon,
  School as SchoolIcon,
  Settings as SettingsIcon,
  Close as CloseIcon,
  CloudUpload as CloudUploadIcon,
  Download as DownloadIcon,
  Bookmark as BookmarkIcon,
} from '@mui/icons-material';
import { useSettings } from '../contexts/SettingsContext';
import { generateLearningPath, startGeneration, createWebSocketConnection } from '../services/api';

const Generator = ({ showNotification }) => {
  const navigate = useNavigate();
  const [topic, setTopic] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState([]);
  const [learningPath, setLearningPath] = useState(null);
  const [connectionId, setConnectionId] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [socketStatus, setSocketStatus] = useState('disconnected');
  const [generationError, setGenerationError] = useState(null);
  const socketRef = useRef(null);
  const progressEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const { settings, updateSettings } = useSettings();

  // Auto scroll to bottom of progress logs
  useEffect(() => {
    if (progressEndRef.current) {
      progressEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [progress]);

  // Clean up WebSocket on component unmount
  useEffect(() => {
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  const handleTopicChange = (event) => {
    setTopic(event.target.value);
  };

  const handleParallelCountChange = (event, newValue) => {
    updateSettings({ parallelCount: newValue });
  };

  const handleSearchParallelCountChange = (event, newValue) => {
    updateSettings({ searchParallelCount: newValue });
  };

  const handleSubmoduleParallelCountChange = (event, newValue) => {
    updateSettings({ submoduleParallelCount: newValue });
  };

  const handleSaveToHistoryChange = (event) => {
    updateSettings({ saveToHistory: event.target.checked });
  };

  const handleGenerateClick = async () => {
    if (!topic.trim()) {
      showNotification('Por favor ingresa un tema para la ruta de aprendizaje', 'warning');
      return;
    }

    try {
      setIsGenerating(true);
      setProgress([]);
      setLearningPath(null);
      setGenerationError(null);
      setSocketStatus('connecting');

      // Get connection ID from API
      const response = await generateLearningPath({
        topic: topic,
        parallel_count: settings.parallelCount,
        search_parallel_count: settings.searchParallelCount,
        submodule_parallel_count: settings.submoduleParallelCount,
        save_to_history: settings.saveToHistory,
      });

      if (!response.connection_id) {
        throw new Error('No se recibió un ID de conexión.');
      }

      const connId = response.connection_id;
      setConnectionId(connId);

      // Create WebSocket connection
      const socket = createWebSocketConnection(
        connId,
        handleWebSocketMessage,
        handleWebSocketClose,
        handleWebSocketError
      );

      socketRef.current = socket;

      // Start generation when socket is open
      socket.onopen = async () => {
        setSocketStatus('connected');
        setProgress(prev => [...prev, 'Conexión establecida. Iniciando generación...']);
        
        // Start the generation process
        await startGeneration(connId, {
          topic: topic,
          parallel_count: settings.parallelCount,
          search_parallel_count: settings.searchParallelCount,
          submodule_parallel_count: settings.submoduleParallelCount,
          save_to_history: settings.saveToHistory,
        });
      };
    } catch (error) {
      console.error('Error starting generation:', error);
      setGenerationError(
        error.error || 'Error al iniciar la generación. Por favor intenta de nuevo.'
      );
      setIsGenerating(false);
      setSocketStatus('disconnected');
      showNotification('Error al iniciar la generación', 'error');
    }
  };

  const handleWebSocketMessage = (data) => {
    console.log('WebSocket message:', data);
    
    if (data.type === 'progress' && data.message) {
      setProgress(prev => [...prev, data.message]);
    } 
    else if (data.type === 'complete' && data.result) {
      setLearningPath(data.result);
      setIsGenerating(false);
      setSocketStatus('completed');
      showNotification('¡Ruta de aprendizaje generada con éxito!', 'success');
    } 
    else if (data.type === 'error') {
      setGenerationError(data.message || 'Error durante la generación.');
      setIsGenerating(false);
      setSocketStatus('error');
      showNotification('Error durante la generación', 'error');
    }
  };

  const handleWebSocketClose = (event) => {
    console.log('WebSocket closed:', event);
    
    if (socketStatus !== 'completed' && socketStatus !== 'error') {
      setSocketStatus('disconnected');
      
      if (isGenerating) {
        setIsGenerating(false);
        setGenerationError('Conexión cerrada inesperadamente.');
        showNotification('Conexión cerrada inesperadamente', 'error');
      }
    }
  };

  const handleWebSocketError = (error) => {
    console.error('WebSocket error:', error);
    setSocketStatus('error');
    setIsGenerating(false);
    setGenerationError('Error en la conexión WebSocket.');
    showNotification('Error en la conexión', 'error');
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setUploadedFile(file);
      
      // Read file to preview
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const content = JSON.parse(e.target.result);
          if (content.topic && content.modules) {
            setLearningPath(content);
            showNotification('Archivo JSON cargado correctamente', 'success');
          } else {
            setUploadedFile(null);
            showNotification('El archivo no tiene el formato correcto de ruta de aprendizaje', 'error');
          }
        } catch (error) {
          setUploadedFile(null);
          showNotification('Error al leer el archivo JSON', 'error');
        }
      };
      reader.readAsText(file);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  const clearUploadedFile = () => {
    setUploadedFile(null);
    setLearningPath(null);
    fileInputRef.current.value = '';
  };

  const downloadLearningPath = () => {
    if (!learningPath) return;
    
    const jsonContent = JSON.stringify(learningPath, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `learning_path_${learningPath.topic.replace(/\s+/g, '_')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const renderProgressLog = () => {
    return (
      <Box sx={{ mt: 3, mb: 3 }}>
        <Paper
          sx={{
            p: 2,
            maxHeight: '250px',
            overflowY: 'auto',
            bgcolor: '#f5f5f5',
            borderRadius: 1,
            boxShadow: 1,
          }}
        >
          <Typography variant="subtitle1" gutterBottom>
            Progreso:
          </Typography>
          {progress.length === 0 ? (
            <Typography variant="body2" color="textSecondary">
              Esperando inicio de generación...
            </Typography>
          ) : (
            progress.map((msg, idx) => (
              <Typography
                key={idx}
                variant="body2"
                sx={{ py: 0.5, borderBottom: idx !== progress.length - 1 ? '1px dotted #e0e0e0' : '' }}
              >
                {'> '}{msg}
              </Typography>
            ))
          )}
          <div ref={progressEndRef} />
        </Paper>
      </Box>
    );
  };

  const renderLearningPath = () => {
    if (!learningPath) return null;

    return (
      <Box sx={{ mt: 4, mb: 2 }}>
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h5" component="h2">
                Ruta de Aprendizaje: {learningPath.topic}
              </Typography>
              <Box>
                <Button
                  startIcon={<DownloadIcon />}
                  variant="outlined"
                  size="small"
                  onClick={downloadLearningPath}
                >
                  Descargar JSON
                </Button>
                {settings.saveToHistory && (
                  <Button
                    startIcon={<BookmarkIcon />}
                    variant="text"
                    size="small"
                    onClick={() => navigate('/history')}
                    sx={{ ml: 1 }}
                  >
                    Ver en Historial
                  </Button>
                )}
              </Box>
            </Box>
            <Divider sx={{ mb: 2 }} />
            {learningPath.modules && learningPath.modules.length > 0 ? (
              learningPath.modules.map((module, index) => (
                <Accordion key={index} sx={{ mb: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">
                      Módulo {index + 1}: {module.title}
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body1" paragraph>
                      {module.description}
                    </Typography>
                    {module.submodules && module.submodules.length > 0 ? (
                      module.submodules.map((submodule, subIndex) => (
                        <Accordion key={subIndex} sx={{ mb: 1 }}>
                          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography>
                              Submódulo {subIndex + 1}: {submodule.title}
                            </Typography>
                          </AccordionSummary>
                          <AccordionDetails>
                            <Typography variant="body2" paragraph>
                              {submodule.description}
                            </Typography>
                            {submodule.content ? (
                              <Typography
                                variant="body2"
                                component="div"
                                className="markdown-content"
                                sx={{ mt: 2 }}
                              >
                                {submodule.content.split('\n').map((line, i) => (
                                  <div key={i}>{line || <br />}</div>
                                ))}
                              </Typography>
                            ) : (
                              <Alert severity="warning">No hay contenido disponible</Alert>
                            )}
                          </AccordionDetails>
                        </Accordion>
                      ))
                    ) : (
                      module.content ? (
                        <Typography
                          variant="body2"
                          component="div"
                          className="markdown-content"
                        >
                          {module.content.split('\n').map((line, i) => (
                            <div key={i}>{line || <br />}</div>
                          ))}
                        </Typography>
                      ) : (
                        <Alert severity="warning">No hay submódulos ni contenido disponible</Alert>
                      )
                    )}
                  </AccordionDetails>
                </Accordion>
              ))
            ) : (
              <Alert severity="info">No se encontraron módulos en esta ruta de aprendizaje</Alert>
            )}
          </CardContent>
        </Card>
      </Box>
    );
  };

  const renderFileUpload = () => {
    return (
      <Box sx={{ mt: 3 }}>
        <Paper sx={{ p: 2, backgroundColor: 'background.paper', borderRadius: 1 }}>
          <Typography variant="subtitle1" gutterBottom>
            Importar Ruta de Aprendizaje
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
            <input
              type="file"
              accept=".json"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
              ref={fileInputRef}
            />
            <Button
              variant="outlined"
              startIcon={<CloudUploadIcon />}
              onClick={triggerFileInput}
              disabled={isGenerating}
            >
              Seleccionar Archivo JSON
            </Button>
            {uploadedFile && (
              <Box sx={{ display: 'flex', alignItems: 'center', ml: 2 }}>
                <Typography variant="body2" sx={{ mr: 1 }}>
                  {uploadedFile.name}
                </Typography>
                <IconButton size="small" onClick={clearUploadedFile}>
                  <CloseIcon fontSize="small" />
                </IconButton>
              </Box>
            )}
          </Box>
        </Paper>
      </Box>
    );
  };

  return (
    <Box className="content-container">
      <Typography variant="h4" component="h1" gutterBottom sx={{ mt: 2 }}>
        Generador de Rutas de Aprendizaje
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4, maxWidth: 800, mx: 'auto' }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 3 }}>
          <SchoolIcon sx={{ mr: 2, mt: 2, color: 'primary.main' }} />
          <TextField
            label="Tema de la ruta de aprendizaje"
            variant="outlined"
            fullWidth
            value={topic}
            onChange={handleTopicChange}
            placeholder="Ej: Inteligencia Artificial para principiantes"
            disabled={isGenerating}
            InputProps={{
              endAdornment: topic && (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setTopic('')}
                    edge="end"
                    size="small"
                  >
                    <CloseIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        </Box>

        <Typography variant="subtitle1" gutterBottom sx={{ mt: 2, display: 'flex', alignItems: 'center' }}>
          <SettingsIcon fontSize="small" sx={{ mr: 1 }} />
          Configuración Avanzada
        </Typography>

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Typography id="parallel-modules-slider" gutterBottom>
              Módulos en paralelo: {settings.parallelCount}
            </Typography>
            <Slider
              value={settings.parallelCount}
              onChange={handleParallelCountChange}
              aria-labelledby="parallel-modules-slider"
              valueLabelDisplay="auto"
              step={1}
              marks
              min={1}
              max={5}
              disabled={isGenerating}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography id="search-parallel-slider" gutterBottom>
              Búsquedas en paralelo: {settings.searchParallelCount}
            </Typography>
            <Slider
              value={settings.searchParallelCount}
              onChange={handleSearchParallelCountChange}
              aria-labelledby="search-parallel-slider"
              valueLabelDisplay="auto"
              step={1}
              marks
              min={1}
              max={5}
              disabled={isGenerating}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography id="submodule-parallel-slider" gutterBottom>
              Submódulos en paralelo: {settings.submoduleParallelCount}
            </Typography>
            <Slider
              value={settings.submoduleParallelCount}
              onChange={handleSubmoduleParallelCountChange}
              aria-labelledby="submodule-parallel-slider"
              valueLabelDisplay="auto"
              step={1}
              marks
              min={1}
              max={5}
              disabled={isGenerating}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.saveToHistory}
                  onChange={handleSaveToHistoryChange}
                  disabled={isGenerating}
                  color="primary"
                />
              }
              label="Guardar automáticamente en historial"
            />
          </Grid>
        </Grid>

        <Divider sx={{ my: 3 }} />

        {generationError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {generationError}
          </Alert>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={isGenerating ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
            onClick={handleGenerateClick}
            disabled={isGenerating || !topic.trim() || !settings.openaiApiKeySet || !settings.tavilyApiKeySet}
            size="large"
          >
            {isGenerating ? 'Generando...' : 'Generar Ruta de Aprendizaje'}
          </Button>

          {(!settings.openaiApiKeySet || !settings.tavilyApiKeySet) && (
            <Button
              variant="outlined"
              color="secondary"
              startIcon={<SettingsIcon />}
              onClick={() => navigate('/settings')}
            >
              Configurar API Keys
            </Button>
          )}
        </Box>

        {isGenerating && (
          <Box sx={{ width: '100%', mt: 2 }}>
            <LinearProgress />
          </Box>
        )}
      </Paper>

      {isGenerating && renderProgressLog()}
      
      {renderLearningPath()}

      {!isGenerating && !learningPath && renderFileUpload()}
    </Box>
  );
};

export default Generator; 
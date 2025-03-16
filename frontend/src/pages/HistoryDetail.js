import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  IconButton,
  Grid,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Divider,
  CircularProgress,
  Link,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Card,
  CardContent,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ArrowBack as ArrowBackIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Label as LabelIcon,
  AddCircleOutline as AddCircleOutlineIcon,
} from '@mui/icons-material';
import { formatDate } from '../utils/dateUtils';
import * as api from '../services/api';

const HistoryDetail = ({ showNotification }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [learningPath, setLearningPath] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [expandedModules, setExpandedModules] = useState({});
  const [tagDialogOpen, setTagDialogOpen] = useState(false);
  const [newTag, setNewTag] = useState('');
  
  useEffect(() => {
    loadLearningPath();
  }, [id]);
  
  const loadLearningPath = async () => {
    try {
      setLoading(true);
      const data = await api.getHistoryItem(id);
      setLearningPath(data);
      
      // Initialize expanded state for modules
      const initialExpandedState = {};
      if (data.learning_path && data.learning_path.modules) {
        data.learning_path.modules.forEach((_, index) => {
          initialExpandedState[index] = false;
        });
      }
      setExpandedModules(initialExpandedState);
      
      setError(null);
    } catch (err) {
      console.error('Error loading learning path:', err);
      setError('No se pudo cargar la ruta de aprendizaje. Por favor, inténtalo de nuevo más tarde.');
      showNotification('Error al cargar la ruta de aprendizaje', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
  };
  
  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false);
  };
  
  const handleConfirmDelete = async () => {
    try {
      await api.deleteHistoryItem(id);
      showNotification('Ruta de aprendizaje eliminada correctamente', 'success');
      navigate('/history');
    } catch (err) {
      console.error('Error deleting learning path:', err);
      showNotification('Error al eliminar la ruta de aprendizaje', 'error');
      handleCloseDeleteDialog();
    }
  };
  
  const handleFavoriteToggle = async () => {
    if (!learningPath) return;
    
    try {
      const newFavoriteState = !learningPath.is_favorite;
      await api.updateHistoryItemFavorite(id, newFavoriteState);
      setLearningPath({
        ...learningPath,
        is_favorite: newFavoriteState,
      });
      
      showNotification(
        `Ruta de aprendizaje ${newFavoriteState ? 'marcada como favorita' : 'desmarcada como favorita'}`,
        'success'
      );
    } catch (err) {
      console.error('Error updating favorite status:', err);
      showNotification('Error al actualizar el estado de favorito', 'error');
    }
  };
  
  const handleModuleExpand = (index) => {
    setExpandedModules({
      ...expandedModules,
      [index]: !expandedModules[index],
    });
  };
  
  const handleOpenTagDialog = () => {
    setTagDialogOpen(true);
    setNewTag('');
  };
  
  const handleCloseTagDialog = () => {
    setTagDialogOpen(false);
    setNewTag('');
  };
  
  const handleNewTagChange = (e) => {
    setNewTag(e.target.value);
  };
  
  const handleAddTag = async () => {
    if (!newTag.trim() || !learningPath) return;
    
    try {
      const currentTags = learningPath.tags || [];
      
      if (currentTags.includes(newTag.trim())) {
        showNotification('Esta etiqueta ya existe para esta ruta de aprendizaje', 'warning');
        return;
      }
      
      const updatedTags = [...currentTags, newTag.trim()];
      
      await api.updateHistoryItemTags(id, updatedTags);
      
      setLearningPath({
        ...learningPath,
        tags: updatedTags,
      });
      
      setNewTag('');
      handleCloseTagDialog();
      showNotification('Etiqueta añadida correctamente', 'success');
    } catch (err) {
      console.error('Error adding tag:', err);
      showNotification('Error al añadir la etiqueta', 'error');
    }
  };
  
  const handleRemoveTag = async (tagToRemove) => {
    if (!learningPath) return;
    
    try {
      const updatedTags = (learningPath.tags || []).filter(tag => tag !== tagToRemove);
      
      await api.updateHistoryItemTags(id, updatedTags);
      
      setLearningPath({
        ...learningPath,
        tags: updatedTags,
      });
      
      showNotification('Etiqueta eliminada correctamente', 'success');
    } catch (err) {
      console.error('Error removing tag:', err);
      showNotification('Error al eliminar la etiqueta', 'error');
    }
  };
  
  const handleDownload = async () => {
    if (!learningPath) return;
    
    try {
      // Create a blob from the learning path data
      const blob = new Blob([JSON.stringify(learningPath.learning_path, null, 2)], { type: 'application/json' });
      
      // Create a sanitized filename
      const sanitizedTopic = learningPath.topic.replace(/[^a-z0-9]/gi, '_').toLowerCase();
      const filename = `learning_path_${sanitizedTopic}_${id}.json`;
      
      // Create a download link and trigger the download
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      showNotification('Ruta de aprendizaje descargada correctamente', 'success');
    } catch (err) {
      console.error('Error downloading learning path:', err);
      showNotification('Error al descargar la ruta de aprendizaje', 'error');
    }
  };
  
  const renderLearningPathContent = () => {
    if (!learningPath || !learningPath.learning_path) return null;
    
    const path = learningPath.learning_path;
    
    return (
      <>
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            Descripción General
          </Typography>
          <Typography variant="body1" paragraph>
            {path.description || 'No hay descripción disponible.'}
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="subtitle2">Fecha de Creación</Typography>
              <Typography variant="body2">
                {formatDate(learningPath.created_at, true)}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="subtitle2">Módulos</Typography>
              <Typography variant="body2">
                {path.modules ? path.modules.length : 0}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="subtitle2">Submódulos Totales</Typography>
              <Typography variant="body2">
                {learningPath.submodules_count || 0}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="subtitle2">Duración Estimada</Typography>
              <Typography variant="body2">
                {path.estimated_time || 'No especificada'}
              </Typography>
            </Grid>
          </Grid>
          
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Etiquetas
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {(learningPath.tags || []).length > 0 ? (
                (learningPath.tags || []).map((tag, index) => (
                  <Chip
                    key={`${tag}-${index}`}
                    label={tag}
                    onDelete={() => handleRemoveTag(tag)}
                    size="small"
                  />
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No hay etiquetas
                </Typography>
              )}
              <Chip
                icon={<AddCircleOutlineIcon />}
                label="Añadir etiqueta"
                onClick={handleOpenTagDialog}
                variant="outlined"
                size="small"
                sx={{ borderStyle: 'dashed' }}
              />
            </Box>
          </Box>
        </Paper>
        
        <Typography variant="h5" gutterBottom>
          Contenido de la Ruta de Aprendizaje
        </Typography>
        
        {path.modules && path.modules.length > 0 ? (
          path.modules.map((module, moduleIndex) => (
            <Accordion
              key={`module-${moduleIndex}`}
              expanded={expandedModules[moduleIndex]}
              onChange={() => handleModuleExpand(moduleIndex)}
              sx={{ mb: 2 }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                aria-controls={`module-${moduleIndex}-content`}
                id={`module-${moduleIndex}-header`}
              >
                <Box sx={{ width: '100%' }}>
                  <Typography variant="subtitle1" fontWeight="bold">
                    {module.number}. {module.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {module.submodules ? `${module.submodules.length} submódulos` : 'Sin submódulos'}
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body1" paragraph>
                  {module.description || 'No hay descripción disponible.'}
                </Typography>
                
                {module.submodules && module.submodules.length > 0 ? (
                  <List disablePadding>
                    {module.submodules.map((submodule, subIndex) => (
                      <React.Fragment key={`submodule-${moduleIndex}-${subIndex}`}>
                        <ListItem
                          sx={{
                            flexDirection: 'column',
                            alignItems: 'flex-start',
                            py: 1,
                          }}
                        >
                          <Box sx={{ width: '100%', display: 'flex', mb: 1 }}>
                            <Typography variant="subtitle2" fontWeight="medium">
                              {module.number}.{subIndex + 1} {submodule.title}
                            </Typography>
                          </Box>
                          
                          <Typography variant="body2" sx={{ width: '100%' }}>
                            {submodule.description || 'No hay descripción disponible.'}
                          </Typography>
                          
                          {submodule.resources && submodule.resources.length > 0 && (
                            <Box sx={{ mt: 1, width: '100%' }}>
                              <Typography variant="body2" fontWeight="medium">
                                Recursos:
                              </Typography>
                              <Box component="ul" sx={{ mt: 0.5, pl: 2 }}>
                                {submodule.resources.map((resource, resIndex) => (
                                  <Box component="li" key={`resource-${moduleIndex}-${subIndex}-${resIndex}`}>
                                    {resource.url ? (
                                      <Link
                                        href={resource.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        underline="hover"
                                      >
                                        {resource.title || resource.url}
                                      </Link>
                                    ) : (
                                      <Typography variant="body2">
                                        {resource.title}
                                      </Typography>
                                    )}
                                    {resource.description && (
                                      <Typography variant="body2" color="text.secondary">
                                        {resource.description}
                                      </Typography>
                                    )}
                                  </Box>
                                ))}
                              </Box>
                            </Box>
                          )}
                        </ListItem>
                        {subIndex < module.submodules.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No hay submódulos disponibles.
                  </Typography>
                )}
              </AccordionDetails>
            </Accordion>
          ))
        ) : (
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography color="text.secondary">
              No hay módulos disponibles en esta ruta de aprendizaje.
            </Typography>
          </Paper>
        )}
      </>
    );
  };
  
  return (
    <Box className="content-container">
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/history')}
          sx={{ mr: 2 }}
        >
          Volver al Historial
        </Button>
        
        <Box sx={{ flexGrow: 1 }} />
        
        {learningPath && (
          <>
            <IconButton
              color={learningPath.is_favorite ? 'warning' : 'default'}
              onClick={handleFavoriteToggle}
              sx={{ mr: 1 }}
            >
              {learningPath.is_favorite ? <StarIcon /> : <StarBorderIcon />}
            </IconButton>
            
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownload}
              sx={{ mr: 1 }}
            >
              Descargar
            </Button>
            
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={handleDeleteClick}
            >
              Eliminar
            </Button>
          </>
        )}
      </Box>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Paper sx={{ p: 3, mb: 3, backgroundColor: 'error.light' }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      ) : learningPath ? (
        <>
          <Typography variant="h4" component="h1" gutterBottom>
            {learningPath.topic}
          </Typography>
          
          {renderLearningPathContent()}
        </>
      ) : (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6">
            No se pudo encontrar la ruta de aprendizaje
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate('/history')}
            sx={{ mt: 2 }}
          >
            Volver al Historial
          </Button>
        </Paper>
      )}
      
      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleCloseDeleteDialog}
      >
        <DialogTitle>Eliminar Ruta de Aprendizaje</DialogTitle>
        <DialogContent>
          <DialogContentText>
            ¿Estás seguro de que deseas eliminar esta ruta de aprendizaje? Esta acción no se puede deshacer.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog}>Cancelar</Button>
          <Button onClick={handleConfirmDelete} color="error" autoFocus>
            Eliminar
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Add Tag Dialog */}
      <Dialog
        open={tagDialogOpen}
        onClose={handleCloseTagDialog}
      >
        <DialogTitle>Añadir Etiqueta</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Añade una etiqueta para organizar mejor tus rutas de aprendizaje.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            label="Nueva Etiqueta"
            fullWidth
            value={newTag}
            onChange={handleNewTagChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LabelIcon />
                </InputAdornment>
              ),
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseTagDialog}>Cancelar</Button>
          <Button 
            onClick={handleAddTag} 
            color="primary" 
            disabled={!newTag.trim()}
          >
            Añadir
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HistoryDetail; 
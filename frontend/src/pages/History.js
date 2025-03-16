import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  TextField,
  Chip,
  InputAdornment,
  Tooltip,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Search as SearchIcon,
  Label as LabelIcon,
  AddCircleOutline as AddCircleOutlineIcon,
  Download as DownloadIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { formatDate, getRelativeTime } from '../utils/dateUtils';
import * as api from '../services/api';

const History = ({ showNotification }) => {
  const navigate = useNavigate();
  const [historyItems, setHistoryItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [clearAllDialogOpen, setClearAllDialogOpen] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredItems, setFilteredItems] = useState([]);
  const [tagDialogOpen, setTagDialogOpen] = useState(false);
  const [newTag, setNewTag] = useState('');
  
  // Load history items on component mount
  useEffect(() => {
    loadHistoryItems();
  }, []);
  
  // Filter items when search term or history items change
  useEffect(() => {
    if (!historyItems.length) {
      setFilteredItems([]);
      return;
    }
    
    const filtered = historyItems.filter(item => {
      const searchLower = searchTerm.toLowerCase();
      return (
        item.topic.toLowerCase().includes(searchLower) ||
        (item.tags && item.tags.some(tag => tag.toLowerCase().includes(searchLower)))
      );
    });
    
    setFilteredItems(filtered);
  }, [searchTerm, historyItems]);
  
  const loadHistoryItems = async () => {
    try {
      setLoading(true);
      const data = await api.getHistoryItems();
      setHistoryItems(data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
      setError(null);
    } catch (err) {
      console.error('Error loading history items:', err);
      setError('No se pudo cargar el historial. Por favor, inténtalo de nuevo más tarde.');
      showNotification('Error al cargar el historial', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  const handleDeleteClick = (id) => {
    setSelectedItemId(id);
    setDeleteDialogOpen(true);
  };
  
  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false);
    setSelectedItemId(null);
  };
  
  const handleConfirmDelete = async () => {
    if (!selectedItemId) return;
    
    try {
      await api.deleteHistoryItem(selectedItemId);
      setHistoryItems(historyItems.filter(item => item.id !== selectedItemId));
      showNotification('Ruta de aprendizaje eliminada correctamente', 'success');
    } catch (err) {
      console.error('Error deleting history item:', err);
      showNotification('Error al eliminar la ruta de aprendizaje', 'error');
    } finally {
      handleCloseDeleteDialog();
    }
  };
  
  const handleClearAllClick = () => {
    setClearAllDialogOpen(true);
  };
  
  const handleCloseClearAllDialog = () => {
    setClearAllDialogOpen(false);
  };
  
  const handleConfirmClearAll = async () => {
    try {
      await api.clearHistory();
      setHistoryItems([]);
      showNotification('Historial eliminado correctamente', 'success');
    } catch (err) {
      console.error('Error clearing history:', err);
      showNotification('Error al eliminar el historial', 'error');
    } finally {
      handleCloseClearAllDialog();
    }
  };
  
  const handleFavoriteToggle = async (id, isFavorite) => {
    try {
      await api.updateHistoryItemFavorite(id, !isFavorite);
      setHistoryItems(
        historyItems.map(item => 
          item.id === id ? { ...item, is_favorite: !isFavorite } : item
        )
      );
      showNotification(
        `Ruta de aprendizaje ${!isFavorite ? 'marcada como favorita' : 'desmarcada como favorita'}`,
        'success'
      );
    } catch (err) {
      console.error('Error updating favorite status:', err);
      showNotification('Error al actualizar el estado de favorito', 'error');
    }
  };
  
  const handleViewDetails = (id) => {
    navigate(`/history/${id}`);
  };
  
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };
  
  const handleClearSearch = () => {
    setSearchTerm('');
  };
  
  const handleOpenTagDialog = (id) => {
    setSelectedItemId(id);
    setTagDialogOpen(true);
    setNewTag('');
  };
  
  const handleCloseTagDialog = () => {
    setTagDialogOpen(false);
    setSelectedItemId(null);
    setNewTag('');
  };
  
  const handleNewTagChange = (e) => {
    setNewTag(e.target.value);
  };
  
  const handleAddTag = async () => {
    if (!newTag.trim() || !selectedItemId) return;
    
    try {
      const item = historyItems.find(item => item.id === selectedItemId);
      const currentTags = item.tags || [];
      
      if (currentTags.includes(newTag.trim())) {
        showNotification('Esta etiqueta ya existe para esta ruta de aprendizaje', 'warning');
        return;
      }
      
      const updatedTags = [...currentTags, newTag.trim()];
      
      await api.updateHistoryItemTags(selectedItemId, updatedTags);
      
      setHistoryItems(
        historyItems.map(item => 
          item.id === selectedItemId ? { ...item, tags: updatedTags } : item
        )
      );
      
      setNewTag('');
      showNotification('Etiqueta añadida correctamente', 'success');
    } catch (err) {
      console.error('Error adding tag:', err);
      showNotification('Error al añadir la etiqueta', 'error');
    }
  };
  
  const handleRemoveTag = async (itemId, tagToRemove) => {
    try {
      const item = historyItems.find(item => item.id === itemId);
      const updatedTags = (item.tags || []).filter(tag => tag !== tagToRemove);
      
      await api.updateHistoryItemTags(itemId, updatedTags);
      
      setHistoryItems(
        historyItems.map(item => 
          item.id === itemId ? { ...item, tags: updatedTags } : item
        )
      );
      
      showNotification('Etiqueta eliminada correctamente', 'success');
    } catch (err) {
      console.error('Error removing tag:', err);
      showNotification('Error al eliminar la etiqueta', 'error');
    }
  };
  
  const handleDownload = async (id, topic) => {
    try {
      const item = await api.getHistoryItem(id);
      
      // Create a blob from the learning path data
      const blob = new Blob([JSON.stringify(item.learning_path, null, 2)], { type: 'application/json' });
      
      // Create a sanitized filename
      const sanitizedTopic = topic.replace(/[^a-z0-9]/gi, '_').toLowerCase();
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
  
  return (
    <Box className="content-container">
      <Typography variant="h4" component="h1" gutterBottom>
        Historial de Rutas de Aprendizaje
      </Typography>
      
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              placeholder="Buscar por tema o etiquetas..."
              value={searchTerm}
              onChange={handleSearchChange}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
                endAdornment: searchTerm && (
                  <InputAdornment position="end">
                    <IconButton size="small" onClick={handleClearSearch}>
                      <ClearIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} sx={{ display: 'flex', justifyContent: { xs: 'flex-start', sm: 'flex-end' } }}>
            {historyItems.length > 0 && (
              <Button
                variant="outlined"
                color="error"
                startIcon={<DeleteIcon />}
                onClick={handleClearAllClick}
              >
                Borrar Todo
              </Button>
            )}
          </Grid>
        </Grid>
      </Paper>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Paper sx={{ p: 3, mb: 3, backgroundColor: 'error.light' }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      ) : historyItems.length === 0 ? (
        <Paper sx={{ p: 5, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            No hay rutas de aprendizaje en tu historial
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Genera nuevas rutas de aprendizaje y se guardarán automáticamente aquí.
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate('/')}
          >
            Generar Nueva Ruta
          </Button>
        </Paper>
      ) : (
        <>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2">
              {searchTerm
                ? `Mostrando ${filteredItems.length} de ${historyItems.length} rutas de aprendizaje`
                : `${historyItems.length} rutas de aprendizaje en total`}
            </Typography>
          </Box>
          
          <Grid container spacing={3}>
            {(searchTerm ? filteredItems : historyItems).map((item) => (
              <Grid item xs={12} sm={6} md={4} key={item.id}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Typography variant="h6" component="h2" gutterBottom sx={{ 
                        wordBreak: 'break-word', 
                        maxWidth: 'calc(100% - 40px)'
                      }}>
                        {item.topic}
                      </Typography>
                      <IconButton
                        size="small"
                        onClick={() => handleFavoriteToggle(item.id, item.is_favorite)}
                        color={item.is_favorite ? 'warning' : 'default'}
                      >
                        {item.is_favorite ? <StarIcon /> : <StarBorderIcon />}
                      </IconButton>
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {getRelativeTime(item.created_at)}
                    </Typography>
                    
                    <Typography variant="body2" gutterBottom>
                      {item.modules_count} módulos, {item.submodules_count} submódulos
                    </Typography>
                    
                    <Divider sx={{ my: 1 }} />
                    
                    <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(item.tags || []).map((tag, index) => (
                        <Chip
                          key={`${tag}-${index}`}
                          label={tag}
                          size="small"
                          onDelete={() => handleRemoveTag(item.id, tag)}
                        />
                      ))}
                      <Tooltip title="Añadir etiqueta">
                        <Chip
                          icon={<AddCircleOutlineIcon />}
                          label="Añadir"
                          size="small"
                          variant="outlined"
                          onClick={() => handleOpenTagDialog(item.id)}
                          sx={{ borderStyle: 'dashed' }}
                        />
                      </Tooltip>
                    </Box>
                  </CardContent>
                  
                  <CardActions>
                    <Button
                      size="small"
                      onClick={() => handleViewDetails(item.id)}
                    >
                      Ver Detalles
                    </Button>
                    <Button
                      size="small"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload(item.id, item.topic)}
                    >
                      Descargar
                    </Button>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDeleteClick(item.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
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
      
      {/* Clear All Confirmation Dialog */}
      <Dialog
        open={clearAllDialogOpen}
        onClose={handleCloseClearAllDialog}
      >
        <DialogTitle>Eliminar Todo el Historial</DialogTitle>
        <DialogContent>
          <DialogContentText>
            ¿Estás seguro de que deseas eliminar todo tu historial de rutas de aprendizaje? Esta acción no se puede deshacer y eliminarás {historyItems.length} rutas.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseClearAllDialog}>Cancelar</Button>
          <Button onClick={handleConfirmClearAll} color="error" autoFocus>
            Eliminar Todo
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

export default History; 
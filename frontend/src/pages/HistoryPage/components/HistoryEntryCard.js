import React, { useState, useEffect, memo, useCallback } from 'react';
import PropTypes from 'prop-types';
import {
  Typography,
  Box,
  CardContent,
  IconButton,
  Divider,
  Button,
  Chip,
  Grid,
  useMediaQuery,
  useTheme,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import DownloadIcon from '@mui/icons-material/Download';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import MoreVertIcon from '@mui/icons-material/MoreVert';

import { formatDate } from '../utils';
import { StyledCard } from '../styledComponents';
import TagsInput from './TagsInput';
import ConfirmationDialog from './ConfirmationDialog';

/**
 * Card component for displaying a single history entry
 * @param {Object} props - Component props
 * @param {Object} props.entry - History entry data
 * @param {Function} props.onView - Handler for viewing entry details
 * @param {Function} props.onDelete - Handler for deleting entry
 * @param {Function} props.onToggleFavorite - Handler for toggling favorite status
 * @param {Function} props.onUpdateTags - Handler for updating tags
 * @param {Function} props.onExport - Handler for exporting entry as JSON
 * @param {Function} props.onDownloadPDF - Handler for downloading entry as PDF
 * @param {boolean} props.virtualized - Whether the card is being rendered in a virtualized list
 * @returns {JSX.Element} History entry card component
 */
const HistoryEntryCard = memo(({ 
  entry, 
  onView, 
  onDelete, 
  onToggleFavorite, 
  onUpdateTags, 
  onExport,
  onDownloadPDF,
  virtualized = false
}) => {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [downloadMenuAnchor, setDownloadMenuAnchor] = useState(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Only log in development mode
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.debug(`Entry ${entry.topic} - ID: ${entry.id}, path_id: ${entry.path_id}`);
    }
  }, [entry]);

  const handleAddTag = useCallback(async (newTag) => {
    const updatedTags = [...entry.tags, newTag];
    await onUpdateTags(entry.path_id, updatedTags);
  }, [entry.tags, entry.path_id, onUpdateTags]);

  const handleDeleteTag = useCallback(async (tagToDelete) => {
    const updatedTags = entry.tags.filter(tag => tag !== tagToDelete);
    await onUpdateTags(entry.path_id, updatedTags);
  }, [entry.tags, entry.path_id, onUpdateTags]);

  const handleOpenDownloadMenu = useCallback((event) => {
    event.stopPropagation();
    setDownloadMenuAnchor(event.currentTarget);
  }, []);

  const handleCloseDownloadMenu = useCallback(() => {
    setDownloadMenuAnchor(null);
  }, []);

  const handleDownloadJSON = useCallback(() => {
    handleCloseDownloadMenu();
    onExport(entry.path_id);
  }, [handleCloseDownloadMenu, onExport, entry.path_id]);

  const handleDownloadPDF = useCallback(() => {
    handleCloseDownloadMenu();
    onDownloadPDF(entry.path_id);
  }, [handleCloseDownloadMenu, onDownloadPDF, entry.path_id]);
  
  const handleViewDetails = useCallback(() => {
    onView(entry.path_id);
  }, [onView, entry.path_id]);
  
  const handleToggleFavorite = useCallback(() => {
    onToggleFavorite(entry.path_id, !entry.favorite);
  }, [onToggleFavorite, entry.path_id, entry.favorite]);
  
  const handleConfirmDelete = useCallback(() => {
    setConfirmDelete(true);
  }, []);
  
  const handleCancelDelete = useCallback(() => {
    setConfirmDelete(false);
  }, []);
  
  const handleDelete = useCallback(() => {
    onDelete(entry.path_id);
    setConfirmDelete(false);
  }, [onDelete, entry.path_id]);

  // Get modules count, handle both formats for backward compatibility
  const modulesCount = entry.modules_count || 
    (entry.path_data && entry.path_data.modules ? entry.path_data.modules.length : 0);

  // Prepare the card content - optimized for virtualized rendering
  return (
    // When virtualized, don't wrap in Grid item as the parent handles that
    virtualized ? (
      <StyledCard variant="outlined" sx={{ height: '100%' }}>
        <CardContent sx={{ flexGrow: 1, p: { xs: 2, md: 2 } }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6" sx={{ 
              fontWeight: 'medium', 
              fontSize: { xs: '1rem', sm: '1.1rem' },
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {entry.topic}
            </Typography>
            <IconButton
              color={entry.favorite ? "warning" : "default"}
              onClick={handleToggleFavorite}
              size="small"
            >
              {entry.favorite ? <StarIcon /> : <StarBorderIcon />}
            </IconButton>
          </Box>
          
          <Typography variant="body2" color="text.secondary" gutterBottom fontSize={{ xs: '0.75rem', sm: '0.8rem' }}>
            Created: {formatDate(entry.creation_date)}
          </Typography>
          
          {entry.last_modified_date && (
            <Typography variant="body2" color="text.secondary" gutterBottom fontSize={{ xs: '0.75rem', sm: '0.8rem' }}>
              Modified: {formatDate(entry.last_modified_date)}
            </Typography>
          )}
          
          <Box sx={{ mt: 1, mb: 1.5, display: 'flex', flexWrap: 'wrap' }}>
            <Chip
              label={`${modulesCount} modules`}
              size="small"
              sx={{ mr: 1, mb: { xs: 1, sm: 0 } }}
            />
            <Chip
              label={entry.source === 'generated' ? 'Generated' : 'Imported'}
              size="small"
              color={entry.source === 'generated' ? 'primary' : 'secondary'}
            />
          </Box>
          
          <TagsInput
            tags={entry.tags}
            onAddTag={handleAddTag}
            onDeleteTag={handleDeleteTag}
            maxDisplayTags={3}
          />
          
          <Divider sx={{ my: 1.5 }} />
          
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            flexDirection: { xs: isMobile ? 'column' : 'row', sm: 'row' },
            alignItems: { xs: isMobile ? 'stretch' : 'center', sm: 'center' }
          }}>
            <Button
              startIcon={<ExpandMoreIcon />}
              onClick={handleViewDetails}
              size="small"
              sx={{ mb: isMobile ? 1 : 0, width: isMobile ? '100%' : 'auto' }}
            >
              View Details
            </Button>
            
            <Box sx={{ display: 'flex', justifyContent: isMobile ? 'space-between' : 'flex-end', width: isMobile ? '100%' : 'auto' }}>
              <Tooltip title="Download options">
                <IconButton 
                  size="small" 
                  onClick={handleOpenDownloadMenu}
                  aria-label="Download options"
                >
                  <DownloadIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              
              <Menu
                anchorEl={downloadMenuAnchor}
                open={Boolean(downloadMenuAnchor)}
                onClose={handleCloseDownloadMenu}
              >
                <MenuItem onClick={handleDownloadJSON}>
                  <ListItemIcon>
                    <FileDownloadIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText>Download as JSON</ListItemText>
                </MenuItem>
                <MenuItem onClick={handleDownloadPDF}>
                  <ListItemIcon>
                    <PictureAsPdfIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText>Download as PDF</ListItemText>
                </MenuItem>
              </Menu>

              <IconButton
                size="small"
                color="error"
                onClick={handleConfirmDelete}
                title="Delete"
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Box>
          </Box>
        </CardContent>
        
        <ConfirmationDialog
          open={confirmDelete}
          title="Delete Learning Path"
          message={`Are you sure you want to delete "${entry.topic}"?`}
          onConfirm={handleDelete}
          onCancel={handleCancelDelete}
        />
      </StyledCard>
    ) : (
      // Non-virtualized version wrapped in Grid item
      <Grid item xs={12} sm={6} md={4}>
        <StyledCard variant="outlined">
          <CardContent sx={{ flexGrow: 1, p: { xs: 2, md: 3 } }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6" sx={{ 
                fontWeight: 'medium', 
                fontSize: { xs: '1rem', sm: '1.15rem', md: '1.25rem' },
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {entry.topic}
              </Typography>
              <IconButton
                color={entry.favorite ? "warning" : "default"}
                onClick={handleToggleFavorite}
                size="small"
              >
                {entry.favorite ? <StarIcon /> : <StarBorderIcon />}
              </IconButton>
            </Box>
            
            <Typography variant="body2" color="text.secondary" gutterBottom fontSize={{ xs: '0.75rem', sm: '0.875rem' }}>
              Created: {formatDate(entry.creation_date)}
            </Typography>
            
            {entry.last_modified_date && (
              <Typography variant="body2" color="text.secondary" gutterBottom fontSize={{ xs: '0.75rem', sm: '0.875rem' }}>
                Modified: {formatDate(entry.last_modified_date)}
              </Typography>
            )}
            
            <Box sx={{ mt: 1, mb: 2, display: 'flex', flexWrap: 'wrap' }}>
              <Chip
                label={`${modulesCount} modules`}
                size="small"
                sx={{ mr: 1, mb: { xs: 1, sm: 0 } }}
              />
              <Chip
                label={entry.source === 'generated' ? 'Generated' : 'Imported'}
                size="small"
                color={entry.source === 'generated' ? 'primary' : 'secondary'}
              />
            </Box>
            
            <TagsInput
              tags={entry.tags}
              onAddTag={handleAddTag}
              onDeleteTag={handleDeleteTag}
            />
            
            <Divider sx={{ my: 2 }} />
            
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              flexDirection: { xs: isMobile ? 'column' : 'row', sm: 'row' },
              alignItems: { xs: isMobile ? 'stretch' : 'center', sm: 'center' }
            }}>
              <Button
                startIcon={<ExpandMoreIcon />}
                onClick={handleViewDetails}
                size="small"
                sx={{ mb: isMobile ? 1 : 0, width: isMobile ? '100%' : 'auto' }}
              >
                View Details
              </Button>
              
              <Box sx={{ display: 'flex', justifyContent: isMobile ? 'space-between' : 'flex-end', width: isMobile ? '100%' : 'auto' }}>
                <Tooltip title="Download options">
                  <IconButton 
                    size="small" 
                    onClick={handleOpenDownloadMenu}
                    aria-label="Download options"
                  >
                    <DownloadIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                
                <Menu
                  anchorEl={downloadMenuAnchor}
                  open={Boolean(downloadMenuAnchor)}
                  onClose={handleCloseDownloadMenu}
                >
                  <MenuItem onClick={handleDownloadJSON}>
                    <ListItemIcon>
                      <FileDownloadIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>Download as JSON</ListItemText>
                  </MenuItem>
                  <MenuItem onClick={handleDownloadPDF}>
                    <ListItemIcon>
                      <PictureAsPdfIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>Download as PDF</ListItemText>
                  </MenuItem>
                </Menu>

                <IconButton
                  size="small"
                  color="error"
                  onClick={handleConfirmDelete}
                  title="Delete"
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Box>
            </Box>
          </CardContent>
          
          <ConfirmationDialog
            open={confirmDelete}
            title="Delete Learning Path"
            message={`Are you sure you want to delete "${entry.topic}"?`}
            onConfirm={handleDelete}
            onCancel={handleCancelDelete}
          />
        </StyledCard>
      </Grid>
    )
  );
});

HistoryEntryCard.propTypes = {
  entry: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    path_id: PropTypes.string,
    topic: PropTypes.string.isRequired,
    creation_date: PropTypes.string,
    last_modified_date: PropTypes.string,
    favorite: PropTypes.bool,
    tags: PropTypes.arrayOf(PropTypes.string),
    source: PropTypes.string,
    modules_count: PropTypes.number,
    path_data: PropTypes.object
  }).isRequired,
  onView: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onToggleFavorite: PropTypes.func.isRequired,
  onUpdateTags: PropTypes.func.isRequired,
  onExport: PropTypes.func.isRequired,
  onDownloadPDF: PropTypes.func.isRequired,
  virtualized: PropTypes.bool
};

export default HistoryEntryCard; 
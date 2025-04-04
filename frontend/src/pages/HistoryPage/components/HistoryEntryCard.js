import React, { useState, useEffect } from 'react';
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
  useTheme
} from '@mui/material';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import DownloadIcon from '@mui/icons-material/Download';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

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
 * @param {Function} props.onExport - Handler for exporting entry
 * @returns {JSX.Element} History entry card component
 */
const HistoryEntryCard = ({ entry, onView, onDelete, onToggleFavorite, onUpdateTags, onExport }) => {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // For debugging - log the ID formats
  useEffect(() => {
    console.debug(`Entry ${entry.topic} - ID: ${entry.id}, path_id: ${entry.path_id}`);
  }, [entry]);

  const handleAddTag = async (newTag) => {
    const updatedTags = [...entry.tags, newTag];
    await onUpdateTags(entry.path_id, updatedTags);
  };

  const handleDeleteTag = async (tagToDelete) => {
    const updatedTags = entry.tags.filter(tag => tag !== tagToDelete);
    await onUpdateTags(entry.path_id, updatedTags);
  };

  return (
    <Grid item xs={12} sm={6} md={4}>
      <StyledCard variant="outlined">
        <CardContent sx={{ flexGrow: 1, p: { xs: 2, md: 3 } }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6" sx={{ 
              fontWeight: 'medium', 
              fontSize: { xs: '1rem', sm: '1.15rem', md: '1.25rem' }
            }} noWrap>
              {entry.topic}
            </Typography>
            <IconButton
              color={entry.favorite ? "warning" : "default"}
              onClick={() => onToggleFavorite(entry.path_id, !entry.favorite)}
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
              label={`${entry.modules_count || (entry.path_data && entry.path_data.modules ? entry.path_data.modules.length : 0)} modules`}
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
              onClick={() => onView(entry.path_id)}
              size="small"
              sx={{ mb: isMobile ? 1 : 0, width: isMobile ? '100%' : 'auto' }}
            >
              View Details
            </Button>
            
            <Box sx={{ display: 'flex', justifyContent: isMobile ? 'space-between' : 'flex-end', width: isMobile ? '100%' : 'auto' }}>
              <IconButton size="small" onClick={() => onExport(entry.path_id)} title="Export">
                <DownloadIcon fontSize="small" />
              </IconButton>
              <IconButton
                size="small"
                color="error"
                onClick={() => setConfirmDelete(true)}
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
          onConfirm={() => {
            onDelete(entry.path_id);
            setConfirmDelete(false);
          }}
          onCancel={() => setConfirmDelete(false)}
        />
      </StyledCard>
    </Grid>
  );
};

HistoryEntryCard.propTypes = {
  entry: PropTypes.shape({
    id: PropTypes.string,
    path_id: PropTypes.string.isRequired,
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
  onExport: PropTypes.func.isRequired
};

export default HistoryEntryCard; 
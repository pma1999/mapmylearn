import React, { useState, memo, useCallback } from 'react';
import PropTypes from 'prop-types';
import { 
  Box, 
  TextField, 
  Button, 
  Chip, 
  Tooltip, 
  Typography, 
  IconButton, 
  InputAdornment 
} from '@mui/material';
import LabelIcon from '@mui/icons-material/Label';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import { StyledChip } from '../styledComponents';

/**
 * Component for tag input and display
 * @param {Object} props - Component props
 * @param {Array<string>} props.tags - Array of current tags
 * @param {Function} props.onAddTag - Handler for adding a tag
 * @param {Function} props.onDeleteTag - Handler for deleting a tag
 * @param {number} props.maxDisplayTags - Maximum number of tags to display before showing count
 * @returns {JSX.Element} Tags input component
 */
const TagsInput = memo(({ tags = [], onAddTag, onDeleteTag, maxDisplayTags = null }) => {
  const [newTag, setNewTag] = useState('');
  const [showInput, setShowInput] = useState(false);

  const handleAddTag = useCallback((event) => {
    if (event && typeof event.stopPropagation === 'function') {
      event.stopPropagation();
    }
    
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      onAddTag(newTag.trim());
      setNewTag('');
    }
  }, [newTag, tags, onAddTag]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    } else if (e.key === 'Escape') {
      setShowInput(false);
      setNewTag('');
    }
  }, [handleAddTag]);
  
  const handleInputChange = useCallback((e) => {
    setNewTag(e.target.value);
  }, []);
  
  const handleShowInput = useCallback((event) => {
    event.stopPropagation();
    setShowInput(true);
  }, []);

  // Determine which tags to show
  const displayTags = maxDisplayTags && tags.length > maxDisplayTags
    ? tags.slice(0, maxDisplayTags)
    : tags;
  
  // Count of hidden tags
  const hiddenTagsCount = maxDisplayTags && tags.length > maxDisplayTags
    ? tags.length - maxDisplayTags
    : 0;

  return (
    <Box>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 0.5, mb: 1 }}>
        {displayTags.map((tag) => (
          <StyledChip
            key={tag}
            label={tag}
            onDelete={() => onDeleteTag(tag)}
            size="small"
            icon={<LabelIcon fontSize="small" />}
          />
        ))}
        
        {hiddenTagsCount > 0 && (
          <Tooltip 
            arrow 
            title={
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                {tags.slice(maxDisplayTags).map(tag => (
                  <Typography key={tag} variant="body2">{tag}</Typography>
                ))}
              </Box>
            }
          >
            <StyledChip
              icon={<MoreHorizIcon fontSize="small" />}
              label={`+${hiddenTagsCount}`}
              size="small"
              sx={{ cursor: 'help' }}
            />
          </Tooltip>
        )}
        
        {showInput ? (
          <TextField
            size="small"
            value={newTag}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="New tag..."
            variant="outlined"
            autoFocus
            onBlur={() => { if (!newTag) setShowInput(false); }}
            sx={{ 
              maxWidth: '150px',
              '& .MuiInputBase-root': { height: '28px' }
            }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    aria-label="add tag"
                    onClick={handleAddTag}
                    disabled={!newTag.trim() || tags.includes(newTag.trim())}
                    edge="end"
                    size="small"
                  >
                    <AddCircleOutlineIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        ) : (
          <Tooltip title="Add Tag" arrow>
            <IconButton 
              size="small" 
              onClick={handleShowInput}
              aria-label="Add new tag"
              sx={{ p: 0.25 }}
            >
              <AddCircleOutlineIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Box>
    </Box>
  );
});

TagsInput.propTypes = {
  tags: PropTypes.arrayOf(PropTypes.string),
  onAddTag: PropTypes.func.isRequired,
  onDeleteTag: PropTypes.func.isRequired,
  maxDisplayTags: PropTypes.number
};

export default TagsInput; 
import React, { useState, memo, useCallback } from 'react';
import PropTypes from 'prop-types';
import { Box, TextField, Button, Chip, Tooltip, Typography } from '@mui/material';
import LabelIcon from '@mui/icons-material/Label';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
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

  const handleAddTag = useCallback(() => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      onAddTag(newTag.trim());
      setNewTag('');
    }
  }, [newTag, tags, onAddTag]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  }, [handleAddTag]);
  
  const handleInputChange = useCallback((e) => {
    setNewTag(e.target.value);
  }, []);
  
  const handleToggleInput = useCallback(() => {
    setShowInput(prev => !prev);
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
      <Box sx={{ display: 'flex', flexWrap: 'wrap', mb: 1 }}>
        {displayTags.map((tag) => (
          <StyledChip
            key={tag}
            label={tag}
            onDelete={() => onDeleteTag(tag)}
            size="small"
            icon={<LabelIcon />}
          />
        ))}
        
        {hiddenTagsCount > 0 && (
          <Tooltip title={tags.slice(maxDisplayTags).join(', ')} arrow>
            <StyledChip
              icon={<MoreHorizIcon />}
              label={`+${hiddenTagsCount} more`}
              size="small"
              sx={{ cursor: 'pointer' }}
            />
          </Tooltip>
        )}
      </Box>
      
      {showInput ? (
        <Box sx={{ display: 'flex' }}>
          <TextField
            size="small"
            value={newTag}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Add tag..."
            variant="outlined"
            fullWidth
            sx={{ mr: 1 }}
            autoFocus
          />
          <Button
            size="small"
            variant="outlined"
            onClick={handleAddTag}
            disabled={!newTag.trim()}
          >
            Add
          </Button>
        </Box>
      ) : (
        <Button
          size="small"
          variant="text"
          onClick={handleToggleInput}
          sx={{ p: 0.5, minWidth: 'auto' }}
        >
          + Add Tag
        </Button>
      )}
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
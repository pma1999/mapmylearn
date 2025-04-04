import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Box, TextField, Button, Chip } from '@mui/material';
import LabelIcon from '@mui/icons-material/Label';
import { StyledChip } from '../styledComponents';

/**
 * Component for tag input and display
 * @param {Object} props - Component props
 * @param {Array<string>} props.tags - Array of current tags
 * @param {Function} props.onAddTag - Handler for adding a tag
 * @param {Function} props.onDeleteTag - Handler for deleting a tag
 * @returns {JSX.Element} Tags input component
 */
const TagsInput = ({ tags = [], onAddTag, onDeleteTag }) => {
  const [newTag, setNewTag] = useState('');

  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      onAddTag(newTag.trim());
      setNewTag('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', mb: 1 }}>
        {tags.map((tag) => (
          <StyledChip
            key={tag}
            label={tag}
            onDelete={() => onDeleteTag(tag)}
            size="small"
            icon={<LabelIcon />}
          />
        ))}
      </Box>
      <Box sx={{ display: 'flex' }}>
        <TextField
          size="small"
          value={newTag}
          onChange={(e) => setNewTag(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Add tag..."
          variant="outlined"
          fullWidth
          sx={{ mr: 1 }}
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
    </Box>
  );
};

TagsInput.propTypes = {
  tags: PropTypes.arrayOf(PropTypes.string),
  onAddTag: PropTypes.func.isRequired,
  onDeleteTag: PropTypes.func.isRequired
};

export default TagsInput; 
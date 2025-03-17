import React from 'react';
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Box,
  TextField,
  FormControlLabel,
  Checkbox,
  Chip,
  InputAdornment,
  IconButton,
  Typography
} from '@mui/material';
import { styled } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';

const StyledChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
}));

function SaveDialog({
  open,
  onClose,
  onSave,
  onCancel,
  tags,
  setTags,
  favorite,
  setFavorite,
  newTag,
  setNewTag,
  handleAddTag,
  handleDeleteTag,
  handleTagKeyDown
}) {
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Save to History</DialogTitle>
      <DialogContent>
        <DialogContentText>
          Do you want to save this learning path to your history?
        </DialogContentText>
        
        <Box sx={{ mt: 3 }}>
          <FormControlLabel
            control={
              <Checkbox 
                icon={<StarBorderIcon />}
                checkedIcon={<StarIcon />}
                checked={favorite} 
                onChange={(e) => setFavorite(e.target.checked)}
              />
            }
            label="Mark as favorite"
          />
        </Box>
        
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" gutterBottom>
            Tags:
          </Typography>
          
          <Box sx={{ display: 'flex', flexWrap: 'wrap', mb: 1 }}>
            {tags.map((tag) => (
              <StyledChip
                key={tag}
                label={tag}
                onDelete={() => handleDeleteTag(tag)}
                size="small"
              />
            ))}
          </Box>
          
          <Box sx={{ display: 'flex' }}>
            <TextField
              size="small"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyDown={handleTagKeyDown}
              placeholder="Add tag..."
              variant="outlined"
              fullWidth
              sx={{ mr: 1 }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton 
                      onClick={handleAddTag} 
                      disabled={!newTag.trim()}
                      size="small"
                    >
                      <AddIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>
          Skip & Continue
        </Button>
        <Button onClick={onSave} variant="contained" color="primary">
          Save to History
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default SaveDialog; 
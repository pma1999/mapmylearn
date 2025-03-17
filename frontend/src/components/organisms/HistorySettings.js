import React from 'react';
import {
  Typography,
  Box,
  TextField,
  Grid,
  FormControlLabel,
  Checkbox,
  Chip,
  InputAdornment,
  IconButton,
  Divider
} from '@mui/material';
import { styled } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import StorageIcon from '@mui/icons-material/Storage';

const StyledChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
}));

function HistorySettings({
  autoSaveToHistory,
  setAutoSaveToHistory,
  initialFavorite,
  setInitialFavorite,
  initialTags,
  setInitialTags,
  newTag,
  setNewTag,
  handleAddTag,
  handleDeleteTag,
  handleTagKeyDown,
  isGenerating
}) {
  return (
    <>
      <Divider sx={{ my: 2 }} />
      <Typography variant="subtitle1" sx={{ fontWeight: 'medium', mb: 2 }}>
        History Settings
      </Typography>
      
      <FormControlLabel
        control={
          <Checkbox 
            checked={autoSaveToHistory} 
            onChange={(e) => setAutoSaveToHistory(e.target.checked)}
            disabled={isGenerating}
          />
        }
        label="Automatically save to history"
      />
      
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, ml: 4 }}>
        <StorageIcon fontSize="inherit" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
        History is stored locally in your browser and is not shared across devices.
      </Typography>
      
      {autoSaveToHistory && (
        <Box sx={{ mt: 2 }}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox 
                    icon={<StarBorderIcon />}
                    checkedIcon={<StarIcon />}
                    checked={initialFavorite} 
                    onChange={(e) => setInitialFavorite(e.target.checked)}
                    disabled={isGenerating}
                  />
                }
                label="Mark as favorite"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="body2" gutterBottom>
                Tags:
              </Typography>
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', mb: 1 }}>
                {initialTags.map((tag) => (
                  <StyledChip
                    key={tag}
                    label={tag}
                    onDelete={() => handleDeleteTag(tag)}
                    size="small"
                    disabled={isGenerating}
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
                  disabled={isGenerating}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton 
                          onClick={handleAddTag} 
                          disabled={!newTag.trim() || isGenerating}
                          size="small"
                        >
                          <AddIcon />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Box>
            </Grid>
          </Grid>
        </Box>
      )}
    </>
  );
}

export default HistorySettings; 
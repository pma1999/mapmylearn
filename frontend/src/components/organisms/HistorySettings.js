import React from 'react';
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Box,
  TextField,
  Grid,
  FormControlLabel,
  Checkbox,
  Chip,
  Stack,
  InputAdornment,
  IconButton
} from '@mui/material';
import { styled } from '@mui/material/styles';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import StarIcon from '@mui/icons-material/Star';
import HistoryIcon from '@mui/icons-material/History';
import AddIcon from '@mui/icons-material/Add';

const StyledChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
  [theme.breakpoints.down('sm')]: {
    fontSize: '0.75rem',
    height: '28px',
  },
}));

const HistorySettings = ({
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
  isGenerating,
  isMobile
}) => {
  return (
    <Accordion disabled={isGenerating} sx={{ mb: 2 }}>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="history-settings-content"
        id="history-settings-header"
      >
        <Stack direction="row" spacing={1} alignItems="center">
          <HistoryIcon color="primary" />
          <Typography variant="h6" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>History Settings</Typography>
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <Typography variant="body2" color="text.secondary" paragraph sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
          Configure how your course will be saved to your history.
        </Typography>
        
        <Grid container spacing={isMobile ? 2 : 3} direction="column">
          <Grid item>
            <FormControlLabel
              control={
                <Checkbox
                  checked={autoSaveToHistory}
                  onChange={(e) => setAutoSaveToHistory(e.target.checked)}
                  disabled={isGenerating}
                  size={isMobile ? "small" : "medium"}
                />
              }
              label={
                <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                  Automatically save to history
                </Typography>
              }
            />
          </Grid>
          
          <Grid item>
            <FormControlLabel
              control={
                <Checkbox
                  checked={initialFavorite}
                  onChange={(e) => setInitialFavorite(e.target.checked)}
                  disabled={isGenerating}
                  size={isMobile ? "small" : "medium"}
                  icon={<StarBorderIcon />}
                  checkedIcon={<StarIcon />}
                />
              }
              label={
                <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                  Add to favorites
                </Typography>
              }
            />
          </Grid>
          
          <Grid item>
            <Typography variant="body2" sx={{ mb: 1, fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
              Tags:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', mb: 1 }}>
              {initialTags.map(tag => (
                <StyledChip
                  key={tag}
                  label={tag}
                  onDelete={() => handleDeleteTag(tag)}
                  size={isMobile ? "small" : "medium"}
                />
              ))}
              {initialTags.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', sm: '0.8rem' } }}>
                  No tags added
                </Typography>
              )}
            </Box>
            
            <TextField
              label="Add Tag"
              variant="outlined"
              size={isMobile ? "small" : "medium"}
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyDown={handleTagKeyDown}
              disabled={isGenerating}
              fullWidth
              margin="dense"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton 
                      onClick={handleAddTag}
                      disabled={!newTag.trim()} 
                      edge="end"
                      size={isMobile ? "small" : "medium"}
                    >
                      <AddIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              placeholder="Type and press Enter to add"
              sx={{ mt: 1 }}
            />
          </Grid>
        </Grid>
        
        {!autoSaveToHistory && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="info.main" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
              You will be prompted to save after generation completes.
            </Typography>
          </Box>
        )}
      </AccordionDetails>
    </Accordion>
  );
};

export default HistorySettings; 
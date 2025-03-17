import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Chip,
  FormControlLabel,
  Checkbox,
  InputAdornment,
  IconButton,
  useMediaQuery,
  useTheme
} from '@mui/material';
import { styled } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import StarIcon from '@mui/icons-material/Star';

const StyledChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
  [theme.breakpoints.down('sm')]: {
    fontSize: '0.75rem',
    height: '28px',
  },
}));

const SaveDialog = ({
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
  handleTagKeyDown,
  isMobile
}) => {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle sx={{ 
        pb: 1,
        fontSize: { xs: '1.2rem', sm: '1.5rem' }
      }}>
        Save to History
      </DialogTitle>
      
      <DialogContent dividers>
        <Typography variant="body2" sx={{ 
          mb: 3,
          fontSize: { xs: '0.875rem', sm: '1rem' }  
        }}>
          Your learning path has been generated. Would you like to save it to your history?
        </Typography>
        
        <Box sx={{ mb: 3 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={favorite}
                onChange={(e) => setFavorite(e.target.checked)}
                icon={<StarBorderIcon />}
                checkedIcon={<StarIcon color="warning" />}
                size={isMobile ? "small" : "medium"}
              />
            }
            label={
              <Typography variant="body2" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                Add to favorites
              </Typography>
            }
          />
        </Box>
        
        <Box sx={{ mb: 1 }}>
          <Typography variant="body2" sx={{ 
            mb: 1,
            fontSize: { xs: '0.875rem', sm: '1rem' }
          }}>
            Tags:
          </Typography>
          
          <Box sx={{ display: 'flex', flexWrap: 'wrap', mb: 1 }}>
            {tags.map(tag => (
              <StyledChip
                key={tag}
                label={tag}
                onDelete={() => handleDeleteTag(tag)}
                size={isMobile ? "small" : "medium"}
              />
            ))}
            {tags.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
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
            fullWidth
            margin="dense"
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton 
                    onClick={handleAddTag}
                    disabled={!newTag.trim()} 
                    size={isMobile ? "small" : "medium"}
                  >
                    <AddIcon />
                  </IconButton>
                </InputAdornment>
              ),
            }}
            placeholder="Type and press Enter to add"
          />
        </Box>
      </DialogContent>
      
      <DialogActions sx={{ 
        py: { xs: 1.5, sm: 2 },
        px: { xs: 2, sm: 3 },
        flexDirection: { xs: 'column', sm: 'row' },
        gap: { xs: 1, sm: 0 }
      }}>
        <Button 
          onClick={onCancel}
          sx={{ 
            width: { xs: '100%', sm: 'auto' },
            order: { xs: 2, sm: 1 }
          }}
        >
          Don't Save
        </Button>
        <Button 
          onClick={onSave} 
          variant="contained" 
          color="primary"
          sx={{ 
            width: { xs: '100%', sm: 'auto' },
            order: { xs: 1, sm: 2 }
          }}
        >
          Save to History
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SaveDialog; 
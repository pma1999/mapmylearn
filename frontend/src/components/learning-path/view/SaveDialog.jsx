import React from 'react';
import PropTypes from 'prop-types';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Box,
  TextField,
  FormControlLabel,
  Checkbox,
  IconButton,
  InputAdornment,
  Typography,
  Chip,
  useTheme
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import SaveIcon from '@mui/icons-material/Save';
import StorageIcon from '@mui/icons-material/Storage';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';

/**
 * Dialog component for saving a learning path to history
 * 
 * @param {Object} props Component props
 * @param {boolean} props.open Whether the dialog is open
 * @param {Function} props.onClose Handler for dialog close
 * @param {Function} props.onConfirm Handler for save confirmation
 * @param {Array} props.tags Array of tags
 * @param {string} props.newTag New tag input value
 * @param {boolean} props.favorite Whether the learning path is marked as favorite
 * @param {Function} props.onAddTag Handler for adding a tag
 * @param {Function} props.onDeleteTag Handler for deleting a tag
 * @param {Function} props.onTagChange Handler for tag input change
 * @param {Function} props.onTagKeyDown Handler for tag input key down
 * @param {Function} props.onFavoriteChange Handler for favorite toggle
 * @param {boolean} props.isMobile Whether the view is in mobile mode
 * @returns {JSX.Element} Save dialog component
 */
const SaveDialog = ({
  open,
  onClose,
  onConfirm,
  tags,
  newTag,
  favorite,
  onAddTag,
  onDeleteTag,
  onTagChange,
  onTagKeyDown,
  onFavoriteChange,
  isMobile
}) => {
  const theme = useTheme();

  // Component for styled tag chip
  const StyledChip = ({ label, onDelete }) => (
    <Chip
      label={label}
      onDelete={onDelete}
      size="small"
      sx={{ margin: 0.5 }}
    />
  );

  return (
    <Dialog 
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="save-dialog-title"
      PaperProps={{
        sx: { 
          m: { xs: 2, sm: 3 },
          width: { xs: 'calc(100% - 16px)', sm: 'auto' },
          borderRadius: 2
        }
      }}
    >
      <DialogTitle id="save-dialog-title">
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <StorageIcon sx={{ mr: 1, color: theme.palette.primary.main }} />
          <Typography variant="h6" sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
            Save to Local History
          </Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        <DialogContentText sx={{ mb: 2, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
          This learning path will be saved to your browser's local storage. It will be available only on this device and browser.
        </DialogContentText>
        
        <FormControlLabel
          control={
            <Checkbox
              icon={<StarBorderIcon />}
              checkedIcon={<StarIcon />}
              checked={favorite}
              onChange={(e) => onFavoriteChange(e.target.checked)}
              color="primary"
            />
          }
          label={
            <Typography sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
              Mark as favorite
            </Typography>
          }
          sx={{ mb: 2 }}
        />
        
        <Typography variant="subtitle2" gutterBottom sx={{ fontSize: { xs: '0.8125rem', sm: '0.875rem' } }}>
          Tags:
        </Typography>
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', mb: 1 }}>
          {tags.map((tag) => (
            <StyledChip
              key={tag}
              label={tag}
              onDelete={() => onDeleteTag(tag)}
            />
          ))}
        </Box>
        
        <Box sx={{ display: 'flex' }}>
          <TextField
            size="small"
            value={newTag}
            onChange={(e) => onTagChange(e.target.value)}
            onKeyDown={onTagKeyDown}
            placeholder="Add tag..."
            variant="outlined"
            fullWidth
            sx={{ mr: 1 }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton 
                    onClick={onAddTag} 
                    disabled={!newTag.trim()}
                    size="small"
                    aria-label="add tag"
                  >
                    <AddIcon />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        </Box>
      </DialogContent>
      
      <DialogActions sx={{ px: { xs: 2, sm: 3 }, pb: { xs: 2, sm: 2 } }}>
        <Button onClick={onClose} size={isMobile ? "small" : "medium"}>
          Cancel
        </Button>
        <Button 
          onClick={onConfirm}
          color="primary"
          variant="contained"
          startIcon={<SaveIcon />}
          size={isMobile ? "small" : "medium"}
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

SaveDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onConfirm: PropTypes.func.isRequired,
  tags: PropTypes.arrayOf(PropTypes.string).isRequired,
  newTag: PropTypes.string.isRequired,
  favorite: PropTypes.bool.isRequired,
  onAddTag: PropTypes.func.isRequired,
  onDeleteTag: PropTypes.func.isRequired,
  onTagChange: PropTypes.func.isRequired,
  onTagKeyDown: PropTypes.func.isRequired,
  onFavoriteChange: PropTypes.func.isRequired,
  isMobile: PropTypes.bool
};

SaveDialog.defaultProps = {
  isMobile: false
};

export default SaveDialog; 
import React from 'react';
import PropTypes from 'prop-types';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  IconButton,
  Slide,
  useMediaQuery,
  useTheme
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

/**
 * Generic confirmation dialog component
 * @param {Object} props - Component props
 * @param {boolean} props.open - Whether the dialog is open
 * @param {string} props.title - Dialog title
 * @param {string} props.message - Dialog message
 * @param {Function} props.onConfirm - Handler for confirmation
 * @param {Function} props.onCancel - Handler for cancellation
 * @param {boolean} [props.isDestructive] - Optional: If true, styles confirm button for destructive actions
 * @returns {JSX.Element} Confirmation dialog component
 */
const ConfirmationDialog = ({ open, title, message, onConfirm, onCancel, isDestructive = false }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  return (
    <Dialog 
      open={open} 
      onClose={onCancel}
      fullWidth
      maxWidth="xs"
      fullScreen={isMobile}
      TransitionComponent={Slide}
      TransitionProps={{ direction: 'up' }}
    >
      <DialogTitle sx={{ fontWeight: 'bold' }}>
        {isMobile && (
          <IconButton
            edge="start"
            color="inherit"
            onClick={onCancel}
            aria-label="close"
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
        )}
        {title}
      </DialogTitle>
      <DialogContent>
        <DialogContentText>{message}</DialogContentText>
      </DialogContent>
      <DialogActions sx={{ 
        px: { xs: 2, sm: 3 }, 
        py: { xs: 2, sm: 1.5 },
        flexDirection: isMobile ? 'column-reverse' : 'row',
        alignItems: 'center',
        justifyContent: 'flex-end'
      }}>
        <Button 
          onClick={onCancel} 
          variant="text"
          fullWidth={isMobile}
          sx={{ mb: isMobile ? 1 : 0, mr: isMobile ? 0 : 1 }}
        >
          Cancel
        </Button>
        <Button 
          onClick={onConfirm} 
          color={isDestructive ? 'error' : 'primary'}
          variant="contained" 
          autoFocus
          fullWidth={isMobile}
          sx={{ 
            ...(isDestructive && {
              // Example: backgroundColor: theme.palette.error.dark, 
              // '&:hover': { backgroundColor: theme.palette.error.main }
            })
          }}
        >
          {isDestructive ? 'Confirm Delete' : 'Confirm'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

ConfirmationDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  title: PropTypes.string.isRequired,
  message: PropTypes.string.isRequired,
  onConfirm: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
  isDestructive: PropTypes.bool
};

export default ConfirmationDialog; 
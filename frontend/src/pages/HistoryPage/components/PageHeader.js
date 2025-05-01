import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Link as RouterLink } from 'react-router';
import { 
  Box, 
  Typography, 
  Button, 
  Chip,
  useMediaQuery, 
  useTheme,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Stack,
  ButtonGroup
} from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import AddIcon from '@mui/icons-material/Add';
import UploadIcon from '@mui/icons-material/Upload';
import DownloadIcon from '@mui/icons-material/Download';
import ClearAllIcon from '@mui/icons-material/ClearAll';
import CloudDoneIcon from '@mui/icons-material/CloudDone';
import SettingsIcon from '@mui/icons-material/Settings';

import { PageHeaderWrapper, ActionButtonsWrapper } from '../styledComponents';

/**
 * Component for the page header with title and action buttons
 * @param {Object} props - Component props
 * @param {boolean} props.hasEntries - Whether there are any entries
 * @param {Function} props.onImport - Handler for import button click
 * @param {Function} props.onExport - Handler for export button click
 * @param {Function} props.onClear - Handler for clear button click
 * @param {boolean} [props.isLoading] - Optional: Indicates if initial data is loading
 * @param {boolean} [props.isProcessing] - Optional: Indicates if a bulk action is in progress
 * @returns {JSX.Element} Page header component
 */
const PageHeader = ({ hasEntries, onImport, onExport, onClear, isLoading = false, isProcessing = false }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);

  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleImportClick = () => {
    onImport();
    handleMenuClose();
  };

  const handleExportClick = () => {
    onExport();
    handleMenuClose();
  };

  const handleClearClick = () => {
    onClear();
    handleMenuClose();
  };

  return (
    <PageHeaderWrapper>
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', mb: { xs: 2, sm: 0 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <HistoryIcon sx={{ mr: 1, fontSize: { xs: 28, sm: 32 }, color: 'primary.main' }} />
          <Typography variant="h4" component="h1" sx={{ 
            fontWeight: 'bold',
            fontSize: { xs: '1.75rem', sm: '2rem', md: '2.125rem' }
          }}>
            History
          </Typography>
          <Tooltip title="History is synchronized with your account" arrow>
            <CloudDoneIcon color="action" sx={{ ml: 1, fontSize: '1.25rem' }} />
          </Tooltip>
        </Box>
      </Box>
      
      <ActionButtonsWrapper 
        direction={{ xs: 'column', sm: 'row' }} 
        spacing={{ xs: 1, sm: 1.5 }}
        alignItems="center"
      >
        <ButtonGroup variant="outlined" size="small" aria-label="History management actions" disabled={isLoading || isProcessing}>
          <Button
            startIcon={<UploadIcon />}
            onClick={onImport}
            sx={{ textTransform: 'none' }}
          >
            Import
          </Button>
          <Button
            startIcon={<DownloadIcon />}
            onClick={onExport}
            disabled={!hasEntries || isLoading || isProcessing}
            sx={{ textTransform: 'none' }}
          >
            Export All
          </Button>
          <Button
            color="error"
            startIcon={<ClearAllIcon />}
            onClick={onClear}
            disabled={!hasEntries || isLoading || isProcessing}
            sx={{ textTransform: 'none' }}
          >
            Clear All
          </Button>
        </ButtonGroup>
        
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          component={RouterLink}
          to="/generator"
          fullWidth={isMobile}
          size="small"
          sx={{ textTransform: 'none' }}
        >
          Create New Path
        </Button>
      </ActionButtonsWrapper>
    </PageHeaderWrapper>
  );
};

PageHeader.propTypes = {
  hasEntries: PropTypes.bool.isRequired,
  onImport: PropTypes.func.isRequired,
  onExport: PropTypes.func.isRequired,
  onClear: PropTypes.func.isRequired,
  isLoading: PropTypes.bool,
  isProcessing: PropTypes.bool
};

export default PageHeader; 
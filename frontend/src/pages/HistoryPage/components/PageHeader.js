import React from 'react';
import PropTypes from 'prop-types';
import { Link as RouterLink } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Button, 
  Chip, 
  useMediaQuery, 
  useTheme 
} from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import AddIcon from '@mui/icons-material/Add';
import UploadIcon from '@mui/icons-material/Upload';
import DownloadIcon from '@mui/icons-material/Download';
import ClearAllIcon from '@mui/icons-material/ClearAll';
import StorageIcon from '@mui/icons-material/Storage';

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
  
  return (
    <PageHeaderWrapper>
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <HistoryIcon sx={{ mr: 1, fontSize: { xs: 24, sm: 32 }, color: 'primary.main' }} />
          <Typography variant="h4" component="h1" sx={{ 
            fontWeight: 'bold',
            fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' }
          }}>
            Learning Path History
          </Typography>
        </Box>
        <Chip
          icon={<StorageIcon />}
          label="Synchronized with your account"
          size="small"
          color="primary"
          variant="outlined"
          sx={{ mt: 1, mb: 1 }}
        />
      </Box>
      
      <ActionButtonsWrapper 
        direction={{ xs: 'column', sm: 'row' }} 
        spacing={{ xs: 1, sm: 2 }}
      >
        <Button
          variant="outlined"
          startIcon={<UploadIcon />}
          onClick={onImport}
          fullWidth={isMobile}
          size="small"
          disabled={isLoading || isProcessing}
        >
          Import
        </Button>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={onExport}
          disabled={!hasEntries || isLoading || isProcessing}
          fullWidth={isMobile}
          size="small"
        >
          Export All
        </Button>
        <Button
          variant="outlined"
          color="error"
          startIcon={<ClearAllIcon />}
          onClick={onClear}
          disabled={!hasEntries || isLoading || isProcessing}
          fullWidth={isMobile}
          size="small"
        >
          Clear All
        </Button>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          component={RouterLink}
          to="/generator"
          fullWidth={isMobile}
          size="small"
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
import React from 'react';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router';
import {
  Typography,
  Box,
  CardContent,
  Button,
  Chip,
  CircularProgress,
  useTheme,
  Tooltip,
  Grid
} from '@mui/material';
import PlayCircleOutlineIcon from '@mui/icons-material/PlayCircleOutline';
import HourglassTopIcon from '@mui/icons-material/HourglassTop';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import VisibilityIcon from '@mui/icons-material/Visibility';

import { formatDateDistance } from '../utils'; // Assuming a utility function like formatDate
import { StyledCard } from '../styledComponents'; // Use the same styled card

/**
 * Card component for displaying an active course generation task
 * @param {Object} props - Component props
 * @param {Object} props.entry - Active generation task data (with isActive: true)
 * @param {boolean} props.virtualized - Whether the card is rendered in a virtualized list
 * @returns {JSX.Element} Active generation card component
 */
const ActiveGenerationCard = ({ entry, virtualized = false }) => {
  const navigate = useNavigate();
  const theme = useTheme();

  const handleViewProgress = () => {
    navigate(`/generating/${entry.task_id}`);
  };

  const getStatusChip = () => {
    switch (entry.status) {
      case 'PENDING':
        return (
          <Chip
            icon={<HourglassTopIcon fontSize="small" />}
            label="Pending"
            size="small"
            color="warning"
            variant="outlined"
          />
        );
      case 'RUNNING':
        return (
          <Chip
            icon={<CircularProgress size={14} sx={{ mr: 0.5 }} color="inherit" />}
            label="Processing"
            size="small"
            color="info"
            variant="outlined"
          />
        );
      case 'COMPLETED': // Should ideally not show here, but handle just in case
         return (
          <Chip
            icon={<CheckCircleOutlineIcon fontSize="small" />}
            label="Completed"
            size="small"
            color="success"
            variant="outlined"
          />
        );
      case 'FAILED': // Should ideally not show here, but handle just in case
         return (
          <Chip
            icon={<ErrorOutlineIcon fontSize="small" />}
            label="Failed"
            size="small"
            color="error"
            variant="outlined"
          />
        );
      default:
        return <Chip label={entry.status} size="small" />; 
    }
  };

  // Virtualized rendering doesn't need Grid wrapper
  const CardWrapper = virtualized ? Box : Grid;
  const wrapperProps = virtualized ? { sx: { height: '100%' } } : { item: true, xs: 12, sm: 6, md: 4, lg: 3, xl: 2 }; // Added xl breakpoint

  return (
    <CardWrapper {...wrapperProps}>
      <StyledCard 
        variant="outlined" 
        sx={{
          height: '100%', 
          borderLeft: `4px solid ${theme.palette.info.main}`, // Thicker border
          backgroundColor: theme.palette.action.hover // Subtle background tint
        }}
        onClick={handleViewProgress} // Make the whole card clickable
      >
        <CardContent sx={{ flexGrow: 1, p: { xs: 1, sm: 1.5 }, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h6" sx={{ 
              fontWeight: 'bold', // Increased weight
              fontSize: { xs: '1rem', sm: '1.1rem' }, // Slightly larger -> Adjusted to match HistoryEntryCard
              overflow: 'hidden', 
              textOverflow: 'ellipsis', 
              // whiteSpace: 'nowrap', // Allow wrapping
              display: '-webkit-box',
              WebkitLineClamp: 2, // Limit to 2 lines
              WebkitBoxOrient: 'vertical',
              lineHeight: 1.3, // Adjust line height for 2 lines
              mb: 0.5 // Reduced margin
            }}>
              {entry.request_topic || 'Processing Request...'}
            </Typography>
            
            <Typography variant="body2" color="text.secondary" gutterBottom fontSize={{ xs: '0.75rem', sm: '0.8rem' }} sx={{ mb: 1 }}>
              Started: {formatDateDistance(entry.created_at)}
            </Typography>

            <Box sx={{ mt: 1, mb: 1.5 }}> {/* Adjusted margins */}
              {getStatusChip()}
            </Box>
          </Box>

          <Box sx={{ mt: 1.5, display: 'flex', justifyContent: 'flex-end' }}> {/* Adjusted margin */}
            <Button // Make button more prominent
                startIcon={<VisibilityIcon />}
                onClick={handleViewProgress}
                size="small"
                variant="contained" // Changed to contained
                color="primary"
                sx={{ textTransform: 'none' }} // Prevent all caps
            >
              View Progress
            </Button>
          </Box>
        </CardContent>
      </StyledCard>
    </CardWrapper>
  );
};

ActiveGenerationCard.propTypes = {
  entry: PropTypes.shape({
    task_id: PropTypes.string.isRequired,
    status: PropTypes.string.isRequired,
    created_at: PropTypes.oneOfType([PropTypes.string, PropTypes.object]).isRequired,
    request_topic: PropTypes.string,
    isActive: PropTypes.bool // Flag indicating it's an active task
  }).isRequired,
  virtualized: PropTypes.bool
};

export default ActiveGenerationCard; 
import React from 'react';
import PropTypes from 'prop-types';
import { Link as RouterLink } from 'react-router';
import { Box, Typography, Button } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import { helpTexts } from '../../../constants/helpTexts';

/**
 * Component to display when there are no history entries
 * @param {Object} props - Component props
 * @param {Function} props.onClearFilters - Handler for clearing filters (optional)
 * @param {boolean} props.hasFilters - Whether filters are applied
 * @returns {JSX.Element} Empty state component
 */
const EmptyState = ({ onClearFilters, hasFilters = false }) => {
  return (
    <Box sx={{ textAlign: 'center', py: { xs: 3, sm: 5 } }}>
      <Typography variant="h6" color="text.secondary" gutterBottom>
        {hasFilters 
          ? 'No courses match your filters' 
          : 'No courses found in your history'}
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        {hasFilters
          ? 'Try adjusting your search or filters.'
          : helpTexts.historyEmptyState}
      </Typography>
      
      {hasFilters && onClearFilters && (
        <Button 
          variant="outlined" 
          onClick={onClearFilters}
          sx={{ mt: 2, mr: 2 }}
        >
          Clear Filters
        </Button>
      )}
      
      <Button
        variant="contained"
        color="primary"
        startIcon={<AddIcon />}
        component={RouterLink}
        to="/generator"
        sx={{ mt: 2 }}
      >
        Create New Course
      </Button>
    </Box>
  );
};

EmptyState.propTypes = {
  onClearFilters: PropTypes.func,
  hasFilters: PropTypes.bool
};

export default EmptyState; 
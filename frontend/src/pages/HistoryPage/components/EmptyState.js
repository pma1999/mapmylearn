import React from 'react';
import PropTypes from 'prop-types';
import { Link as RouterLink } from 'react-router-dom';
import { Box, Typography, Button } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';

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
          ? 'No learning paths match your filters' 
          : 'No learning paths found'}
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        {hasFilters
          ? 'Try adjusting your filters or create a new learning path.'
          : 'Create your first learning path or import one to get started.'}
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
        Create Learning Path
      </Button>
    </Box>
  );
};

EmptyState.propTypes = {
  onClearFilters: PropTypes.func,
  hasFilters: PropTypes.bool
};

export default EmptyState; 
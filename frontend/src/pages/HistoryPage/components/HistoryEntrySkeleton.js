import React, { memo } from 'react';
import PropTypes from 'prop-types';
import {
  Card,
  CardContent,
  Skeleton,
  Grid,
  Box,
  Divider
} from '@mui/material';

/**
 * Skeleton loading component for history entries
 * @param {Object} props - Component props
 * @param {number} props.count - Number of skeletons to display
 * @param {boolean} props.virtualized - Whether the skeleton is for virtualized list
 * @returns {JSX.Element} History entry skeleton
 */
const HistoryEntrySkeleton = memo(({ count = 1, virtualized = false }) => {
  // Animation delay factors for staggered loading effect
  const getAnimationDelay = (index) => {
    return `${(index % 5) * 0.1}s`;
  };
  
  const SkeletonContent = ({ index }) => (
    <CardContent sx={{ p: { xs: 2, md: virtualized ? 2 : 3 } }}>
      <Skeleton 
        variant="text" 
        width="70%" 
        height={40} 
        animation="wave"
        sx={{ animationDelay: getAnimationDelay(index) }}
      />
      <Skeleton 
        variant="text" 
        width="40%" 
        animation="wave"
        sx={{ animationDelay: getAnimationDelay(index) }}
      />
      <Skeleton 
        variant="text" 
        width="60%" 
        animation="wave"
        sx={{ animationDelay: getAnimationDelay(index) }}
      />
      <Box sx={{ mt: 1, mb: 2, display: 'flex', flexWrap: 'wrap' }}>
        <Skeleton 
          variant="rectangular" 
          width={120} 
          height={24} 
          sx={{ borderRadius: 4, mr: 1, animationDelay: getAnimationDelay(index) }} 
          animation="wave"
        />
        <Skeleton 
          variant="rectangular" 
          width={100} 
          height={24} 
          sx={{ borderRadius: 4, animationDelay: getAnimationDelay(index) }}
          animation="wave"
        />
      </Box>
      <Skeleton 
        variant="rectangular" 
        height={80} 
        animation="wave"
        sx={{ animationDelay: getAnimationDelay(index) }}
      />
      <Divider sx={{ my: 2 }} />
      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Skeleton 
          variant="rectangular" 
          width={100} 
          height={30} 
          sx={{ borderRadius: 1, animationDelay: getAnimationDelay(index) }}
          animation="wave"
        />
        <Box>
          <Skeleton 
            variant="circular" 
            width={24} 
            height={24} 
            sx={{ display: 'inline-block', mr: 1, animationDelay: getAnimationDelay(index) }}
            animation="wave"
          />
          <Skeleton 
            variant="circular" 
            width={24} 
            height={24} 
            sx={{ display: 'inline-block', animationDelay: getAnimationDelay(index) }}
            animation="wave"
          />
        </Box>
      </Box>
    </CardContent>
  );
  
  if (virtualized) {
    // For virtualized lists, don't wrap in Grid
    return Array.from(new Array(count)).map((_, index) => (
      <Card key={index} variant="outlined" sx={{ height: '100%' }}>
        <SkeletonContent index={index} />
      </Card>
    ));
  }
  
  // Standard grid layout
  return Array.from(new Array(count)).map((_, index) => (
    <Grid item xs={12} sm={6} md={4} key={index}>
      <Card variant="outlined" sx={{ height: '100%' }}>
        <SkeletonContent index={index} />
      </Card>
    </Grid>
  ));
});

HistoryEntrySkeleton.propTypes = {
  count: PropTypes.number,
  virtualized: PropTypes.bool
};

export default HistoryEntrySkeleton; 
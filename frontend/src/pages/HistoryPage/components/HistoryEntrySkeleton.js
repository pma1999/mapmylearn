import React, { memo } from 'react';
import PropTypes from 'prop-types';
import {
  Card,
  CardContent,
  Skeleton,
  Box,
  Divider,
  Stack
} from '@mui/material';

/**
 * Skeleton loading component for a single history entry.
 * Designed to mimic the structure and spacing of HistoryEntryCard.
 */
const HistoryEntrySkeletonInternal = memo(({ index }) => {
  // Animation delay factors for staggered loading effect (optional)
  const getAnimationDelay = (idx) => {
    return `${(idx % 5) * 0.1}s`; // Use idx passed from parent grid
  };

  // Mimic the structure of HistoryEntryCard
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent sx={{ p: { xs: 1, sm: 1.5 }, display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Top Section */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
          {/* Title Skeleton - now for 2 lines */}
          <Skeleton 
            variant="text" 
            width="70%" 
            height={40} // Adjust height for two-line title
            animation="wave"
            sx={{ animationDelay: getAnimationDelay(index), mb: 0.5 }} // Reduced margin bottom
          />
          {/* Icons Skeleton */}
          <Box sx={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
             <Skeleton variant="circular" width={20} height={20} sx={{ p: 0.5, animationDelay: getAnimationDelay(index) }} animation="wave" />
             <Skeleton variant="circular" width={20} height={20} sx={{ p: 0.5, ml: 0.5, animationDelay: getAnimationDelay(index) }} animation="wave" />
          </Box>
        </Box>

        {/* Info Section: Dates */}
        <Stack direction="row" spacing={1} sx={{ mb: 1, flexWrap: 'wrap' }} alignItems="center">
          <Skeleton variant="text" width="80px" height={16} animation="wave" sx={{ animationDelay: getAnimationDelay(index) }} />
          <Skeleton variant="text" width="80px" height={16} animation="wave" sx={{ animationDelay: getAnimationDelay(index) }} />
        </Stack>
        
        {/* Info Section: Chips */}
        <Stack direction="row" spacing={0.5} sx={{ mb: 1, flexWrap: 'wrap' }} alignItems="center">
           <Skeleton variant="rounded" width={100} height={22} sx={{ borderRadius: '16px', animationDelay: getAnimationDelay(index) }} animation="wave" />
           <Skeleton variant="rounded" width={90} height={22} sx={{ borderRadius: '16px', animationDelay: getAnimationDelay(index) }} animation="wave" />
        </Stack>

        {/* Tags Section Skeleton - reduced display */}
        <Box sx={{ mb: 1 }}>
            <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap' }}>
                <Skeleton variant="rounded" width={70} height={22} sx={{ borderRadius: '16px', animationDelay: getAnimationDelay(index) }} animation="wave" />
                <Skeleton variant="rounded" width={60} height={22} sx={{ borderRadius: '16px', animationDelay: getAnimationDelay(index) }} animation="wave" />
            </Stack>
            {/* Skeleton for the Add Tag button area */}
            <Skeleton variant="text" width={60} height={20} sx={{ mt: 0.5, animationDelay: getAnimationDelay(index) }} animation="wave"/> 
        </Box>

        {/* Spacer */}
        <Box sx={{ flexGrow: 1 }} />

        {/* Bottom Action Skeleton */}
        <Divider sx={{ my: 1 }} />
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
           <Skeleton variant="rounded" width={80} height={28} sx={{ borderRadius: 1, animationDelay: getAnimationDelay(index) }} animation="wave" />
        </Box>
      </CardContent>
    </Card>
  );
});

HistoryEntrySkeletonInternal.propTypes = {
  index: PropTypes.number.isRequired,
};

// Keep the export name the same for compatibility
const HistoryEntrySkeleton = HistoryEntrySkeletonInternal;

export default HistoryEntrySkeleton; 
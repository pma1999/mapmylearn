import React from 'react';
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
 * @returns {JSX.Element} History entry skeleton
 */
const HistoryEntrySkeleton = ({ count = 1 }) => {
  return Array.from(new Array(count)).map((_, index) => (
    <Grid item xs={12} sm={6} md={4} key={index}>
      <Card variant="outlined" sx={{ height: '100%' }}>
        <CardContent sx={{ p: { xs: 2, md: 3 } }}>
          <Skeleton variant="text" width="70%" height={40} />
          <Skeleton variant="text" width="40%" />
          <Skeleton variant="text" width="60%" />
          <Box sx={{ mt: 1, mb: 2, display: 'flex', flexWrap: 'wrap' }}>
            <Skeleton variant="rectangular" width={120} height={24} sx={{ borderRadius: 4, mr: 1 }} />
            <Skeleton variant="rectangular" width={100} height={24} sx={{ borderRadius: 4 }} />
          </Box>
          <Skeleton variant="rectangular" height={80} />
          <Divider sx={{ my: 2 }} />
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Skeleton variant="rectangular" width={100} height={30} sx={{ borderRadius: 1 }} />
            <Box>
              <Skeleton variant="circular" width={24} height={24} sx={{ display: 'inline-block', mr: 1 }} />
              <Skeleton variant="circular" width={24} height={24} sx={{ display: 'inline-block' }} />
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Grid>
  ));
};

HistoryEntrySkeleton.propTypes = {
  count: PropTypes.number
};

export default HistoryEntrySkeleton; 
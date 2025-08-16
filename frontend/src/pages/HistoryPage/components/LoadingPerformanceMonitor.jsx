import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Grid,
  IconButton,
  Collapse,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import SpeedIcon from '@mui/icons-material/Speed';
import MemoryIcon from '@mui/icons-material/Memory';
import NetworkCheckIcon from '@mui/icons-material/NetworkCheck';
import ErrorIcon from '@mui/icons-material/Error';

/**
 * Development-only performance monitoring component for HistoryPage loading optimization
 * Displays detailed metrics about loading states, cache usage, and performance statistics
 * Only renders in development environment
 * 
 * @param {Object} props - Component props
 * @param {Object} props.loadingState - Enhanced loading state object
 * @param {Object} props.stats - Performance statistics object
 * @param {number} props.entriesCount - Current number of entries displayed
 * @param {Object} props.pagination - Pagination state
 * @param {string} props.error - Error message if any
 * @returns {JSX.Element|null} Performance monitor component or null in production
 */
const LoadingPerformanceMonitor = ({
  loadingState,
  stats,
  entriesCount,
  pagination,
  error
}) => {
  const [expanded, setExpanded] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState([]);
  const [lastUpdateTime, setLastUpdateTime] = useState(Date.now());

  // Only render in development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  // Track loading events for performance analysis
  useEffect(() => {
    const timestamp = Date.now();
    setLastUpdateTime(timestamp);

    // Add to loading history for trend analysis
    setLoadingHistory(prev => {
      const newEntry = {
        timestamp,
        loadingState: { ...loadingState },
        stats: { ...stats },
        entriesCount,
        error: error || null
      };

      // Keep only last 10 entries to prevent memory leaks
      return [...prev.slice(-9), newEntry];
    });
  }, [loadingState, stats, entriesCount, error]);

  const getLoadingStateColor = () => {
    if (loadingState.initialLoading) return 'primary';
    if (loadingState.backgroundRefreshing) return 'info';
    if (loadingState.showingCache) return 'warning';
    return 'success';
  };

  const getLoadingStateText = () => {
    if (loadingState.initialLoading) return 'Initial Loading';
    if (loadingState.backgroundRefreshing) return 'Background Refresh';
    if (loadingState.showingCache) return 'Showing Cache';
    return 'Idle';
  };

  const formatDuration = (ms) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getPerformanceRating = () => {
    if (!stats.loadTime) return null;
    
    if (stats.fromCache) return { rating: 'Excellent', color: 'success' };
    if (stats.loadTime < 500) return { rating: 'Excellent', color: 'success' };
    if (stats.loadTime < 1000) return { rating: 'Good', color: 'info' };
    if (stats.loadTime < 2000) return { rating: 'Fair', color: 'warning' };
    return { rating: 'Poor', color: 'error' };
  };

  const performanceRating = getPerformanceRating();

  return (
    <Card sx={{ mt: 2, border: '2px solid', borderColor: 'primary.main' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SpeedIcon color="primary" />
            <Typography variant="h6" color="primary">
              Loading Performance Monitor
            </Typography>
            <Chip 
              label={getLoadingStateText()} 
              color={getLoadingStateColor()} 
              size="small" 
            />
          </Box>
          <IconButton onClick={() => setExpanded(!expanded)}>
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        {/* Quick Stats Row */}
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Entries Loaded
              </Typography>
              <Typography variant="h6">
                {entriesCount}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Load Time
              </Typography>
              <Typography variant="h6">
                {stats.loadTime ? formatDuration(stats.loadTime) : 'N/A'}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Cache Status
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                <MemoryIcon fontSize="small" />
                <Typography variant="h6">
                  {stats.fromCache ? 'Hit' : 'Miss'}
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Performance
              </Typography>
              {performanceRating && (
                <Chip 
                  label={performanceRating.rating} 
                  color={performanceRating.color} 
                  size="small" 
                />
              )}
            </Box>
          </Grid>
        </Grid>

        <Collapse in={expanded}>
          <Box sx={{ mt: 2 }}>
            
            {/* Error Display */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }} icon={<ErrorIcon />}>
                <Typography variant="body2">
                  <strong>Error:</strong> {error}
                </Typography>
              </Alert>
            )}

            {/* Detailed Statistics */}
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Loading State Details
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell>Initial Loading</TableCell>
                        <TableCell>
                          <Chip 
                            label={loadingState.initialLoading ? 'Yes' : 'No'}
                            color={loadingState.initialLoading ? 'primary' : 'default'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Background Refreshing</TableCell>
                        <TableCell>
                          <Chip 
                            label={loadingState.backgroundRefreshing ? 'Yes' : 'No'}
                            color={loadingState.backgroundRefreshing ? 'info' : 'default'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Showing Cache</TableCell>
                        <TableCell>
                          <Chip 
                            label={loadingState.showingCache ? 'Yes' : 'No'}
                            color={loadingState.showingCache ? 'warning' : 'default'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Performance Metrics
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell>Client Load Time</TableCell>
                        <TableCell>{stats.loadTime ? formatDuration(stats.loadTime) : 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Server Processing</TableCell>
                        <TableCell>{stats.serverTime ? formatDuration(stats.serverTime) : 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Cache Source</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <MemoryIcon fontSize="small" />
                            {stats.fromCache ? 'Cache Hit' : 'Network'}
                          </Box>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Parallel Loading</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <NetworkCheckIcon fontSize="small" />
                            {stats.parallelLoad ? 'Enabled' : 'Disabled'}
                          </Box>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Total Entries</TableCell>
                        <TableCell>{pagination?.total || stats.total || 'N/A'}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
            </Grid>

            {/* Loading History */}
            {loadingHistory.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Recent Loading Events (Last {loadingHistory.length})
                </Typography>
                <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 200 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Time</TableCell>
                        <TableCell>State</TableCell>
                        <TableCell>Load Time</TableCell>
                        <TableCell>Entries</TableCell>
                        <TableCell>Cache</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {loadingHistory.slice().reverse().map((event, index) => (
                        <TableRow key={event.timestamp}>
                          <TableCell>
                            {new Date(event.timestamp).toLocaleTimeString()}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={
                                event.loadingState.initialLoading ? 'Initial' :
                                event.loadingState.backgroundRefreshing ? 'Refresh' :
                                event.loadingState.showingCache ? 'Cache' : 'Idle'
                              }
                              size="small"
                              color={
                                event.loadingState.initialLoading ? 'primary' :
                                event.loadingState.backgroundRefreshing ? 'info' :
                                event.loadingState.showingCache ? 'warning' : 'success'
                              }
                            />
                          </TableCell>
                          <TableCell>
                            {event.stats.loadTime ? formatDuration(event.stats.loadTime) : 'N/A'}
                          </TableCell>
                          <TableCell>{event.entriesCount}</TableCell>
                          <TableCell>
                            {event.stats.fromCache ? '✓' : '✗'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}

            <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
              Last updated: {new Date(lastUpdateTime).toLocaleString()}
            </Typography>
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};

LoadingPerformanceMonitor.propTypes = {
  loadingState: PropTypes.shape({
    initialLoading: PropTypes.bool.isRequired,
    backgroundRefreshing: PropTypes.bool.isRequired,
    showingCache: PropTypes.bool.isRequired
  }).isRequired,
  stats: PropTypes.shape({
    loadTime: PropTypes.number,
    serverTime: PropTypes.number,
    fromCache: PropTypes.bool,
    parallelLoad: PropTypes.bool,
    total: PropTypes.number
  }).isRequired,
  entriesCount: PropTypes.number.isRequired,
  pagination: PropTypes.shape({
    total: PropTypes.number,
    page: PropTypes.number,
    perPage: PropTypes.number
  }),
  error: PropTypes.string
};

export default LoadingPerformanceMonitor;

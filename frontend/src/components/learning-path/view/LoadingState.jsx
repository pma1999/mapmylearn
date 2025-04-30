import React from 'react';
import PropTypes from 'prop-types';
import { 
  Container, 
  Paper, 
  Typography, 
  Box, 
  LinearProgress,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Collapse,
  Button,
  useTheme
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ModuleIcon from '@mui/icons-material/AccountTree';

/**
 * Component to display loading and progress updates for learning path generation.
 * Shows current phase, overall progress, latest message, and optional preview/history.
 * 
 * @param {Object} props Component props
 * @param {Array} props.progressMessages Progress messages from SSE
 * @param {boolean} props.isReconnecting - Flag indicating if reconnecting
 * @param {number} props.retryAttempt - Current retry attempt number
 * @returns {JSX.Element} Loading state component
 */
const LoadingState = ({ progressMessages = [], isReconnecting = false, retryAttempt = 0 }) => {
  const theme = useTheme();
  const [showHistory, setShowHistory] = React.useState(false);
  
  const storedTopic = sessionStorage.getItem('currentTopic') || 'your topic';

  // Get the latest update object
  const latestUpdate = progressMessages.length > 0 
      ? progressMessages[progressMessages.length - 1] 
      : null;

  // Extract relevant data from the latest update
  const overallProgress = latestUpdate?.overall_progress; // 0.0 to 1.0
  const progressPercent = overallProgress !== null && !isNaN(overallProgress) ? overallProgress * 100 : null;
  const currentPhase = latestUpdate?.phase || 'Initialization';
  const latestMessage = latestUpdate?.message || 'Initializing generation...';
  const previewModules = latestUpdate?.preview_data?.modules;
  
  // Determine progress bar variant and value
  const progressBarVariant = progressPercent !== null ? "determinate" : "indeterminate";
  const progressBarValue = progressPercent !== null ? progressPercent : undefined;

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };
  
  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4 } }
  };

  const handleToggleHistory = () => {
      setShowHistory(prev => !prev);
  };

  return (
    <Container maxWidth="md" sx={{ py: { xs: 3, md: 4 } }}> 
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        layout
      >
        {/* Main Loading Box */}
        <motion.div variants={itemVariants} layout>
          <Paper
            elevation={3} 
            sx={{
              p: { xs: 3, sm: 4 },
              borderRadius: 3,
              textAlign: 'center',
              mx: 'auto',
            }}
          >
            <Typography variant="h5" component="h2" gutterBottom fontWeight="bold">
              Building Path: "{storedTopic}"
            </Typography>
            
            {/* Phase Indicator */}
            <Box sx={{ my: 2 }}>
                <Chip 
                    label={`Phase: ${currentPhase.replace(/_/g, ' ').toUpperCase()}`}
                    color="secondary"
                    variant="outlined"
                    size="small"
                />
            </Box>
            
            {/* Latest Message & Reconnection Status */}
            <Typography variant="body1" color="text.secondary" paragraph sx={{ minHeight: '2.5em', mb: 3 }}> 
                <AnimatePresence mode="wait">
                    <motion.span
                        key={latestMessage}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.3 }}
                    >
                        {latestMessage}
                    </motion.span>
                </AnimatePresence>
              {isReconnecting && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <Box sx={{ mt: 1, color: theme.palette.warning.dark, fontWeight: 'medium' }}>
                        <Typography variant="body2" component="span">
                            Connection issue. Reconnecting... (Attempt {retryAttempt}/{MAX_RETRIES})
                        </Typography>
                    </Box>
                 </motion.div>
              )}
            </Typography>
            
            {/* Progress Bar */}
            <Box sx={{ width: '100%', my: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
                {progressBarVariant === 'indeterminate' && !isReconnecting && (
                     <CircularProgress size={20} thickness={4} color="primary" />
                )}
                <LinearProgress 
                    variant={progressBarVariant}
                    value={progressBarValue}
                    sx={{ 
                        flexGrow: 1,
                        height: 10, 
                        borderRadius: 5,
                        backgroundColor: theme.palette.grey[300],
                        '& .MuiLinearProgress-bar': {
                            background: progressBarVariant === 'determinate' 
                                ? theme.palette.primary.main 
                                : `linear-gradient(90deg, ${theme.palette.primary.light}, ${theme.palette.primary.main})`, 
                            borderRadius: 5,
                            transition: progressBarVariant === 'determinate' ? 'transform .4s linear' : 'none',
                        }
                    }} 
                />
                {progressPercent !== null && (
                     <Typography variant="body2" sx={{ fontWeight: 'medium', color: 'text.secondary', minWidth: '40px' }}>
                       {Math.round(progressPercent)}%
                     </Typography>
                )}
                {progressBarVariant === 'indeterminate' && isReconnecting && (
                     <CircularProgress size={20} thickness={4} color="warning" />
                )}
            </Box>

            {/* Preview Data (Optional) */}
            {previewModules && previewModules.length > 0 && (
                <motion.div variants={itemVariants} layout>
                     <Typography variant="caption" display="block" sx={{ mt: 2, mb: 1, color: 'text.secondary' }}>
                         Drafting Modules...
                     </Typography>
                    <List dense disablePadding sx={{ maxHeight: 150, overflowY: 'auto', textAlign: 'left', border: `1px solid ${theme.palette.divider}`, borderRadius: 1 }}>
                        {previewModules.map((mod, index) => (
                             <ListItem key={mod.title || index} dense>
                                 <ListItemIcon sx={{ minWidth: 32}}><ModuleIcon fontSize="small" color="action" /></ListItemIcon>
                                <ListItemText 
                                    primary={mod.title || `Module ${index + 1}`}
                                    primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                                />
                             </ListItem>
                        ))}
                    </List>
                 </motion.div>
            )}

          </Paper>
        </motion.div>

        {/* Detailed Progress History (Collapsible) */}
        {progressMessages.length > 1 && (
            <motion.div layout>
                 <Box sx={{ mt: 3, textAlign: 'center' }}> 
                     <Button 
                         size="small"
                         onClick={handleToggleHistory}
                         endIcon={showHistory ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                     >
                         {showHistory ? 'Hide Details' : 'Show Details'}
                     </Button>
                 </Box>
                <Collapse in={showHistory} timeout="auto" unmountOnExit>
                    <Box sx={{ mt: 1, maxWidth: 700, mx: 'auto' }}> 
                        {progressMessages.slice(0, -1).reverse().map((msg, index) => (
                            <motion.div 
                                key={msg.timestamp || index}
                                variants={itemVariants}
                                initial="hidden"
                                animate="visible"
                                exit="hidden"
                                transition={{ duration: 0.3, delay: index * 0.03 }} 
                            >
                                <Paper
                                    elevation={0}
                                    variant="outlined"
                                    sx={{
                                        p: 1.5, 
                                        mb: 1,
                                        borderRadius: 2,
                                        opacity: 0.85, 
                                        fontSize: '0.8rem',
                                        color: 'text.secondary'
                                    }}
                                >
                                     <Typography variant="caption" display="block" sx={{ float: 'right', color: 'text.disabled'}}>
                                         {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : ''}
                                     </Typography>
                                    {msg.phase && <Chip label={msg.phase} size="small" variant="outlined" sx={{ mr: 1, height: 'auto', fontSize: '0.65rem' }} />} 
                                    {msg.message}
                                </Paper>
                            </motion.div>
                        ))}
                    </Box>
                 </Collapse>
             </motion.div>
        )}

      </motion.div>
    </Container>
  );
};

// Define MAX_RETRIES within the component or import if defined elsewhere
const MAX_RETRIES = 5;

LoadingState.propTypes = {
  progressMessages: PropTypes.arrayOf(PropTypes.shape({
    message: PropTypes.string.isRequired,
    timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    phase: PropTypes.string,
    overall_progress: PropTypes.number,
    preview_data: PropTypes.object,
    action: PropTypes.string
  })),
  isReconnecting: PropTypes.bool, 
  retryAttempt: PropTypes.number, 
};

export default LoadingState; 
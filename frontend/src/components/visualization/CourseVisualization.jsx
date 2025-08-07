import React, { useState } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Button,
  Alert,
  CircularProgress,
  Typography,
  Paper,
  IconButton,
  Tooltip,
  useTheme
} from '@mui/material';
import SchemaIcon from '@mui/icons-material/Schema';
import RefreshIcon from '@mui/icons-material/Refresh';
import { motion, AnimatePresence } from 'framer-motion';

// Import the MermaidVisualization component
import MermaidVisualization from './MermaidVisualization';

// Import API utilities
import { api } from '../../services/api';

const CourseVisualization = ({
  pathId,
  pathData,
  topic,
  language = 'en',
  isPublicView = false,
  sx = {},
  ...props
}) => {
  const theme = useTheme();
  const [mermaidSyntax, setMermaidSyntax] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [hasGenerated, setHasGenerated] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);

  const handleGenerateVisualization = async () => {
    if (!pathId) {
      setError('No course ID provided');
      return;
    }

    setIsGenerating(true);
    setError('');

    try {
      const requestData = {
        language: language || 'en',
        ...(pathData && { path_data: pathData })
      };

      const response = await api.post(
        `/v1/learning-paths/${pathId}/course-visualization`,
        requestData
      );

      if (response.data.mermaid_syntax) {
        setMermaidSyntax(response.data.mermaid_syntax);
        setHasGenerated(true);
        setError('');
      } else if (response.data.message) {
        setError(response.data.message);
        setMermaidSyntax('');
      } else {
        setError('Failed to generate course visualization');
        setMermaidSyntax('');
      }
    } catch (err) {
      console.error('Course visualization generation error:', err);
      
      if (err.response?.status === 402) {
        setError('Insufficient credits to generate course visualization. Please purchase more credits.');
      } else if (err.response?.status === 404) {
        setError('Course not found or access denied.');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('An unexpected error occurred while generating the course visualization.');
      }
      setMermaidSyntax('');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRegenerateVisualization = async () => {
    if (!pathId) {
      setError('No course ID provided');
      return;
    }

    setIsRegenerating(true);
    setError('');

    try {
      const requestData = {
        language: language || 'en',
        ...(pathData && { path_data: pathData })
      };

      const response = await api.put(
        `/v1/learning-paths/${pathId}/course-visualization/regenerate`,
        requestData
      );

      if (response.data.mermaid_syntax) {
        setMermaidSyntax(response.data.mermaid_syntax);
        setHasGenerated(true);
        setError('');
      } else if (response.data.message) {
        setError(response.data.message);
        setMermaidSyntax('');
      } else {
        setError('Failed to regenerate course visualization');
        setMermaidSyntax('');
      }
    } catch (err) {
      console.error('Course visualization regeneration error:', err);
      
      if (err.response?.status === 402) {
        setError('Insufficient credits to regenerate course visualization. Please purchase more credits.');
      } else if (err.response?.status === 404) {
        setError('Course not found or access denied.');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('An unexpected error occurred while regenerating the course visualization.');
      }
      setMermaidSyntax('');
    } finally {
      setIsRegenerating(false);
    }
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.4,
        ease: "easeOut"
      }
    }
  };

  return (
    <Box sx={{ width: '100%', ...sx }} {...props}>
      <motion.div
        variants={cardVariants}
        initial="hidden"
        animate="visible"
      >
        <Paper
          elevation={0}
          sx={{
            p: 3,
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: 2,
            background: theme.palette.background.paper
          }}
        >
          {/* Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <SchemaIcon sx={{ color: theme.palette.primary.main, mr: 1.5, fontSize: 28 }} />
              <Typography variant="h6" component="h3" sx={{ fontWeight: 600 }}>
                Course Overview Visualization
              </Typography>
            </Box>
            
            {hasGenerated && !isPublicView && (
              <Tooltip title="Regenerate Visualization">
                <IconButton 
                  onClick={handleRegenerateVisualization}
                  disabled={isRegenerating}
                  sx={{ color: theme.palette.primary.main }}
                >
                  {isRegenerating ? <CircularProgress size={20} /> : <RefreshIcon />}
                </IconButton>
              </Tooltip>
            )}
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Generate an interactive diagram showing the complete course structure with modules and learning pathways.
            {!isPublicView && " This costs 1 credit."}
          </Typography>

          {/* Generate Button */}
          {!hasGenerated && !mermaidSyntax && (
            <Button
              variant="contained"
              onClick={handleGenerateVisualization}
              disabled={isGenerating || isPublicView}
              startIcon={isGenerating ? <CircularProgress size={20} /> : <SchemaIcon />}
              sx={{
                px: 3,
                py: 1.5,
                borderRadius: 2,
                fontWeight: 600,
                background: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.secondary.main} 90%)`,
                '&:hover': {
                  background: `linear-gradient(45deg, ${theme.palette.primary.dark} 30%, ${theme.palette.secondary.dark} 90%)`,
                  transform: 'translateY(-1px)',
                  boxShadow: theme.shadows[4]
                },
                '&:disabled': {
                  background: theme.palette.action.disabledBackground
                },
                transition: 'all 0.3s ease'
              }}
            >
              {isGenerating ? 'Generating Course Visualization...' : 'Generate Course Visualization'}
            </Button>
          )}

          {/* Loading State */}
          <AnimatePresence>
            {(isGenerating || isRegenerating) && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'center', 
                  alignItems: 'center', 
                  py: 4,
                  flexDirection: 'column'
                }}>
                  <CircularProgress size={40} sx={{ mb: 2 }} />
                  <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
                    {isRegenerating ? 'Regenerating course visualization...' : 'Analyzing course structure and generating visualization...'}
                    <br />
                    <Typography component="span" variant="caption" color="text.secondary">
                      This may take a moment
                    </Typography>
                  </Typography>
                </Box>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Error Display */}
          <AnimatePresence>
            {error && !isGenerating && !isRegenerating && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Alert 
                  severity="error" 
                  sx={{ mt: 2, mb: 2 }}
                  action={
                    !isPublicView && (
                      <Button 
                        color="inherit" 
                        size="small" 
                        onClick={() => {
                          setError('');
                          if (hasGenerated) {
                            handleRegenerateVisualization();
                          } else {
                            handleGenerateVisualization();
                          }
                        }}
                      >
                        Try Again
                      </Button>
                    )
                  }
                >
                  {error}
                </Alert>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Visualization Display */}
          <AnimatePresence>
            {mermaidSyntax && !isGenerating && !isRegenerating && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.5 }}
              >
                <Box sx={{ mt: 3 }}>
                  <MermaidVisualization
                    mermaidSyntax={mermaidSyntax}
                    title={`${topic} - Course Structure`}
                    sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 1 }}
                  />
                </Box>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Help Text */}
          {!hasGenerated && !isGenerating && !error && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
              💡 The course visualization will show the learning path structure, module relationships, and key milestones.
              {isPublicView && " Visualization is not available in public view."}
            </Typography>
          )}
        </Paper>
      </motion.div>
    </Box>
  );
};

CourseVisualization.propTypes = {
  pathId: PropTypes.string.isRequired,
  pathData: PropTypes.object,
  topic: PropTypes.string.isRequired,
  language: PropTypes.string,
  isPublicView: PropTypes.bool,
  sx: PropTypes.object
};

export default CourseVisualization;
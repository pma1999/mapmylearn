import React from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Typography,
  Button,
  Paper,
  Divider,
  Stack,
  useTheme,
  useMediaQuery,
  Tooltip
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import SaveIcon from '@mui/icons-material/Save';
import SchoolIcon from '@mui/icons-material/School';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import { motion } from 'framer-motion';
import InfoTooltip from '../../shared/InfoTooltip';
import { helpTexts } from '../../../constants/helpTexts';

/**
 * Header component for learning path display
 * 
 * @param {Object} props Component props 
 * @param {string} props.topic Learning path topic/title
 * @param {boolean} props.detailsHaveBeenSet Whether tags/favorites have been set
 * @param {boolean} props.isPdfReady Whether the PDF download is ready/enabled
 * @param {Function} props.onDownload Handler for JSON download
 * @param {Function} props.onDownloadPDF Handler for PDF download
 * @param {Function} props.onSaveToHistory Handler for opening save details dialog
 * @param {Function} props.onNewLearningPath Handler for creating a new learning path
 * @returns {JSX.Element} Header component
 */
const LearningPathHeader = ({ 
  topic, 
  detailsHaveBeenSet,
  isPdfReady,
  onDownload, 
  onDownloadPDF,
  onSaveToHistory, 
  onNewLearningPath 
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isMedium = useMediaQuery(theme.breakpoints.down('md'));

  // Animation variants
  const headerVariants = {
    hidden: { opacity: 0, y: -30 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.6,
        ease: "easeOut" 
      }
    }
  };
  
  const buttonContainerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { 
        staggerChildren: 0.1,
        delayChildren: 0.3
      }
    }
  };
  
  const buttonVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: { duration: 0.3 }
    }
  };

  return (
    <Paper 
      elevation={2} 
      sx={{ 
        p: { xs: 2, sm: 3, md: 4 }, 
        borderRadius: 2, 
        mb: 4,
        background: `linear-gradient(145deg, ${theme.palette.primary.light}10, ${theme.palette.background.paper})`,
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          right: 0,
          width: { xs: '120px', sm: '150px', md: '200px' },
          height: { xs: '120px', sm: '150px', md: '200px' },
          background: `linear-gradient(135deg, transparent 50%, ${theme.palette.primary.light}30 50%)`,
          zIndex: 0
        }}
      />
      
      <motion.div
        initial="hidden"
        animate="visible"
        variants={headerVariants}
      >
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <SchoolIcon 
              sx={{ 
                fontSize: { xs: 32, sm: 36, md: 40 }, 
                color: theme.palette.primary.main,
                mr: 2 
              }} 
            />
            <Typography 
              variant="h4" 
              component="h1" 
              sx={{ 
                fontWeight: 700,
                fontSize: { xs: '1.5rem', sm: '1.8rem', md: '2.125rem' },
                color: theme.palette.text.primary
              }}
            >
              Learning Path
            </Typography>
          </Box>
          
          <Box sx={{ mt: 2 }}>
            <Typography 
              variant="h5"
              color="primary"
              sx={{ 
                fontWeight: 600,
                fontSize: { xs: '1.25rem', sm: '1.5rem', md: '1.6rem' },
                mb: 2,
                wordBreak: 'break-word'
              }}
            >
              {topic}
            </Typography>
            
            <Divider sx={{ mt: 3, mb: 3 }} />
            
            <motion.div
              variants={buttonContainerVariants}
              initial="hidden"
              animate="visible"
            >
              {/* Mobile view - Stack buttons vertically */}
              {isMedium ? (
                <Stack direction="column" spacing={1.5} sx={{ width: '100%' }}>
                  <Box sx={{ display: 'flex', flexDirection: 'row', gap: 1 }}>
                    <motion.div variants={buttonVariants} sx={{ flex: 1 }}>
                      <Tooltip title="Download as JSON">
                        <Button
                          variant="outlined"
                          fullWidth
                          startIcon={<DownloadIcon />}
                          onClick={onDownload}
                          size={isMobile ? "small" : "medium"}
                        >
                          JSON
                        </Button>
                      </Tooltip>
                    </motion.div>
                    
                    <motion.div variants={buttonVariants} sx={{ flex: 1 }}>
                      <Tooltip title={!isPdfReady ? "PDF download available after generation completes" : "Download as PDF"}>
                        <span>
                          <Button
                            variant="outlined"
                            fullWidth
                            startIcon={<PictureAsPdfIcon />}
                            onClick={onDownloadPDF}
                            size={isMobile ? "small" : "medium"}
                            disabled={!isPdfReady}
                          >
                            PDF
                          </Button>
                        </span>
                      </Tooltip>
                    </motion.div>
                  </Box>
                  
                  <motion.div variants={buttonVariants}>
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                      <Button
                        variant="outlined"
                        fullWidth
                        color="secondary"
                        startIcon={<SaveIcon />}
                        onClick={onSaveToHistory}
                        disabled={detailsHaveBeenSet}
                        size={isMobile ? "small" : "medium"}
                      >
                        {detailsHaveBeenSet ? "Details Set" : "Save Details"}
                      </Button>
                      <InfoTooltip title={helpTexts.lphSaveTooltip} />
                    </Box>
                  </motion.div>
                  
                  <motion.div variants={buttonVariants}>
                    <Button
                      variant="contained"
                      fullWidth
                      color="primary"
                      startIcon={<BookmarkIcon />}
                      onClick={onNewLearningPath}
                      size={isMobile ? "small" : "medium"}
                    >
                      Create New Path
                    </Button>
                  </motion.div>
                </Stack>
              ) : (
                /* Desktop view - Horizontal button layout */
                <Stack direction="row" spacing={2} alignItems="center">
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <motion.div variants={buttonVariants}>
                      <Tooltip title="Download as JSON">
                        <Button
                          variant="outlined"
                          startIcon={<DownloadIcon />}
                          onClick={onDownload}
                        >
                          JSON
                        </Button>
                      </Tooltip>
                    </motion.div>
                    
                    <motion.div variants={buttonVariants}>
                      <Tooltip title={!isPdfReady ? "PDF download available after generation completes" : "Download as PDF"}>
                        <span>
                          <Button
                            variant="outlined"
                            startIcon={<PictureAsPdfIcon />}
                            onClick={onDownloadPDF}
                            disabled={!isPdfReady}
                          >
                            PDF
                          </Button>
                        </span>
                      </Tooltip>
                    </motion.div>
                  </Box>
                  
                  <motion.div variants={buttonVariants}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Button
                        variant="outlined"
                        color="secondary"
                        startIcon={<SaveIcon />}
                        onClick={onSaveToHistory}
                        disabled={detailsHaveBeenSet}
                      >
                        {detailsHaveBeenSet ? "Details Set" : "Save Details"}
                      </Button>
                      <InfoTooltip title={helpTexts.lphSaveTooltip} />
                    </Box>
                  </motion.div>
                  
                  <motion.div variants={buttonVariants}>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<BookmarkIcon />}
                      onClick={onNewLearningPath}
                    >
                      Create New Path
                    </Button>
                  </motion.div>
                </Stack>
              )}
            </motion.div>
          </Box>
        </Box>
      </motion.div>
    </Paper>
  );
};

LearningPathHeader.propTypes = {
  topic: PropTypes.string.isRequired,
  detailsHaveBeenSet: PropTypes.bool.isRequired,
  isPdfReady: PropTypes.bool.isRequired,
  onDownload: PropTypes.func.isRequired,
  onDownloadPDF: PropTypes.func.isRequired,
  onSaveToHistory: PropTypes.func.isRequired,
  onNewLearningPath: PropTypes.func.isRequired
};

export default LearningPathHeader; 
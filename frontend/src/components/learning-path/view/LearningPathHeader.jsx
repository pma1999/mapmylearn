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
  Tooltip,
  IconButton
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import SaveIcon from '@mui/icons-material/Save';
import SchoolIcon from '@mui/icons-material/School';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import MenuIcon from '@mui/icons-material/Menu';
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
 * @param {Function} [props.onOpenMobileNav] Optional handler to open mobile navigation
 * @param {boolean} [props.showMobileNavButton] Optional flag to show the mobile nav button
 * @returns {JSX.Element} Header component
 */
const LearningPathHeader = ({ 
  topic, 
  detailsHaveBeenSet,
  isPdfReady,
  onDownload, 
  onDownloadPDF,
  onSaveToHistory, 
  onNewLearningPath,
  onOpenMobileNav,
  showMobileNavButton
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
      elevation={0} 
      variant="outlined"
      sx={{ 
        p: { xs: 2, sm: 3 },
        borderRadius: 2,
        borderColor: theme.palette.divider,
        background: theme.palette.background.paper,
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      <motion.div
        initial="hidden"
        animate="visible"
        variants={headerVariants}
      >
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: { xs: 1.5, md: 2 }, justifyContent: 'space-between' }}>
            {showMobileNavButton && (
              <motion.div variants={buttonVariants}>
                <Tooltip title="Modules Navigation">
                  <IconButton 
                    color="primary"
                    onClick={onOpenMobileNav}
                    sx={{ mr: 1 }} 
                    aria-label="Open module navigation"
                  >
                    <MenuIcon />
                  </IconButton>
                </Tooltip>
              </motion.div>
            )}
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <SchoolIcon 
                sx={{ 
                  fontSize: { xs: 28, sm: 32, md: 40 }, 
                  color: theme.palette.primary.main,
                  mr: 1.5 
                }} 
              />
              <Typography 
                variant="h4" 
                component="h1" 
                sx={{ 
                  fontWeight: theme.typography.fontWeightBold,
                  color: theme.palette.text.primary
                }}
              >
                Learning Path
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ mt: 1, mb: 2 }}>
            <Typography 
              variant="h5"
              color="primary"
              sx={{ 
                fontWeight: theme.typography.fontWeightMedium,
                mb: 1,
                wordBreak: 'break-word',
                textAlign: { xs: 'center', sm: 'left' }
              }}
            >
              {topic}
            </Typography>
          </Box>
          
          <Divider sx={{ mt: 2, mb: 3 }} />
          
          <motion.div
            variants={buttonContainerVariants}
            initial="hidden"
            animate="visible"
          >
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
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems="center">
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
                
                <motion.div variants={buttonVariants}>
                  <Tooltip title={detailsHaveBeenSet ? "Details Saved" : "Save to History (Add Tags/Favorite)"}>
                    <span>
                      <Button
                        variant="contained"
                        startIcon={detailsHaveBeenSet ? <BookmarkIcon /> : <SaveIcon />}
                        onClick={onSaveToHistory}
                        disabled={detailsHaveBeenSet}
                      >
                        {detailsHaveBeenSet ? 'Saved' : 'Save Path'}
                      </Button>
                    </span>
                  </Tooltip>
                </motion.div>
                <Box sx={{ flexGrow: { xs: 0, sm: 1 } }} />
                <motion.div variants={buttonVariants}>
                  <Button
                    variant="text"
                    color="secondary"
                    startIcon={<SchoolIcon />}
                    onClick={onNewLearningPath}
                  >
                    New Path
                  </Button>
                </motion.div>
              </Stack>
            )}
          </motion.div>
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
  onNewLearningPath: PropTypes.func.isRequired,
  onOpenMobileNav: PropTypes.func,
  showMobileNavButton: PropTypes.bool,
};

export default LearningPathHeader; 
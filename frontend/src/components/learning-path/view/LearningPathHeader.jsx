import React, { useMemo } from 'react';
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
  IconButton,
  LinearProgress,
  FormControlLabel,
  Switch,
  Chip,
  Grid
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import DownloadForOfflineIcon from '@mui/icons-material/DownloadForOffline';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import SaveIcon from '@mui/icons-material/Save';
import SchoolIcon from '@mui/icons-material/School';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import MenuIcon from '@mui/icons-material/Menu';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import LinkIcon from '@mui/icons-material/Link';
import LockOpenIcon from '@mui/icons-material/LockOpen';
import LockIcon from '@mui/icons-material/Lock';
import BookmarkAddIcon from '@mui/icons-material/BookmarkAdd';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CircularProgress from '@mui/material/CircularProgress';
import { motion } from 'framer-motion';
import InfoTooltip from '../../shared/InfoTooltip';
import { helpTexts } from '../../../constants/helpTexts';
import ArticleIcon from '@mui/icons-material/Article';

/**
 * Header component for course display
 * 
 * @param {Object} props Component props 
 * @param {string} props.topic Course topic/title
 * @param {boolean} props.detailsHaveBeenSet Whether tags/favorites have been set
 * @param {boolean} props.isPdfReady Whether the PDF download is ready/enabled
 * @param {Function} props.onDownload Handler for JSON download
 * @param {Function} props.onDownloadPDF Handler for PDF download
 * @param {Function} props.onSaveToHistory Handler for opening save details dialog
 * @param {Function} props.onSaveOffline Handler for saving course to offline storage
 * @param {Function} props.onNewLearningPath Handler for creating a new course
 * @param {Function} [props.onOpenMobileNav] Optional handler to open mobile navigation
 * @param {boolean} [props.showMobileNavButton] Optional flag to show the mobile nav button
 * @param {Object} [props.progressMap] Optional map of submodule completion status
 * @param {Object} [props.actualPathData] Optional full course data for calculating totals
 * @param {Function} props.onStartTutorial Callback to start the interactive tutorial
 * @param {boolean} [props.isPublicView=false] Flag indicating if this is a public view
 * @param {boolean} [props.isPublic=false] Current public status of the course
 * @param {string|null} [props.shareId=null] Share ID if public
 * @param {Function} [props.onTogglePublic] Handler to toggle public status
 * @param {Function} [props.onCopyShareLink] Handler to copy share link
 * @param {string|null} [props.entryId=null] Persistent ID of the course (if saved)
 * @param {boolean} [props.isLoggedIn=false] Whether the current user is logged in
 * @param {Function} [props.onCopyToHistory] Handler to copy public course to user's history
 * @param {boolean} [props.isCopying=false] Loading state for the copy operation
 * @param {string} [props.viewMode='overview'] Current view mode ('overview' or 'focus')
 * @param {Function} [props.onBackToOverview] Handler to go back to overview mode
 * @param {Function} [props.onDownloadMarkdown] Handler for Markdown download
 * @returns {JSX.Element} Header component
 */
const LearningPathHeader = ({ 
  topic, 
  detailsHaveBeenSet,
  isPdfReady,
  onDownload,
  onDownloadPDF,
  onSaveToHistory,
  onSaveOffline,
  onNewLearningPath,
  onOpenMobileNav,
  showMobileNavButton,
  progressMap,
  actualPathData,
  onStartTutorial,
  isPublicView = false,
  isPublic = false,
  shareId = null,
  onTogglePublic,
  onCopyShareLink,
  entryId = null,
  isLoggedIn = false,
  onCopyToHistory,
  isCopying = false,
  viewMode = 'overview',
  onBackToOverview,
  onDownloadMarkdown
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isMedium = useMediaQuery(theme.breakpoints.down('md'));

  // Determine if sharing controls should be shown
  const showSharingControls = isLoggedIn && entryId && !isPublicView;

  // Calculate progress
  const { completedCount, totalSubmodules, progressPercent } = useMemo(() => {
    if (!progressMap || !actualPathData?.modules) {
      return { completedCount: 0, totalSubmodules: 0, progressPercent: 0 };
    }
    const completed = Object.values(progressMap).filter(Boolean).length;
    const total = actualPathData.modules.reduce((sum, mod) => sum + (mod.submodules?.length || 0), 0);
    const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
    return { completedCount: completed, totalSubmodules: total, progressPercent: percent };
  }, [progressMap, actualPathData]);

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
      data-tut="lp-header"
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
            {showMobileNavButton && !isPublicView && (
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
            <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
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
                Course
              </Typography>
            </Box>
            {!isPublicView && (
              <motion.div variants={buttonVariants}>
                <Tooltip title="Show Tutorial">
                  <IconButton 
                      data-tut="help-icon"
                      color="default"
                      onClick={onStartTutorial}
                      aria-label="show tutorial"
                      sx={{ ml: 1 }}
                  >
                      <HelpOutlineIcon />
                  </IconButton>
                </Tooltip>
              </motion.div>
            )}
          </Box>
          
          <Box sx={{ mt: 1, mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
              <Typography 
                variant="h5"
                color="primary"
                sx={{ 
                  fontWeight: theme.typography.fontWeightMedium,
                  wordBreak: 'break-word',
                  flexGrow: 1
                }}
              >
                {topic}
              </Typography>
              {viewMode === 'focus' && onBackToOverview && (
                <motion.div variants={buttonVariants}>
                  <Tooltip title="Back to Course Overview">
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<ArrowBackIcon />}
                      onClick={onBackToOverview}
                      sx={{
                        borderColor: theme.palette.primary.main,
                        color: theme.palette.primary.main,
                        '&:hover': {
                          backgroundColor: theme.palette.primary.main,
                          color: theme.palette.primary.contrastText
                        }
                      }}
                    >
                      Overview
                    </Button>
                  </Tooltip>
                </motion.div>
              )}
            </Box>
          </Box>

          {/* Progress Bar Section (Only if totalSubmodules > 0) */}
          {!isPublicView && totalSubmodules > 0 && (
              <Box sx={{ mt: 2, mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                      <Typography variant="body2" color="text.secondary">
                          Progress
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ fontWeight: theme.typography.fontWeightMedium }}>
                          {completedCount} / {totalSubmodules} ({progressPercent}%)
                      </Typography>
                  </Box>
                  <LinearProgress 
                      variant="determinate" 
                      value={progressPercent} 
                      sx={{ height: 8, borderRadius: 4 }}
                  />
              </Box>
          )}
          
          <Divider sx={{ mt: 2, mb: 3 }} />
          
          {/* --- Sharing Controls Section (conditionally rendered) --- */}
          {showSharingControls && (
            <Box sx={{ mb: 3 }}>
              <Grid container spacing={1} alignItems="center">
                <Grid item>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={isPublic}
                        onChange={onTogglePublic}
                        color="primary"
                        size="small"
                        disabled={!onTogglePublic}
                      />
                    }
                    label={isPublic ? 'Public' : 'Private'}
                    labelPlacement="start"
                    sx={{ ml: 0, mr: 1 }}
                  />
                </Grid>
                <Grid item>
                  {isPublic ? <LockOpenIcon fontSize="small" color="primary" /> : <LockIcon fontSize="small" color="disabled" />}
                </Grid>
                {isPublic && shareId && (
                  <Grid item xs>
                    <Chip 
                      label={`ID: ${shareId}`}
                      size="small" 
                      variant="outlined"
                      sx={{ mr: 1 }}
                    />
                    <Button 
                      size="small" 
                      variant="text"
                      startIcon={<LinkIcon />}
                      onClick={() => onCopyShareLink(shareId)}
                      disabled={!onCopyShareLink || !shareId}
                      sx={{ ml: 1 }}
                    >
                      Copy Link
                    </Button>
                  </Grid>
                )}
              </Grid>
              <Divider sx={{ mt: 2 }} /> 
            </Box>
          )}
          
          <motion.div
            variants={buttonContainerVariants}
            initial="hidden"
            animate="visible"
          >
            {isMedium ? (
              <Stack direction="column" spacing={1.5} sx={{ width: '100%' }}>
                <Grid container spacing={1}>
                  <Grid container item xs={12} spacing={1}>
                    <Grid item xs={6}>
                      <motion.div variants={buttonVariants}>
                        <Tooltip title="Download as JSON">
                          <Button
                            data-tut="download-json-button"
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
                    </Grid>
                    <Grid item xs={6}>
                      <motion.div variants={buttonVariants}>
                        <Tooltip title="Download as Markdown">
                          <Button
                            variant="outlined"
                            fullWidth
                            startIcon={<ArticleIcon />}
                            onClick={onDownloadMarkdown}
                            size={isMobile ? "small" : "medium"}
                          >
                            Markdown
                          </Button>
                        </Tooltip>
                      </motion.div>
                    </Grid>
                  </Grid>
                  <Grid container item xs={12} spacing={1}>
                    <Grid item xs={6}>
                      <motion.div variants={buttonVariants}>
                        <Tooltip title="Save for offline use">
                          <Button
                            variant="outlined"
                            fullWidth
                            startIcon={<DownloadForOfflineIcon />}
                            onClick={onSaveOffline}
                            size={isMobile ? "small" : "medium"}
                          >
                            Offline
                          </Button>
                        </Tooltip>
                      </motion.div>
                    </Grid>
                    <Grid item xs={6}>
                      <motion.div variants={buttonVariants}>
                        <Tooltip title={!isPdfReady ? "PDF download available after generation completes" : "Download as PDF"}>
                          <span>
                            <Button
                              data-tut="download-pdf-button"
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
                    </Grid>
                  </Grid>
                </Grid>
                
                {!isPublicView && (
                  <motion.div variants={buttonVariants}>
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                      <Button
                        data-tut="save-path-button"
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
                )}
                
                {isPublicView && isLoggedIn && (
                  <motion.div variants={buttonVariants} sx={{ width: '100%' }}>
                    <Tooltip title="Save a copy to your personal history">
                      <Button
                        data-tut="copy-public-path-button"
                        variant="outlined"
                        fullWidth
                        color="secondary"
                        startIcon={isCopying ? <CircularProgress size={20} color="inherit" /> : <BookmarkAddIcon />}
                        onClick={onCopyToHistory}
                        size={isMobile ? "small" : "medium"}
                        disabled={isCopying}
                      >
                        {isCopying ? 'Saving...' : 'Save to My History'}
                      </Button>
                    </Tooltip>
                  </motion.div>
                )}
                
                <motion.div variants={buttonVariants}>
                  <Button
                    data-tut="create-new-button"
                    variant="contained"
                    fullWidth
                    color="primary"
                    startIcon={<BookmarkIcon />}
                    onClick={onNewLearningPath}
                    size={isMobile ? "small" : "medium"}
                  >
                    Create New Course
                  </Button>
                </motion.div>
              </Stack>
            ) : (
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems="center">
                <motion.div variants={buttonVariants}>
                  <Tooltip title="Download as JSON">
                    <Button
                      data-tut="download-json-button"
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={onDownload}
                    >
                      JSON
                    </Button>
                  </Tooltip>
                </motion.div>

                <motion.div variants={buttonVariants}>
                  <Tooltip title="Download as Markdown">
                    <Button
                      variant="outlined"
                      startIcon={<ArticleIcon />}
                      onClick={onDownloadMarkdown}
                    >
                      Markdown
                    </Button>
                  </Tooltip>
                </motion.div>

                <motion.div variants={buttonVariants}>
                  <Tooltip title="Save for offline use">
                    <Button
                      variant="outlined"
                      startIcon={<DownloadForOfflineIcon />}
                      onClick={onSaveOffline}
                    >
                      Offline
                    </Button>
                  </Tooltip>
                </motion.div>
                
                <motion.div variants={buttonVariants}>
                  <Tooltip title={!isPdfReady ? "PDF download available after generation completes" : "Download as PDF"}>
                    <span>
                      <Button
                        data-tut="download-pdf-button"
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
                
                {!isPublicView && (
                  <motion.div variants={buttonVariants}>
                    <Tooltip title={detailsHaveBeenSet ? "Details Saved" : "Save Course (Add Tags/Favorite)"}>
                      <span>
                        <Button
                          data-tut="save-path-button"
                          variant="contained"
                          startIcon={detailsHaveBeenSet ? <BookmarkIcon /> : <SaveIcon />}
                          onClick={onSaveToHistory}
                          disabled={detailsHaveBeenSet}
                        >
                          {detailsHaveBeenSet ? 'Saved' : 'Save Course'}
                        </Button>
                      </span>
                    </Tooltip>
                  </motion.div>
                )}

                {isPublicView && isLoggedIn && (
                  <motion.div variants={buttonVariants}>
                    <Tooltip title="Save a copy to your personal history">
                      <Button
                        data-tut="copy-public-path-button"
                        variant="outlined"
                        color="secondary"
                        startIcon={isCopying ? <CircularProgress size={20} color="inherit" /> : <BookmarkAddIcon />}
                        onClick={onCopyToHistory}
                        size={isMobile ? "small" : "medium"}
                        disabled={isCopying}
                      >
                        {isCopying ? 'Saving...' : 'Save to My History'}
                      </Button>
                    </Tooltip>
                  </motion.div>
                )}

                <Box sx={{ flexGrow: { xs: 0, sm: 1 } }} />
                <motion.div variants={buttonVariants}>
                  <Button
                    data-tut="create-new-button"
                    variant="text"
                    color="secondary"
                    startIcon={<SchoolIcon />}
                    onClick={onNewLearningPath}
                  >
                    New Course
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
  onSaveOffline: PropTypes.func.isRequired,
  onNewLearningPath: PropTypes.func.isRequired,
  onOpenMobileNav: PropTypes.func,
  showMobileNavButton: PropTypes.bool,
  progressMap: PropTypes.object,
  actualPathData: PropTypes.object,
  onStartTutorial: PropTypes.func.isRequired,
  isPublicView: PropTypes.bool,
  isPublic: PropTypes.bool,
  shareId: PropTypes.string,
  onTogglePublic: PropTypes.func,
  onCopyShareLink: PropTypes.func,
  entryId: PropTypes.string,
  isLoggedIn: PropTypes.bool,
  onCopyToHistory: PropTypes.func,
  isCopying: PropTypes.bool,
  viewMode: PropTypes.string,
  onBackToOverview: PropTypes.func,
  onDownloadMarkdown: PropTypes.func,
};

export default LearningPathHeader;

import React from 'react';
import PropTypes from 'prop-types';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Card, 
  CardContent, 
  CardActions,
  Button, 
  Chip, 
  Stack, 
  LinearProgress,
  IconButton,
  Tooltip,
  Divider,
  useTheme,
  useMediaQuery,
  Collapse,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Checkbox,
  alpha
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PlayCircleFilledIcon from '@mui/icons-material/PlayCircleFilled';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import CollectionsBookmarkIcon from '@mui/icons-material/CollectionsBookmark';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import SchoolIcon from '@mui/icons-material/School';
import AutoStoriesIcon from '@mui/icons-material/AutoStories';

// Shared components
import ResourcesSection from '../../shared/ResourcesSection';
import CourseVisualization from '../../visualization/CourseVisualization';

const CourseOverview = ({ 
  actualPathData, 
  topic, 
  topicResources,
  onSelectSubmodule, 
  onStartCourse,
  progressMap,
  onToggleProgress,
  isPublicView = false,
  lastVisitedModuleIdx = null,
  lastVisitedSubmoduleIdx = null,
  pathId = null,
  language = 'en'
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [expandedModules, setExpandedModules] = React.useState({});
  const [courseVisualizationExpanded, setCourseVisualizationExpanded] = React.useState(false);

  const modules = actualPathData?.modules || [];

  // Calculate overall progress
  const totalSubmodules = modules.reduce((total, module) => total + (module.submodules?.length || 0), 0);
  const completedSubmodules = Object.values(progressMap || {}).filter(Boolean).length;
  const overallProgress = totalSubmodules > 0 ? (completedSubmodules / totalSubmodules) * 100 : 0;

  // Determine if the user has started the course
  const hasStartedCourse = 
    (lastVisitedModuleIdx !== null && lastVisitedSubmoduleIdx !== null) ||
    Object.values(progressMap || {}).some(Boolean);

  // Dynamic button text and icon
  const buttonText = hasStartedCourse ? "Resume Course" : "Start Course";
  const heroButtonText = hasStartedCourse ? "Resume Learning Journey" : "Start Learning Journey";
  const buttonIcon = hasStartedCourse ? <PlayCircleFilledIcon /> : <PlayArrowIcon />;
  const ctaText = hasStartedCourse ? "Ready to jump back in?" : "Ready to begin your learning journey?";

  // Calculate progress for each module
  const getModuleProgress = (moduleIndex, module) => {
    if (!module.submodules || module.submodules.length === 0) return 0;
    
    const moduleSubmodules = module.submodules.length;
    const completedInModule = module.submodules.filter((_, subIndex) => 
      progressMap[`${moduleIndex}_${subIndex}`]
    ).length;
    
    return moduleSubmodules > 0 ? (completedInModule / moduleSubmodules) * 100 : 0;
  };

  const toggleModuleExpansion = (moduleIndex) => {
    setExpandedModules(prev => ({
      ...prev,
      [moduleIndex]: !prev[moduleIndex]
    }));
  };

  const handleSubmoduleClick = (moduleIndex, submoduleIndex) => {
    onSelectSubmodule(moduleIndex, submoduleIndex);
  };

  const handleToggleSubmoduleProgress = (moduleIndex, submoduleIndex, event) => {
    event.stopPropagation();
    if (!isPublicView && onToggleProgress) {
      onToggleProgress(moduleIndex, submoduleIndex);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      }
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
    <Box
      component={motion.div}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      sx={{ 
        width: '100%',
        maxWidth: '1200px',
        mx: 'auto',
        p: { xs: 2, md: 3 }
      }}
    >
      {/* Hero Section */}
      <motion.div variants={cardVariants}>
        <Paper
          elevation={0}
          sx={{
            p: { xs: 3, md: 4 },
            mb: 4,
            background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.05)} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: 2,
            textAlign: 'center'
          }}
        >
          <SchoolIcon 
            sx={{ 
              fontSize: { xs: 48, md: 64 }, 
              color: theme.palette.primary.main, 
              mb: 2 
            }} 
          />
          <Typography 
            variant="h3" 
            component="h1" 
            gutterBottom
            sx={{ 
              fontWeight: 700,
              color: theme.palette.text.primary,
              fontSize: { xs: '1.75rem', md: '2.5rem' }
            }}
          >
            {topic}
          </Typography>
          
          {/* Overall Progress */}
          <Box sx={{ mt: 3, mb: 3 }}>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              Course Progress: {Math.round(overallProgress)}% Complete
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={overallProgress}
              sx={{ 
                height: 8, 
                borderRadius: 4,
                backgroundColor: alpha(theme.palette.primary.main, 0.1),
                '& .MuiLinearProgress-bar': {
                  borderRadius: 4,
                  background: `linear-gradient(90deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`
                }
              }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              {completedSubmodules} of {totalSubmodules} lessons completed
            </Typography>
          </Box>

          {/* Start Course Button */}
          <Button
            variant="contained"
            size="large"
            startIcon={buttonIcon}
            onClick={onStartCourse}
            sx={{
              px: 4,
              py: 1.5,
              fontSize: '1.1rem',
              fontWeight: 600,
              borderRadius: 2,
              background: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.secondary.main} 90%)`,
              '&:hover': {
                background: `linear-gradient(45deg, ${theme.palette.primary.dark} 30%, ${theme.palette.secondary.dark} 90%)`,
                transform: 'translateY(-2px)',
                boxShadow: theme.shadows[8]
              },
              transition: 'all 0.3s ease'
            }}
          >
            {heroButtonText}
          </Button>
        </Paper>
      </motion.div>

      {/* Topic Resources */}
      {topicResources && topicResources.length > 0 && (
        <motion.div variants={cardVariants}>
          <Paper
            elevation={0}
            sx={{
              p: 3,
              mb: 4,
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2
            }}
          >
            <ResourcesSection
              resources={topicResources}
              title="Course Resources"
              type="topic"
              collapsible={true}
              expanded={false}
              compact={false}
            />
          </Paper>
        </motion.div>
      )}

      {/* Course Visualization */}
      {pathId && (
        <motion.div variants={cardVariants}>
          <Paper
            elevation={0}
            sx={{
              mb: 4,
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2
            }}
          >
            <Box 
              sx={{ 
                p: 2, 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                cursor: 'pointer',
                '&:hover': {
                  backgroundColor: alpha(theme.palette.action.hover, 0.04)
                }
              }}
              onClick={() => setCourseVisualizationExpanded(!courseVisualizationExpanded)}
            >
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SchoolIcon 
                  sx={{ 
                    mr: 1, 
                    color: theme.palette.primary.main,
                    fontSize: 20
                  }} 
                />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Course Visualization
                </Typography>
              </Box>
              <IconButton size="small">
                {courseVisualizationExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>
            
            <Collapse in={courseVisualizationExpanded} timeout="auto" unmountOnExit>
              <Box sx={{ p: 2, pt: 0 }}>
                <CourseVisualization
                  pathId={pathId}
                  pathData={actualPathData}
                  topic={topic}
                  language={language}
                  isPublicView={isPublicView}
                />
              </Box>
            </Collapse>
          </Paper>
        </motion.div>
      )}

      {/* Modules Grid */}
      <Grid container spacing={3}>
        {modules.map((module, moduleIndex) => {
          const moduleProgress = getModuleProgress(moduleIndex, module);
          const isExpanded = expandedModules[moduleIndex];
          const hasSubmodules = module.submodules && module.submodules.length > 0;
          const hasResources = module.resources && module.resources.length > 0;

          return (
            <Grid item xs={12} lg={6} key={moduleIndex}>
              <motion.div variants={cardVariants}>
                <Card
                  elevation={0}
                  sx={{
                    height: '100%',
                    border: `1px solid ${theme.palette.divider}`,
                    borderRadius: 2,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      borderColor: theme.palette.primary.main,
                      boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.1)}`
                    }
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    {/* Module Header */}
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                      <AutoStoriesIcon 
                        sx={{ 
                          color: theme.palette.primary.main, 
                          mr: 2, 
                          mt: 0.5,
                          fontSize: 28
                        }} 
                      />
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography 
                          variant="h5" 
                          component="h2" 
                          gutterBottom
                          sx={{ 
                            fontWeight: 600,
                            color: theme.palette.text.primary,
                            lineHeight: 1.3
                          }}
                        >
                          Module {moduleIndex + 1}: {module.title}
                        </Typography>
                        <Typography 
                          variant="body2" 
                          color="text.secondary"
                          sx={{ mb: 2 }}
                        >
                          {module.description}
                        </Typography>
                      </Box>
                    </Box>

                    {/* Prerequisites */}
                    {module.prerequisites && module.prerequisites.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="caption" sx={{ fontWeight: 500, mb: 1, display: 'block' }}>
                          Prerequisites:
                        </Typography>
                        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                          {module.prerequisites.map((prereq, idx) => (
                            <Chip 
                              key={idx} 
                              label={prereq} 
                              size="small" 
                              variant="outlined"
                              sx={{ fontSize: '0.75rem' }}
                            />
                          ))}
                        </Stack>
                      </Box>
                    )}

                    {/* Progress Bar */}
                    {hasSubmodules && (
                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="caption" sx={{ fontWeight: 500 }}>
                            Progress
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {Math.round(moduleProgress)}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={moduleProgress}
                          sx={{ 
                            height: 6, 
                            borderRadius: 3,
                            backgroundColor: alpha(theme.palette.primary.main, 0.1),
                            '& .MuiLinearProgress-bar': {
                              borderRadius: 3,
                              backgroundColor: theme.palette.primary.main
                            }
                          }}
                        />
                      </Box>
                    )}

                    {/* Module Stats */}
                    <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                      {hasSubmodules && (
                        <Chip
                          icon={<MenuBookIcon />}
                          label={`${module.submodules.length} Lessons`}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.75rem' }}
                        />
                      )}
                      {hasResources && (
                        <Chip
                          icon={<CollectionsBookmarkIcon />}
                          label={`${module.resources.length} Resources`}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.75rem' }}
                        />
                      )}
                      {module.submodules?.some(sub => sub.quiz_questions?.length > 0) && (
                        <Chip
                          icon={<FitnessCenterIcon />}
                          label="Quiz Available"
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.75rem' }}
                        />
                      )}
                    </Stack>
                  </CardContent>

                  {/* Expandable Submodules */}
                  {hasSubmodules && (
                    <>
                      <Divider />
                      <CardActions sx={{ p: 0 }}>
                        <Button
                          fullWidth
                          onClick={() => toggleModuleExpansion(moduleIndex)}
                          endIcon={isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          sx={{ 
                            py: 1.5,
                            justifyContent: 'space-between',
                            textTransform: 'none',
                            fontWeight: 500
                          }}
                        >
                          {isExpanded ? 'Hide Lessons' : `View ${module.submodules.length} Lessons`}
                        </Button>
                      </CardActions>
                      
                      <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                        <Divider />
                        <List sx={{ py: 0 }}>
                          {module.submodules.map((submodule, submoduleIndex) => {
                            const progressKey = `${moduleIndex}_${submoduleIndex}`;
                            const isCompleted = progressMap[progressKey] || false;
                            
                            return (
                              <ListItem key={submoduleIndex} disablePadding>
                                <ListItemButton
                                  onClick={() => handleSubmoduleClick(moduleIndex, submoduleIndex)}
                                  sx={{
                                    py: 1.5,
                                    px: 3,
                                    '&:hover': {
                                      backgroundColor: alpha(theme.palette.primary.main, 0.04)
                                    }
                                  }}
                                >
                                  <ListItemIcon sx={{ minWidth: 40 }}>
                                    <Tooltip title={isPublicView ? "Progress tracking disabled" : (isCompleted ? "Mark as incomplete" : "Mark as complete")}>
                                      <IconButton
                                        size="small"
                                        onClick={(e) => handleToggleSubmoduleProgress(moduleIndex, submoduleIndex, e)}
                                        disabled={isPublicView}
                                        sx={{ p: 0.5 }}
                                      >
                                        {isCompleted ? (
                                          <CheckCircleIcon sx={{ color: theme.palette.success.main }} />
                                        ) : (
                                          <RadioButtonUncheckedIcon sx={{ color: theme.palette.action.active }} />
                                        )}
                                      </IconButton>
                                    </Tooltip>
                                  </ListItemIcon>
                                  <ListItemText
                                    primary={`${moduleIndex + 1}.${submoduleIndex + 1} ${submodule.title}`}
                                    secondary={submodule.description}
                                    primaryTypographyProps={{
                                      variant: 'body2',
                                      fontWeight: 500,
                                      sx: { 
                                        textDecoration: isCompleted ? 'line-through' : 'none',
                                        color: isCompleted ? theme.palette.text.disabled : theme.palette.text.primary
                                      }
                                    }}
                                    secondaryTypographyProps={{
                                      variant: 'caption',
                                      sx: { 
                                        color: isCompleted ? theme.palette.text.disabled : theme.palette.text.secondary
                                      }
                                    }}
                                  />
                                  <Stack direction="row" spacing={0.5} sx={{ ml: 1 }}>
                                    {submodule.quiz_questions?.length > 0 && (
                                      <Chip
                                        icon={<FitnessCenterIcon />}
                                        label="Quiz"
                                        size="small"
                                        variant="outlined"
                                        sx={{ fontSize: '0.7rem', height: 20 }}
                                      />
                                    )}
                                    {submodule.resources?.length > 0 && (
                                      <Chip
                                        icon={<CollectionsBookmarkIcon />}
                                        label={submodule.resources.length}
                                        size="small"
                                        variant="outlined"
                                        sx={{ fontSize: '0.7rem', height: 20 }}
                                      />
                                    )}
                                  </Stack>
                                </ListItemButton>
                              </ListItem>
                            );
                          })}
                        </List>
                      </Collapse>
                    </>
                  )}

                  {/* Module Resources */}
                  {hasResources && (
                    <>
                      <Divider />
                      <Box sx={{ p: 3, pt: 2 }}>
                        <ResourcesSection
                          resources={module.resources}
                          title="Module Resources"
                          type="module"
                          collapsible={true}
                          expanded={false}
                          compact={true}
                        />
                      </Box>
                    </>
                  )}
                </Card>
              </motion.div>
            </Grid>
          );
        })}
      </Grid>

      {/* Bottom CTA */}
      <motion.div variants={cardVariants}>
        <Box sx={{ textAlign: 'center', mt: 6, mb: 4 }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 500 }}>
            {ctaText}
          </Typography>
          <Button
            variant="contained"
            size="large"
            startIcon={buttonIcon}
            onClick={onStartCourse}
            sx={{
              px: 4,
              py: 1.5,
              fontSize: '1rem',
              fontWeight: 600,
              borderRadius: 2,
              mt: 2
            }}
          >
            {buttonText}
          </Button>
        </Box>
      </motion.div>
    </Box>
  );
};

CourseOverview.propTypes = {
  actualPathData: PropTypes.object.isRequired,
  topic: PropTypes.string.isRequired,
  topicResources: PropTypes.array,
  onSelectSubmodule: PropTypes.func.isRequired,
  onStartCourse: PropTypes.func.isRequired,
  progressMap: PropTypes.object,
  onToggleProgress: PropTypes.func,
  isPublicView: PropTypes.bool,
  lastVisitedModuleIdx: PropTypes.number,
  lastVisitedSubmoduleIdx: PropTypes.number,
  pathId: PropTypes.string,
  language: PropTypes.string
};

export default CourseOverview;

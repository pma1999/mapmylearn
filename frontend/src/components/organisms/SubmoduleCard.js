import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Divider,
  useTheme,
  useMediaQuery,
  Fade,
  Badge,
  Tabs,
  Tab
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import CollectionsBookmarkIcon from '@mui/icons-material/CollectionsBookmark';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import MarkdownRenderer from '../MarkdownRenderer';
import { motion } from 'framer-motion';
import ResourcesSection from '../shared/ResourcesSection';

// Import quiz components
import { QuizContainer } from '../quiz';

// Import placeholders for future content types
import PlaceholderContent from '../shared/PlaceholderContent';

// Import the new Chat component
import SubmoduleChat from '../chat/SubmoduleChat';

// Import useAuth hook instead of AuthContext
import { useAuth } from '../../services/authContext';

// TabPanel component for the tabbed interface
const TabPanel = (props) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ 
          p: index === 3 ? 0 : { xs: 1, sm: 2 } 
        }}>
          {children}
        </Box>
      )}
    </div>
  );
};

const SubmoduleCard = ({ submodule, index, moduleIndex, pathId }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const fullScreen = useMediaQuery(theme.breakpoints.down('md'));
  
  // Use the useAuth hook to get user information
  const { user } = useAuth();
  
  // Check if this submodule has quiz questions
  const hasQuizQuestions = submodule.quiz_questions && submodule.quiz_questions.length > 0;
  
  const handleOpenModal = () => {
    setModalOpen(true);
  };
  
  const handleCloseModal = () => {
    setModalOpen(false);
  };
  
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  // Animation variants for the card
  const cardVariants = {
    hidden: { opacity: 0, x: -10 },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: { 
        duration: 0.3,
        delay: index * 0.05 
      }
    }
  };

  // Ensure pathId is passed; provide a fallback or handle error if missing
  if (!pathId) {
    console.error("Error: pathId prop is missing in SubmoduleCard");
    // Optionally return null or an error message component
    return null; 
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={cardVariants}
    >
      <Card 
        variant="outlined" 
        sx={{ 
          borderRadius: 2,
          transition: 'all 0.3s ease',
          borderWidth: 1,
          borderColor: 'grey.300',
          '&:hover': {
            borderColor: theme.palette.primary.light,
            boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.08)'
          }
        }}
      >
        <CardContent sx={{ p: { xs: 2, sm: 2.5 } }}>
          <Box 
            sx={{ 
              display: 'flex', 
              alignItems: 'flex-start',
              justifyContent: 'space-between'
            }}
          >
            <Box sx={{ flex: 1 }}>
              <Typography 
                variant="h6" 
                sx={{ 
                  fontWeight: 500,
                  fontSize: { xs: '1rem', sm: '1.1rem' },
                  mb: 1,
                  lineHeight: 1.4,
                  color: theme.palette.text.primary,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
                }}
              >
                {submodule.title}
              </Typography>
              
              <Typography 
                variant="body2" 
                color="text.secondary"
                sx={{ 
                  mb: 2,
                  fontSize: { xs: '0.85rem', sm: '0.9rem' },
                  lineHeight: 1.5
                }}
              >
                {submodule.description}
              </Typography>
            </Box>
          </Box>
          
          <Box 
            sx={{ 
              display: 'flex', 
              justifyContent: 'flex-end',
              alignItems: 'center',
              mt: 1
            }}
          >
            <Button
              size="small"
              color="primary"
              variant="outlined"
              startIcon={<MenuBookIcon />}
              onClick={handleOpenModal}
            >
              View Content
            </Button>
          </Box>
        </CardContent>
      </Card>
      
      {/* Enhanced Full Content Modal with Tabs */}
      <Dialog
        open={modalOpen}
        onClose={handleCloseModal}
        fullScreen={fullScreen}
        maxWidth="md"
        fullWidth
        TransitionComponent={Fade}
        transitionDuration={300}
        scroll="paper"
        PaperProps={{
          sx: {
            borderRadius: { xs: 0, sm: 2 },
            maxHeight: '90vh'
          }
        }}
      >
        <DialogTitle
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            px: { xs: 2, sm: 3 },
            py: { xs: 1.5, sm: 2 },
            bgcolor: 'primary.main',
            color: 'white',
          }}
        >
          <Typography variant="h6" component="div" sx={{ flex: 1, pr: 2 }}>
            Module {moduleIndex + 1}.{index + 1}: {submodule.title}
          </Typography>
          <IconButton
            edge="end"
            color="inherit"
            onClick={handleCloseModal}
            aria-label="close"
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        
        <DialogContent 
          dividers 
          sx={{ 
            p: 0, 
            display: 'flex', 
            flexDirection: 'column' 
          }}
        >
          {/* Submodule description */}
          <Box sx={{ px: { xs: 2, sm: 3 }, pt: { xs: 2, sm: 3 } }}>
            <Typography 
              variant="subtitle1" 
              color="text.secondary"
              paragraph
              sx={{ 
                mb: 3, 
                fontStyle: 'italic',
                borderLeft: '4px solid',
                borderColor: 'primary.light',
                pl: 2,
                py: 1,
                bgcolor: 'grey.50',
                borderRadius: '0 4px 4px 0'
              }}
            >
              {submodule.description}
            </Typography>
          </Box>
          
          {/* Tabbed interface */}
          <Box sx={{ width: '100%', flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
            {/* Tabs navigation */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs 
                value={activeTab} 
                onChange={handleTabChange} 
                aria-label="submodule content tabs"
                variant={isMobile ? "scrollable" : "standard"}
                scrollButtons={isMobile ? "auto" : false}
                allowScrollButtonsMobile
                sx={{
                  px: { xs: 2, sm: 3 },
                  '& .MuiTab-root': {
                    minWidth: { xs: 'auto', sm: 100 },
                    py: { xs: 1, sm: 1.5 },
                    px: { xs: 2, sm: 3 },
                    fontSize: { xs: '0.8rem', sm: '0.9rem' },
                    fontWeight: 500,
                  }
                }}
              >
                <Tab 
                  label="Content" 
                  icon={<MenuBookIcon />} 
                  iconPosition="start" 
                  id="tab-0"
                  aria-controls="tabpanel-0"
                />
                <Tab 
                  label={hasQuizQuestions ? "Quiz" : "Exercises"}
                  icon={<FitnessCenterIcon />} 
                  iconPosition="start" 
                  id="tab-1"
                  aria-controls="tabpanel-1"
                />
                <Tab 
                  label="Resources" 
                  icon={<CollectionsBookmarkIcon />} 
                  iconPosition="start" 
                  id="tab-2"
                  aria-controls="tabpanel-2"
                />
                <Tab 
                  label="Chatbot" 
                  icon={<QuestionAnswerIcon />} 
                  iconPosition="start" 
                  id="tab-3"
                  aria-controls="tabpanel-3"
                />
              </Tabs>
            </Box>
            
            {/* Content tab panel */}
            <TabPanel value={activeTab} index={0}>
              <MarkdownRenderer>
                {submodule.content}
              </MarkdownRenderer>
            </TabPanel>
            
            {/* Exercises tab panel - now shows quiz if available */}
            <TabPanel value={activeTab} index={1}>
              {hasQuizQuestions ? (
                <QuizContainer quizQuestions={submodule.quiz_questions} />
              ) : (
                <>
                  <PlaceholderContent 
                    title="Interactive Exercises Coming Soon"
                    description="This section will contain practice exercises to help you test your understanding and apply what you've learned."
                    type="exercises"
                    icon={<FitnessCenterIcon sx={{ fontSize: 40 }} />}
                  />
                  
                  <Box sx={{ px: 2, mt: 3 }}>
                    <Typography 
                      variant="body2" 
                      color="textSecondary" 
                      sx={{ 
                        fontStyle: 'italic',
                        textAlign: 'center'
                      }}
                    >
                      Future exercises will include multiple choice quizzes, code challenges, 
                      and interactive problems to reinforce your learning.
                    </Typography>
                  </Box>
                </>
              )}
            </TabPanel>
            
            {/* Resources tab panel */}
            <TabPanel value={activeTab} index={2}>
              <ResourcesSection
                resources={submodule.resources}
                title="Additional Resources"
                type="submodule"
                compact={isMobile}
              />
            </TabPanel>

            {/* Chatbot tab panel */}
            <TabPanel value={activeTab} index={3}>
              <SubmoduleChat 
                pathId={pathId} 
                moduleIndex={moduleIndex} 
                submoduleIndex={index} 
                userId={user?.id}
              />
            </TabPanel>
          </Box>
        </DialogContent>
        
        <DialogActions sx={{ px: { xs: 2, sm: 3 }, py: 2 }}>
          <Button onClick={handleCloseModal} color="primary">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </motion.div>
  );
};

export default SubmoduleCard; 
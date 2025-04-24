import React, { useEffect } from 'react';
import { Link as RouterLink } from 'react-router';
import {
  Typography,
  Button,
  Box,
  Container,
  Paper,
  Grid,
  Card,
  CardContent,
  useTheme,
  useMediaQuery,
  Stack,
  Avatar,
  Chip
} from '@mui/material';
import { motion } from 'framer-motion';
import AutoStoriesIcon from '@mui/icons-material/AutoStories';
import SchoolIcon from '@mui/icons-material/School';
import PsychologyIcon from '@mui/icons-material/Psychology';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ArrowRightAltIcon from '@mui/icons-material/ArrowRightAlt';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import TimelineIcon from '@mui/icons-material/Timeline';
import AssessmentIcon from '@mui/icons-material/Assessment';

// Animation variants for Framer Motion
const fadeInUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: "easeOut" } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2
    }
  }
};

const fadeIn = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.6 } }
};

const heroCardVariant = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: { 
    opacity: 1, 
    scale: 1,
    transition: { 
      duration: 0.5,
      delay: 0.3
    } 
  }
};

const FloatingElement = ({ children, delay = 0, offsetY = 15 }) => (
  <motion.div
    animate={{ 
      y: [0, offsetY, 0], 
    }}
    transition={{ 
      repeat: Infinity, 
      duration: 5, 
      ease: "easeInOut",
      delay
    }}
    style={{ display: 'inline-flex' }}
  >
    {children}
  </motion.div>
);

function HomePage() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isMedium = useMediaQuery(theme.breakpoints.down('md'));

  // Intersection Observer setup
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate');
          }
        });
      },
      { threshold: 0.2 }
    );

    document.querySelectorAll('.animate-on-scroll').forEach((element) => {
      observer.observe(element);
    });

    return () => {
      document.querySelectorAll('.animate-on-scroll').forEach((element) => {
        observer.unobserve(element);
      });
    };
  }, []);

  return (
    <Box sx={{ overflow: 'hidden' }}>
      {/* Hero Section with Animated Background */}
      <Box
        component={motion.div}
        initial="hidden"
        animate="visible"
        sx={{
          background: 'linear-gradient(135deg, #1976d2 0%, #6d4ce3 100%)',
          color: '#fff',
          position: 'relative',
          pt: { xs: 6, md: 10 },
          pb: { xs: 10, md: 15 },
          overflow: 'hidden',
          borderRadius: { xs: 0, md: '0 0 30px 30px' },
          boxShadow: 3
        }}
      >
        {/* Floating background elements */}
        <Box sx={{ position: 'absolute', width: '100%', height: '100%', top: 0, left: 0, overflow: 'hidden', pointerEvents: 'none' }}>
          <FloatingElement delay={0.5} offsetY={25}>
            <Box component={LightbulbIcon} sx={{ position: 'absolute', top: '15%', left: '10%', fontSize: 40, opacity: 0.2 }} />
          </FloatingElement>
          <FloatingElement delay={1.2} offsetY={-20}>
            <Box component={SchoolIcon} sx={{ position: 'absolute', top: '30%', right: '15%', fontSize: 50, opacity: 0.2 }} />
          </FloatingElement>
          <FloatingElement delay={0.8} offsetY={30}>
            <Box component={TimelineIcon} sx={{ position: 'absolute', bottom: '25%', left: '20%', fontSize: 45, opacity: 0.2 }} />
          </FloatingElement>
          <FloatingElement delay={1.5} offsetY={-15}>
            <Box component={AssessmentIcon} sx={{ position: 'absolute', bottom: '15%', right: '25%', fontSize: 35, opacity: 0.2 }} />
          </FloatingElement>
        </Box>

        <Container maxWidth="lg">
          <Grid container spacing={4} alignItems="center" justifyContent="space-between">
            <Grid item xs={12} md={6} component={motion.div} variants={fadeInUp}>
              <Typography
                component={motion.h1}
                variant="h2"
                sx={{
                  fontWeight: 800,
                  mb: 2,
                  background: 'linear-gradient(90deg, #fff 0%, #e0e7ff 100%)',
                  backgroundClip: 'text',
                  textFillColor: 'transparent',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontSize: { xs: '2.5rem', md: '3.5rem' }
                }}
              >
                Personalized Learning Paths
              </Typography>
              
              <Typography 
                variant="h5" 
                component={motion.p}
                variants={fadeIn}
                sx={{ 
                  mb: 4, 
                  fontWeight: 400,
                  maxWidth: '90%',
                  opacity: 0.9,
                  lineHeight: 1.5
                }}
              >
                Supercharge your knowledge journey with AI-generated learning paths 
                tailored perfectly to your goals and interests.
              </Typography>
              
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.98 }}
              >
                <Button
                  variant="contained"
                  color="secondary"
                  size="large"
                  component={RouterLink}
                  to="/generator"
                  endIcon={<ArrowForwardIcon />}
                  sx={{
                    px: 4,
                    py: 1.8,
                    fontSize: '1.1rem',
                    fontWeight: 'bold',
                    borderRadius: 8,
                    boxShadow: '0 10px 20px rgba(0,0,0,0.12)',
                    textTransform: 'none',
                    background: 'linear-gradient(90deg, #ff9a8b 0%, #ff6a88 55%, #ff99ac 100%)',
                    '&:hover': {
                      background: 'linear-gradient(90deg, #ff6a88 0%, #ff9a8b 100%)',
                      boxShadow: '0 6px 15px rgba(255,106,136,0.4)',
                    }
                  }}
                >
                  Create Your Path
                </Button>
              </motion.div>
            </Grid>
            
            <Grid item xs={12} md={6} component={motion.div} variants={heroCardVariant} sx={{ display: { xs: 'none', md: 'block' } }}>
              <motion.div
                whileHover={{ y: -10, boxShadow: '0 20px 25px rgba(0,0,0,0.2)' }}
                transition={{ duration: 0.5 }}
              >
                <Paper 
                  elevation={8} 
                  sx={{ 
                    borderRadius: 4, 
                    overflow: 'hidden',
                    position: 'relative',
                    height: 400,
                    background: 'rgba(255,255,255,0.1)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255,255,255,0.2)'
                  }}
                >
                  <Box 
                    component="img" 
                    src="/learning-path-illustration.svg" 
                    alt="Learning Path" 
                    sx={{ 
                      width: '100%', 
                      height: '100%', 
                      objectFit: 'contain',
                      p: 4
                    }}
                    onError={(e) => {
                      // Fallback if image doesn't exist
                      e.target.style.display = 'none';
                      e.target.parentElement.style.display = 'flex';
                      e.target.parentElement.style.alignItems = 'center';
                      e.target.parentElement.style.justifyContent = 'center';
                      
                      const icon = document.createElement('div');
                      icon.innerHTML = `<svg width="200" height="200" viewBox="0 0 24 24" fill="white">
                        <path d="M12 3L1 9L5 11.18V17.18L12 21L19 17.18V11.18L21 10.09V17H23V9L12 3ZM18.82 9L12 12.72L5.18 9L12 5.28L18.82 9ZM17 16L12 18.72L7 16V12.27L12 15L17 12.27V16Z"/>
                      </svg>`;
                      e.target.parentElement.appendChild(icon);
                    }}
                  />
                </Paper>
              </motion.div>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Value Proposition Section */}
      <Container maxWidth="lg" sx={{ py: { xs: 6, md: 10 } }} className="animate-on-scroll">
        <Box sx={{ textAlign: 'center', mb: 6 }}>
          <Typography
            component="h2"
            variant="h3"
            color="primary.main"
            sx={{ 
              fontWeight: 700, 
              mb: 2,
              fontSize: { xs: '1.8rem', md: '2.5rem' }
            }}
          >
            Why Choose MapMyLearn?
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 700, mx: 'auto' }}>
            Our AI-powered platform creates personalized learning experiences that adapt to your specific needs and goals.
          </Typography>
        </Box>

        <Grid container spacing={4} component={motion.div} variants={staggerContainer} initial="hidden" animate="visible">
          {[
            { 
              icon: <SmartToyIcon sx={{ fontSize: 40 }} />, 
              title: 'AI-Powered Paths', 
              description: 'Advanced algorithms analyze your topic to create perfectly structured learning journeys.' 
            },
            { 
              icon: <PsychologyIcon sx={{ fontSize: 40 }} />, 
              title: 'Personalized Content', 
              description: 'Learning materials tailored to your specific interests, goals, and learning style.' 
            },
            { 
              icon: <AutoStoriesIcon sx={{ fontSize: 40 }} />, 
              title: 'Efficient Learning', 
              description: 'Save time with optimized learning paths that focus on what matters most.' 
            }
          ].map((item, index) => (
            <Grid item xs={12} md={4} key={index}>
              <motion.div variants={fadeInUp} whileHover={{ y: -10 }} transition={{ duration: 0.3 }}>
                <Card 
                  sx={{ 
                    height: '100%', 
                    boxShadow: 2, 
                    borderRadius: 4,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      boxShadow: 8,
                      transform: 'translateY(-8px)'
                    }
                  }}
                >
                  <CardContent sx={{ p: 4, textAlign: 'center' }}>
                    <Avatar 
                      sx={{ 
                        width: 80, 
                        height: 80, 
                        mb: 3, 
                        mx: 'auto',
                        background: 'linear-gradient(135deg, #1976d2 0%, #6d4ce3 100%)'
                      }}
                    >
                      {item.icon}
                    </Avatar>
                    <Typography variant="h5" component="h3" gutterBottom sx={{ fontWeight: 600 }}>
                      {item.title}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      {item.description}
                    </Typography>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* How It Works Section */}
      <Box sx={{ 
        backgroundColor: 'rgba(25, 118, 210, 0.04)', 
        py: { xs: 6, md: 10 },
        mt: 4
      }} className="animate-on-scroll">
        <Container maxWidth="lg">
          <Typography 
            component="h2" 
            variant="h3" 
            color="primary.main" 
            align="center"
            sx={{ 
              fontWeight: 700, 
              mb: 6,
              fontSize: { xs: '1.8rem', md: '2.5rem' }
            }}
          >
            How It Works
          </Typography>

          <Grid container spacing={isMobile ? 4 : 0} sx={{ position: 'relative' }}>
            {/* Connecting line between steps (hidden on mobile) */}
            {!isMobile && (
              <Box 
                sx={{ 
                  position: 'absolute', 
                  top: '100px', 
                  left: '20%', 
                  right: '20%', 
                  height: '4px', 
                  bgcolor: 'primary.light',
                  zIndex: 0,
                  opacity: 0.3,
                  borderRadius: 2
                }} 
              />
            )}
            
            {[
              { 
                number: 1, 
                title: 'Enter Your Topic', 
                description: 'Simply tell us what you want to learn about.' 
              },
              { 
                number: 2, 
                title: 'AI Creates Your Path', 
                description: 'Our AI generates a structured learning path.' 
              },
              { 
                number: 3, 
                title: 'Start Learning', 
                description: 'Follow your personalized path to mastery.' 
              }
            ].map((step, index) => (
              <Grid 
                item 
                xs={12} 
                md={4} 
                key={index} 
                sx={{ 
                  textAlign: 'center',
                  position: 'relative',
                  zIndex: 1
                }}
              >
                <motion.div
                  whileHover={{ y: -5 }}
                  transition={{ duration: 0.3 }}
                >
                  <Box 
                    sx={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      p: 2
                    }}
                  >
                    <Avatar 
                      sx={{ 
                        width: 70, 
                        height: 70, 
                        bgcolor: 'primary.main', 
                        mb: 2,
                        fontSize: '1.8rem',
                        fontWeight: 'bold',
                        boxShadow: 2
                      }}
                    >
                      {step.number}
                    </Avatar>
                    <Typography 
                      variant="h5" 
                      component="h3" 
                      gutterBottom 
                      sx={{ fontWeight: 600, mt: 2 }}
                    >
                      {step.title}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      {step.description}
                    </Typography>
                  </Box>
                </motion.div>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Example Learning Paths Section */}
      <Container maxWidth="lg" sx={{ py: { xs: 6, md: 10 } }} className="animate-on-scroll">
        <Typography 
          component="h2" 
          variant="h3" 
          color="primary.main" 
          align="center"
          sx={{ 
            fontWeight: 700, 
            mb: 2,
            fontSize: { xs: '1.8rem', md: '2.5rem' }
          }}
        >
          Example Learning Paths
        </Typography>
        <Typography 
          variant="body1" 
          color="text.secondary" 
          align="center" 
          sx={{ mb: 6, maxWidth: 700, mx: 'auto' }}
        >
          Discover the power of AI-generated learning paths across various subjects
        </Typography>

        <Grid container spacing={3}>
          {[
            {
              title: 'Web Development Mastery',
              description: 'From HTML basics to advanced React applications',
              modules: 12,
              duration: '4 weeks'
            },
            {
              title: 'Data Science Fundamentals',
              description: 'Statistics, Python, and machine learning essentials',
              modules: 15,
              duration: '6 weeks'
            },
            {
              title: 'Digital Marketing Strategy',
              description: 'SEO, social media, and conversion optimization',
              modules: 8,
              duration: '3 weeks'
            }
          ].map((path, index) => (
            <Grid item xs={12} md={4} key={index}>
              <motion.div whileHover={{ y: -8 }} transition={{ duration: 0.3 }}>
                <Card 
                  sx={{ 
                    height: '100%', 
                    boxShadow: 2, 
                    borderRadius: 4,
                    overflow: 'hidden',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      boxShadow: 8
                    }
                  }}
                >
                  <Box sx={{ 
                    height: 12, 
                    bgcolor: index === 0 ? 'primary.main' : index === 1 ? 'secondary.main' : 'success.main' 
                  }} />
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Chip 
                        label="AI Generated" 
                        size="small" 
                        color="primary" 
                        sx={{ height: 24, fontSize: '0.7rem' }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {path.duration}
                      </Typography>
                    </Box>
                    <Typography variant="h6" component="h3" gutterBottom sx={{ fontWeight: 600 }}>
                      {path.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {path.description}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        <strong>{path.modules}</strong> modules
                      </Typography>
                      <Button 
                        variant="text" 
                        color="primary" 
                        endIcon={<ArrowRightAltIcon />}
                        component={RouterLink}
                        to="/generator"
                        sx={{ 
                          fontWeight: 600,
                          fontSize: '0.9rem',
                          '&:hover': { background: 'rgba(25, 118, 210, 0.08)' }
                        }}
                      >
                        Create similar
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Final CTA Section */}
      <Box 
        sx={{ 
          background: 'linear-gradient(135deg, #1976d2 0%, #6d4ce3 100%)',
          py: { xs: 6, md: 8 },
          mt: 6,
          borderRadius: { xs: 0, md: '30px 30px 0 0' },
          position: 'relative',
          overflow: 'hidden'
        }}
        className="animate-on-scroll"
      >
        {/* Background pattern */}
        <Box sx={{ 
          position: 'absolute', 
          width: '100%', 
          height: '100%', 
          top: 0, 
          left: 0, 
          opacity: 0.1,
          background: 'radial-gradient(circle, transparent 20%, #000 20%, #000 21%, transparent 21%), radial-gradient(circle, transparent 20%, #000 20%, #000 21%, transparent 21%)',
          backgroundSize: '40px 40px',
          backgroundPosition: '0 0, 20px 20px',
        }} />
        
        <Container maxWidth="md">
          <Stack spacing={4} alignItems="center" textAlign="center">
            <Typography
              variant="h3"
              component="h2"
              color="white"
              sx={{ 
                fontWeight: 700,
                fontSize: { xs: '1.8rem', md: '2.5rem' }
              }}
            >
              Start Your Learning Journey Today
            </Typography>
            <Typography variant="h6" color="white" sx={{ opacity: 0.9, maxWidth: '80%', mx: 'auto' }}>
              Create your first AI-generated learning path and unlock a new way of learning
            </Typography>
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.98 }}
              transition={{ duration: 0.2 }}
            >
              <Button
                variant="contained"
                color="secondary"
                size="large"
                component={RouterLink}
                to="/generator"
                endIcon={<ArrowForwardIcon />}
                sx={{
                  px: 5,
                  py: 2,
                  mt: 2,
                  fontSize: '1.1rem',
                  fontWeight: 'bold',
                  borderRadius: 8,
                  boxShadow: '0 8px 20px rgba(0,0,0,0.2)',
                  background: 'white',
                  color: 'primary.main',
                  '&:hover': {
                    background: 'white',
                    boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
                  }
                }}
              >
                Create Your Learning Path
              </Button>
            </motion.div>
          </Stack>
        </Container>
      </Box>
    </Box>
  );
}

export default HomePage; 
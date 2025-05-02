import React from 'react';
import { Link as RouterLink } from 'react-router';
import { Helmet } from 'react-helmet-async';
import {
  Typography,
  Button,
  Box,
  Container,
  Grid,
  Divider,
  Avatar,
  Card,
  CardContent,
} from '@mui/material';
import { motion } from 'framer-motion';
import DynamicFormIcon from '@mui/icons-material/DynamicForm';
import ChatIcon from '@mui/icons-material/Chat';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ArrowRightAltIcon from '@mui/icons-material/ArrowRightAlt';
import CardGiftcardIcon from '@mui/icons-material/CardGiftcard';

const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15
    }
  }
};

const whyFeatures = [
  { icon: <DynamicFormIcon fontSize="large" />, title: 'Interactive Modules', text: 'Structured content, quizzes, and resource recommendations.' },
  { icon: <ChatIcon fontSize="large" />, title: 'AI Chat Assistant', text: 'Instant answers to your questions, whenever you need them.' },
  { icon: <VolumeUpIcon fontSize="large" />, title: 'Audio Summaries', text: 'Optional audio explanations for flexible learning on-the-go.' }
];

const howSteps = [
  { number: 1, title: 'Enter Your Topic', text: 'Tell us exactly what you want to learn.' },
  { number: 2, title: 'AI Generates Your Course', text: 'Our advanced AI builds a custom learning path with structured modules.' },
  { number: 3, title: 'Start Learning Immediately', text: 'Dive straight into content tailored specifically for you.' }
];

const examplePaths = [
  { title: 'Web Development Mastery', meta: '(4 weeks, 12 modules)', desc: 'From basic HTML to advanced React applications.', color: 'primary.main' },
  { title: 'Data Science Fundamentals', meta: '(6 weeks, 15 modules)', desc: 'Master statistics, Python, and machine learning essentials.', color: 'secondary.main' },
  { title: 'Digital Marketing Strategy', meta: '(3 weeks, 8 modules)', desc: 'Comprehensive insights on SEO, social media, and conversion optimization.', color: 'success.main' }
];

function HomePage() {
  return (
    <Box>
      <Helmet>
        <title>MapMyLearn: Personalized AI Learning Paths</title>
        <meta
          name="description"
          content="Generate personalized learning paths with AI. MapMyLearn creates courses with interactive modules, AI chat, and audio summaries to help you learn any topic efficiently."
        />
      </Helmet>

      <motion.div initial="hidden" animate="visible" variants={fadeInUp}>
        <Container maxWidth="md" sx={{ py: { xs: 4, md: 6 }, textAlign: 'center' }}>
          <Typography variant="h2" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
            MAPMYLEARN
          </Typography>
          <Typography variant="h5" color="text.secondary" sx={{ mb: 2 }}>
            Personalized Learning Paths Powered by AI
          </Typography>
          <Typography variant="body1" sx={{ maxWidth: '750px', mx: 'auto' }}>
            Supercharge your learning journey with fully personalized, AI-generated courses designed specifically for your interests and goals.
          </Typography>
        </Container>
      </motion.div>

      <Divider sx={{ my: 6 }} />

      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.2 }}
        variants={fadeInUp}
      >
        <Container maxWidth="lg">
          <Typography variant="h3" component="h2" gutterBottom align="center" sx={{ mb: 1 }}>
            🚀 Why Choose MapMyLearn?
          </Typography>
          <Typography variant="body1" color="text.secondary" align="center" sx={{ maxWidth: '700px', mx: 'auto', mb: 5 }}>
            MapMyLearn empowers you to master any topic efficiently by creating fully personalized courses featuring:
          </Typography>
          <motion.div variants={staggerContainer}>
            <Grid container spacing={4} justifyContent="center">
              {whyFeatures.map((feature, index) => (
                <Grid item xs={12} sm={6} md={4} key={index} component={motion.div} variants={fadeInUp}>
                  <Card
                    sx={{
                      p: 3,
                      height: '100%',
                      textAlign: 'center',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 2,
                      boxShadow: 0,
                      transition: 'all 0.3s ease-in-out',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: 6,
                      }
                    }}
                  >
                    <Avatar sx={{ bgcolor: 'primary.main', color: 'white', width: 60, height: 60, mb: 2 }}>
                      {feature.icon}
                    </Avatar>
                    <Typography variant="h6" gutterBottom>
                      {feature.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {feature.text}
                    </Typography>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </motion.div>
        </Container>
      </motion.div>

      <Divider sx={{ my: 6 }} />

      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.2 }}
        variants={fadeInUp}
        style={{ backgroundColor: 'rgba(0, 122, 255, 0.04)', paddingBottom: '48px', paddingTop: '48px' }}
      >
        <Container maxWidth="md">
          <Typography variant="h3" component="h2" gutterBottom align="center" sx={{ mb: 5 }}>
            ✨ How Does it Work?
          </Typography>
          <motion.div variants={staggerContainer}>
            <Grid container spacing={4} justifyContent="center">
              {howSteps.map((step, index) => (
                <Grid item xs={12} md={4} key={index} component={motion.div} variants={fadeInUp}>
                  <Box
                    sx={{
                      textAlign: 'center',
                      p: 2,
                      borderRadius: 2,
                      transition: 'background-color 0.3s ease',
                      '&:hover': {
                         bgcolor: 'action.hover'
                      }
                    }}
                  >
                    <Avatar sx={{ bgcolor: 'primary.light', color: 'white', mx: 'auto', mb: 2, width: 56, height: 56, fontSize: '1.5rem', fontWeight: 'bold' }}>
                      {step.number}
                    </Avatar>
                    <Typography variant="h6" gutterBottom sx={{ mt: 1 }}>
                      {step.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {step.text}
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </motion.div>
        </Container>
      </motion.div>

      <Divider sx={{ my: 6 }} />

      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.2 }}
        variants={fadeInUp}
      >
        <Container maxWidth="lg">
          <Typography variant="h3" component="h2" gutterBottom align="center">
            📚 Example Learning Paths
          </Typography>
          <Typography variant="body1" color="text.secondary" align="center" sx={{ maxWidth: '700px', mx: 'auto', mb: 5 }}>
            Explore some popular AI-generated courses:
          </Typography>
          <motion.div variants={staggerContainer}>
            <Grid container spacing={4} justifyContent="center">
              {examplePaths.map((path, index) => (
                <Grid item xs={12} md={4} key={index} component={motion.div} variants={fadeInUp}>
                  <Card
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      borderTop: 4,
                      borderColor: path.color || 'primary.main',
                      borderRadius: 2,
                      boxShadow: 1,
                      transition: 'all 0.3s ease-in-out',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: 6,
                      }
                    }}
                  >
                    <CardContent sx={{ flexGrow: 1, p: 3 }}>
                      <Typography variant="h6" component="h3" gutterBottom>
                        {path.title}
                      </Typography>
                      <Typography variant="caption" display="block" color="text.secondary" sx={{ mb: 1 }}>
                        {path.meta}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {path.desc}
                      </Typography>
                    </CardContent>
                    <Box sx={{ mt: 'auto', p: 2, textAlign: 'right' }}>
                      <Button
                        component={RouterLink}
                        to="/generator"
                        variant="text"
                        size="small"
                        endIcon={<ArrowRightAltIcon />}
                      >
                        Create Similar
                      </Button>
                    </Box>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </motion.div>
        </Container>
      </motion.div>

      <Divider sx={{ my: 6 }} />

      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.2 }}
        variants={fadeInUp}
      >
        <Container maxWidth="md">
          <Box sx={{ textAlign: 'center', bgcolor: 'primary.main', color: 'primary.contrastText', py: { xs: 4, md: 6 }, borderRadius: 2, my: 4 }}>
            <Typography variant="h4" component="h2" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
              <CardGiftcardIcon fontSize="large" /> Exclusive Beta Offer!
            </Typography>
            <Typography variant="body1" sx={{ mb: 3, px: 2 }}>
              Join now and receive <Typography component="span" sx={{ fontWeight: 'bold', color: 'secondary.light' }}>3 free credits</Typography> to create and explore your personalized learning paths.
            </Typography>
            <Button
              component={RouterLink}
              to="/register"
              variant="contained"
              sx={{
                bgcolor: 'white',
                color: 'primary.main',
                '&:hover': {
                  bgcolor: 'grey.200',
                  transform: 'scale(1.03)',
                },
                py: 1.5,
                px: 4,
                fontWeight: 'bold',
                transition: 'transform 0.2s ease-in-out'
              }}
              size="large"
              endIcon={<ArrowForwardIcon />}
            >
              Start Your Free Trial Now
            </Button>
          </Box>
        </Container>
      </motion.div>
    </Box>
  );
}

export default HomePage; 
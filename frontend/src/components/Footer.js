import React from 'react';
import { Link as RouterLink } from 'react-router';
import { 
  Box, 
  Container, 
  Typography, 
  Link, 
  Grid, 
  Divider, 
  IconButton, 
  useTheme,
  useMediaQuery,
  Tooltip
} from '@mui/material';
import SchoolIcon from '@mui/icons-material/School';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import GitHubIcon from '@mui/icons-material/GitHub';
import XIcon from '@mui/icons-material/X';
import EmailIcon from '@mui/icons-material/Email';
import Logo from './shared/Logo';

function Footer() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const navItems = [
    { text: 'Home', path: '/', ariaLabel: 'Go to homepage' },
    { text: 'Generator', path: '/generator', ariaLabel: 'Go to generator' },
    { text: 'History', path: '/history', ariaLabel: 'View your history' },
  ];

  const socialLinks = [
    { icon: <LinkedInIcon />, url: 'https://www.linkedin.com/in/pablomiar', label: 'LinkedIn' },
    { icon: <GitHubIcon />, url: 'https://github.com/pma1999', label: 'GitHub' },
    { icon: <XIcon />, url: 'https://x.com/pablomiar', label: 'X (Twitter)' },
    { icon: <EmailIcon />, url: 'mailto:pablomiguelargudo@gmail.com', label: 'Email' },
  ];

  return (
    <Box
      component="footer"
      sx={{
        py: { xs: 4, md: 6 },
        mt: 'auto',
        background: theme => `linear-gradient(180deg, ${theme.palette.grey[50]} 0%, ${theme.palette.grey[100]} 100%)`,
        borderTop: '1px solid',
        borderColor: 'divider',
        boxShadow: '0px -2px 10px rgba(0, 0, 0, 0.05)',
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          {/* Brand Section */}
          <Grid item xs={12} md={4}>
            <Box 
              sx={{ 
                display: 'flex',
                alignItems: 'center',
                mb: 2,
                flexDirection: { xs: 'column', sm: 'row' },
                justifyContent: { xs: 'center', md: 'flex-start' }
              }}
            >
              <RouterLink to="/" aria-label="MapMyLearn homepage" style={{ textDecoration: 'none', color: 'inherit', display: 'inline-block' }}>
                <Logo height={58} sx={{ mr: { xs: 0, sm: 1 }, mb: { xs: 1, sm: 0 } }} />
              </RouterLink>
            </Box>
            <Typography 
              variant="body2" 
              color="text.secondary"
              sx={{ 
                mb: 2,
                textAlign: { xs: 'center', md: 'left' }
              }}
            >
              Personalized courses powered by AI. Discover your optimal learning journey with our cutting-edge technology.
            </Typography>
          </Grid>
          
          {/* Navigation Links */}
          <Grid item xs={12} sm={6} md={4}>
            <Typography 
              variant="subtitle1" 
              color="text.primary" 
              fontWeight="bold"
              sx={{ 
                mb: 2,
                textAlign: { xs: 'center', sm: 'left' }
              }}
            >
              Quick Links
            </Typography>
            <Box 
              sx={{ 
                display: 'flex', 
                flexDirection: 'column',
                alignItems: { xs: 'center', sm: 'flex-start' }
              }}
            >
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  component={RouterLink}
                  to={item.path}
                  color="text.secondary"
                  underline="hover"
                  aria-label={item.ariaLabel}
                  sx={{ 
                    mb: 1.5,
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      color: 'primary.main',
                      transform: 'translateX(3px)',
                    },
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  {item.text}
                </Link>
              ))}
            </Box>
          </Grid>
          
          {/* Connect Section */}
          <Grid item xs={12} sm={6} md={4}>
            <Typography 
              variant="subtitle1" 
              color="text.primary" 
              fontWeight="bold"
              sx={{ 
                mb: 2,
                textAlign: { xs: 'center', sm: 'left' }
              }}
            >
              Connect With Us
            </Typography>
            <Box 
              sx={{ 
                display: 'flex', 
                justifyContent: { xs: 'center', sm: 'flex-start' },
                mb: 3
              }}
            >
              {socialLinks.map((link, index) => (
                <Tooltip key={index} title={link.label} arrow placement="top">
                  <IconButton
                    aria-label={`Visit our ${link.label} page`}
                    size="medium"
                    sx={{
                      mr: 1,
                      color: 'text.secondary',
                      borderRadius: '8px',
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        backgroundColor: 'rgba(0, 0, 0, 0.04)',
                        transform: 'translateY(-3px)',
                        color: 'primary.main',
                      },
                    }}
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {link.icon}
                  </IconButton>
                </Tooltip>
              ))}
            </Box>
          </Grid>
        </Grid>
        
        <Divider sx={{ my: 3, opacity: 0.6 }} />
        
        <Box 
          sx={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center',
            flexDirection: { xs: 'column', sm: 'row' },
            textAlign: { xs: 'center', sm: 'left' }
          }}
        >
          <Typography variant="body2" color="text.secondary">
            {'© '}
            {new Date().getFullYear()}
            {' '}
            <Link color="inherit" component={RouterLink} to="/" underline="hover">
              MapMyLearn
            </Link>
            {' - AI-Powered Course Generator'}
          </Typography>
          
          {/* Legal Links */}
          <Box sx={{ mt: { xs: 2, sm: 0 } }}>
              <Link 
                  component={RouterLink} 
                  to="/terms" 
                  variant="body2" 
                  color="text.secondary" 
                  underline="hover"
                  sx={{ mr: 2 }}
              >
                  Terms & Conditions
              </Link>
              <Link 
                  component={RouterLink} 
                  to="/privacy" 
                  variant="body2" 
                  color="text.secondary" 
                  underline="hover"
              >
                  Privacy Policy
              </Link>
              {/* Add Cookie Policy link here if created */}
          </Box>
          
          {!isMobile && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: { xs: 1, sm: 0 } }}>
              Made with ❤️ for effective learning
            </Typography>
          )}
        </Box>
      </Container>
    </Box>
  );
}

export default React.memo(Footer); 
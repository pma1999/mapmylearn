import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Button, 
  Box,
  Container,
  useMediaQuery,
  useTheme,
  IconButton,
  Menu,
  MenuItem,
  Fade,
  Slide,
  Tooltip,
  Avatar,
  useScrollTrigger
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SchoolIcon from '@mui/icons-material/School';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import Fab from '@mui/material/Fab';
import Zoom from '@mui/material/Zoom';

const navItems = [
  { text: 'Home', path: '/', ariaLabel: 'Go to homepage' },
  { text: 'Generator', path: '/generator', ariaLabel: 'Go to generator page' },
  { text: 'History', path: '/history', ariaLabel: 'View your history' },
];

// Scroll to top button component
function ScrollTop(props) {
  const { children } = props;
  const trigger = useScrollTrigger({
    disableHysteresis: true,
    threshold: 100,
  });

  const handleClick = (event) => {
    const anchor = document.querySelector('#back-to-top-anchor');
    if (anchor) {
      anchor.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  };

  return (
    <Zoom in={trigger}>
      <Box
        onClick={handleClick}
        role="presentation"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          zIndex: 1000,
        }}
      >
        {children}
      </Box>
    </Zoom>
  );
}

const NavLogo = React.memo(() => (
  <Box 
    sx={{ 
      display: 'flex', 
      alignItems: 'center',
      transition: 'transform 0.3s ease-in-out',
      '&:hover': {
        transform: 'scale(1.05)',
      }
    }}
  >
    <SchoolIcon 
      sx={{ 
        mr: 1,
        fontSize: { xs: 28, md: 32 },
        color: theme => theme.palette.primary.light
      }} 
    />
    <Typography
      variant="h6"
      component={RouterLink}
      to="/"
      sx={{
        mr: 2,
        fontWeight: 700,
        letterSpacing: '0.3rem',
        color: 'inherit',
        textDecoration: 'none',
        flexGrow: 1,
        fontSize: { xs: '1.1rem', sm: '1.25rem', md: '1.4rem' },
        background: 'linear-gradient(45deg, #FFF 30%, rgba(255,255,255,0.8) 90%)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        textShadow: '0px 2px 3px rgba(0,0,0,0.1)',
      }}
      aria-label="Learny homepage"
    >
      LEARNY
    </Typography>
  </Box>
));

function Navbar() {
  const location = useLocation();
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);
  const [scrolled, setScrolled] = useState(false);
  
  // Handle scrolling effects
  const trigger = useScrollTrigger({
    disableHysteresis: true,
    threshold: 0,
  });

  useEffect(() => {
    const handleScroll = () => {
      const isScrolled = window.scrollY > 20;
      if (isScrolled !== scrolled) {
        setScrolled(isScrolled);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [scrolled]);

  const handleMenuOpen = useCallback((event) => {
    setAnchorEl(event.currentTarget);
  }, []);

  const handleMenuClose = useCallback(() => {
    setAnchorEl(null);
  }, []);

  const handleKeyDown = useCallback((event, path) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      window.location.href = path;
    }
  }, []);

  const DesktopNav = useMemo(() => (
    <Box sx={{ display: 'flex', alignItems: 'center' }}>
      {navItems.map((item) => (
        <Tooltip 
          key={item.path} 
          title={item.ariaLabel} 
          arrow 
          placement="bottom" 
          enterDelay={500}
        >
          <Button
            component={RouterLink}
            to={item.path}
            aria-label={item.ariaLabel}
            onKeyDown={(e) => handleKeyDown(e, item.path)}
            aria-current={location.pathname === item.path ? 'page' : undefined}
            sx={{ 
              color: 'white', 
              mx: 1.5,
              py: 1,
              px: 2,
              fontWeight: location.pathname === item.path ? 700 : 500,
              position: 'relative',
              overflow: 'hidden',
              borderRadius: '4px',
              textTransform: 'none',
              fontSize: '1rem',
              letterSpacing: '0.05rem',
              '&::after': {
                content: '""',
                position: 'absolute',
                bottom: 0,
                left: 0,
                width: location.pathname === item.path ? '100%' : '0%',
                height: '3px',
                backgroundColor: theme => theme.palette.secondary.light,
                transition: 'width 0.3s ease-in-out',
                borderRadius: '3px 3px 0 0',
              },
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                '&::after': {
                  width: '100%',
                },
              },
              '&:focus-visible': {
                outline: `2px solid ${theme.palette.secondary.light}`,
                outlineOffset: '2px',
              },
              transition: 'all 0.3s ease'
            }}
          >
            {item.text}
          </Button>
        </Tooltip>
      ))}
      
      {/* Optional user avatar button - uncomment if you have user authentication */}
      {/*
      <Tooltip title="Account settings">
        <IconButton 
          sx={{ 
            ml: 2,
            border: '2px solid rgba(255,255,255,0.7)',
            transition: 'all 0.3s ease',
            '&:hover': {
              borderColor: 'white',
              transform: 'scale(1.05)'
            }
          }}
          aria-label="User account"
        >
          <Avatar sx={{ width: 32, height: 32, bgcolor: theme.palette.secondary.main }}>U</Avatar>
        </IconButton>
      </Tooltip>
      */}
    </Box>
  ), [location.pathname, handleKeyDown, theme.palette.secondary.light]);

  const MobileNav = useMemo(() => (
    <>
      <IconButton
        size="large"
        edge="end"
        color="inherit"
        aria-label={open ? "Close main menu" : "Open main menu"}
        aria-controls={open ? 'mobile-menu' : undefined}
        aria-haspopup="true"
        aria-expanded={open ? 'true' : undefined}
        onClick={handleMenuOpen}
        sx={{
          transition: 'transform 0.2s ease',
          transform: open ? 'rotate(90deg)' : 'rotate(0)',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
          },
          '&:focus-visible': {
            outline: `2px solid ${theme.palette.secondary.light}`,
            outlineOffset: '2px',
          },
        }}
      >
        <MenuIcon />
      </IconButton>
      <Menu
        id="mobile-menu"
        anchorEl={anchorEl}
        open={open}
        onClose={handleMenuClose}
        TransitionComponent={Fade}
        MenuListProps={{
          'aria-labelledby': 'mobile-button',
          sx: {
            py: 1
          }
        }}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        sx={{
          mt: 1.5,
          '& .MuiPaper-root': {
            borderRadius: 2,
            boxShadow: '0 8px 16px rgba(0,0,0,0.15)',
            minWidth: 180,
            background: theme => `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`,
            border: '1px solid rgba(255,255,255,0.1)',
          }
        }}
      >
        {navItems.map((item) => (
          <MenuItem
            key={item.path}
            component={RouterLink}
            to={item.path}
            onClick={handleMenuClose}
            selected={location.pathname === item.path}
            aria-current={location.pathname === item.path ? 'page' : undefined}
            sx={{
              minWidth: '180px',
              padding: '12px 16px',
              borderRadius: 1,
              mx: 1,
              my: 0.5,
              color: 'white',
              position: 'relative',
              fontWeight: location.pathname === item.path ? 700 : 400,
              backgroundColor: location.pathname === item.path ? 'rgba(255,255,255,0.15) !important' : 'transparent',
              '&:hover': {
                backgroundColor: 'rgba(255,255,255,0.1) !important',
              },
              '&:focus-visible': {
                outline: `2px solid ${theme.palette.secondary.light}`,
                outlineOffset: '-2px',
              },
              '&::after': {
                content: '""',
                position: 'absolute',
                left: 0,
                top: '50%',
                transform: 'translateY(-50%)',
                height: '60%',
                width: location.pathname === item.path ? '3px' : '0px',
                backgroundColor: theme.palette.secondary.light,
                borderRadius: '0 3px 3px 0',
                transition: 'width 0.2s ease-in-out'
              },
              transition: 'all 0.2s ease-in-out',
            }}
          >
            {item.text}
          </MenuItem>
        ))}
      </Menu>
    </>
  ), [anchorEl, handleMenuClose, handleMenuOpen, location.pathname, open, theme]);

  return (
    <>
      <Slide appear={false} direction="down" in={!trigger}>
        <AppBar 
          position="fixed" 
          color="primary" 
          elevation={scrolled ? 8 : 2}
          sx={{
            boxShadow: scrolled ? '0 4px 20px rgba(0,0,0,0.2)' : '0 2px 10px rgba(0,0,0,0.1)',
            backdropFilter: 'blur(10px)',
            background: theme => scrolled 
              ? `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`
              : `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
            height: scrolled ? 64 : 80,
            transition: 'all 0.3s ease',
            borderBottom: '1px solid rgba(255,255,255,0.1)'
          }}
        >
          <Container maxWidth="lg">
            <Toolbar 
              disableGutters 
              sx={{ 
                height: '100%',
                justifyContent: 'space-between',
                transition: 'all 0.3s ease',
                py: scrolled ? 1 : 1.5,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
                <NavLogo />
              </Box>
              {isDesktop ? DesktopNav : MobileNav}
            </Toolbar>
          </Container>
        </AppBar>
      </Slide>
      
      {/* This element gives proper spacing below the fixed navbar */}
      <Toolbar id="back-to-top-anchor" sx={{ mb: 2 }} />
      
      {/* Scroll to top button */}
      <ScrollTop>
        <Fab
          color="secondary"
          size="small"
          aria-label="scroll back to top"
          sx={{
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: '0 6px 16px rgba(0,0,0,0.2)',
            },
            transition: 'all 0.3s ease',
          }}
        >
          <KeyboardArrowUpIcon />
        </Fab>
      </ScrollTop>
    </>
  );
}

export default React.memo(Navbar); 
import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';
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
  useScrollTrigger,
  Divider,
  Chip,
  Badge
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SchoolIcon from '@mui/icons-material/School';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import LogoutIcon from '@mui/icons-material/Logout';
import LoginIcon from '@mui/icons-material/Login';
import PersonIcon from '@mui/icons-material/Person';
import TokenIcon from '@mui/icons-material/Token';
import Fab from '@mui/material/Fab';
import Zoom from '@mui/material/Zoom';
import { useAuth } from '../services/authContext';

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
      aria-label="LearnCompass homepage"
    >
      LEARNCOMPASS
    </Typography>
  </Box>
));

function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));
  const [anchorEl, setAnchorEl] = useState(null);
  const [userMenuAnchorEl, setUserMenuAnchorEl] = useState(null);
  const open = Boolean(anchorEl);
  const userMenuOpen = Boolean(userMenuAnchorEl);
  const [scrolled, setScrolled] = useState(false);
  const { isAuthenticated, user, logout, loading, fetchUserCredits } = useAuth();
  
  // Auth-aware navigation items
  const navItems = useMemo(() => {
    const items = [
      { text: 'Home', path: '/', ariaLabel: 'Go to homepage' },
    ];
    
    // Only show these items when authenticated
    if (isAuthenticated) {
      items.push(
        { text: 'Generator', path: '/generator', ariaLabel: 'Go to generator page' },
        { text: 'History', path: '/history', ariaLabel: 'View your history' }
      );
    }
    
    return items;
  }, [isAuthenticated]);
  
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
  
  const handleUserMenuOpen = useCallback((event) => {
    setUserMenuAnchorEl(event.currentTarget);
    
    // Refresh user credits when menu is opened
    if (isAuthenticated && fetchUserCredits) {
      fetchUserCredits();
    }
  }, [isAuthenticated, fetchUserCredits]);

  const handleUserMenuClose = useCallback(() => {
    setUserMenuAnchorEl(null);
  }, []);

  const handleKeyDown = useCallback((event, path) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      window.location.href = path;
    }
  }, []);
  
  const handleLogout = useCallback(async () => {
    handleUserMenuClose();
    await logout();
    navigate('/');
  }, [logout, navigate, handleUserMenuClose]);

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
      
      {isAuthenticated ? (
        // User menu
        <>
          <Tooltip title="Account settings">
            <IconButton 
              onClick={handleUserMenuOpen}
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
              aria-controls={userMenuOpen ? 'user-menu' : undefined}
              aria-haspopup="true"
              aria-expanded={userMenuOpen ? 'true' : undefined}
            >
              <Badge
                overlap="circular"
                anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
                badgeContent={
                  user?.credits > 0 ? (
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        backgroundColor: theme.palette.secondary.main,
                        border: `2px solid ${theme.palette.background.paper}`,
                      }}
                    />
                  ) : null
                }
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: theme.palette.secondary.main }}>
                  {user?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                </Avatar>
              </Badge>
            </IconButton>
          </Tooltip>
          
          <Menu
            id="user-menu"
            anchorEl={userMenuAnchorEl}
            open={userMenuOpen}
            onClose={handleUserMenuClose}
            MenuListProps={{
              'aria-labelledby': 'user-button',
            }}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            {user && (
              <Box sx={{ px: 2, py: 1, minWidth: 180 }}>
                <Typography variant="subtitle1" noWrap>
                  {user.full_name || 'User'}
                </Typography>
                <Typography variant="body2" color="text.secondary" noWrap>
                  {user.email}
                </Typography>
                <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Chip
                    icon={<TokenIcon fontSize="small" />}
                    label={`${user.credits || 0} credits`}
                    size="small"
                    color={user.credits > 0 ? "primary" : "default"}
                    sx={{ 
                      fontWeight: 500,
                      transition: 'all 0.3s ease',
                      '& .MuiChip-icon': {
                        color: user.credits > 0 ? 'inherit' : theme.palette.text.secondary
                      }
                    }}
                  />
                </Box>
              </Box>
            )}
            <Divider />
            <MenuItem onClick={handleLogout}>
              <LogoutIcon fontSize="small" sx={{ mr: 1 }} />
              Logout
            </MenuItem>
          </Menu>
        </>
      ) : (
        // Login/Register buttons
        <>
          <Button
            component={RouterLink}
            to="/login"
            variant="outlined"
            startIcon={<LoginIcon />}
            sx={{ 
              color: 'white',
              borderColor: 'rgba(255,255,255,0.5)',
              '&:hover': {
                borderColor: 'white',
                backgroundColor: 'rgba(255,255,255,0.1)',
              }
            }}
          >
            Login
          </Button>
          
          <Button
            component={RouterLink}
            to="/register"
            variant="contained"
            startIcon={<PersonIcon />}
            sx={{ 
              ml: 2,
              backgroundColor: theme.palette.secondary.main,
              '&:hover': {
                backgroundColor: theme.palette.secondary.dark,
              }
            }}
          >
            Register
          </Button>
        </>
      )}
    </Box>
  ), [location.pathname, handleKeyDown, theme, isAuthenticated, user, userMenuOpen, userMenuAnchorEl, handleUserMenuOpen, handleUserMenuClose, handleLogout]);

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
          }
        }}
      >
        <MenuIcon />
      </IconButton>

      <Menu
        id="mobile-menu"
        anchorEl={anchorEl}
        open={open}
        onClose={handleMenuClose}
        MenuListProps={{
          'aria-labelledby': 'menu-button',
        }}
        TransitionComponent={Fade}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        {navItems.map((item) => (
          <MenuItem 
            key={item.path} 
            component={RouterLink} 
            to={item.path}
            selected={location.pathname === item.path}
            onClick={handleMenuClose}
            sx={{
              minWidth: 150,
              fontSize: '1rem',
              py: 1.5
            }}
          >
            {item.text}
          </MenuItem>
        ))}
        
        <Divider sx={{ my: 1 }} />
        
        {isAuthenticated ? (
          <>
            {user && (
              <Box sx={{ px: 2, py: 1 }}>
                <Typography variant="subtitle2" noWrap>
                  {user.full_name || 'User'}
                </Typography>
                <Typography variant="body2" color="text.secondary" noWrap sx={{ fontSize: '0.8rem' }}>
                  {user.email}
                </Typography>
                <Box sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
                  <Chip
                    icon={<TokenIcon fontSize="small" />}
                    label={`${user.credits || 0} credits`}
                    size="small"
                    color={user.credits > 0 ? "primary" : "default"}
                    sx={{ 
                      fontWeight: 500,
                      fontSize: '0.8rem',
                      transition: 'all 0.3s ease',
                      '& .MuiChip-icon': {
                        color: user.credits > 0 ? 'inherit' : theme.palette.text.secondary
                      }
                    }}
                  />
                </Box>
              </Box>
            )}
            <MenuItem onClick={handleLogout}>
              <LogoutIcon fontSize="small" sx={{ mr: 1 }} />
              Logout
            </MenuItem>
          </>
        ) : (
          <>
            <MenuItem 
              component={RouterLink} 
              to="/login"
              onClick={handleMenuClose}
            >
              <LoginIcon fontSize="small" sx={{ mr: 1 }} />
              Login
            </MenuItem>
            <MenuItem 
              component={RouterLink} 
              to="/register"
              onClick={handleMenuClose}
            >
              <PersonIcon fontSize="small" sx={{ mr: 1 }} />
              Register
            </MenuItem>
          </>
        )}
      </Menu>
    </>
  ), [anchorEl, open, handleMenuOpen, handleMenuClose, theme.palette.secondary.light, location.pathname, navItems, isAuthenticated, user, handleLogout]);

  return (
    <>
      <AppBar 
        position="sticky" 
        sx={{ 
          backgroundColor: scrolled ? 'rgba(25, 118, 210, 0.95)' : 'rgba(25, 118, 210, 0.8)',
          backdropFilter: 'blur(8px)',
          boxShadow: scrolled ? 3 : 0,
          transition: 'all 0.3s ease',
        }}
        id="back-to-top-anchor"
      >
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={{ py: { xs: 1.5, md: 1 } }}>
            <NavLogo />
            <Box sx={{ flexGrow: 1 }} />
            {isDesktop ? DesktopNav : MobileNav}
          </Toolbar>
        </Container>
      </AppBar>
      
      <ScrollTop>
        <Fab
          color="secondary"
          size="small"
          aria-label="scroll back to top"
          sx={{
            boxShadow: 3,
            '&:hover': {
              backgroundColor: theme => theme.palette.secondary.dark,
            }
          }}
        >
          <KeyboardArrowUpIcon />
        </Fab>
      </ScrollTop>
    </>
  );
}

export default Navbar; 
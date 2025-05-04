import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router';
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
import CreditPurchaseDialog from './payments/CreditPurchaseDialog';
import InfoTooltip from './shared/InfoTooltip';
import { helpTexts } from '../constants/helpTexts';
import Logo from './shared/Logo';

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
    <RouterLink to="/" aria-label="MapMyLearn homepage" style={{ textDecoration: 'none', color: 'inherit', display: 'flex', alignItems: 'center' }}>
      <Logo height={58} sx={{ display: 'block' }} />
    </RouterLink>
  </Box>
));

// Assume AUDIO_CREDIT_COST is defined globally or imported (e.g., 1)
const AUDIO_CREDIT_COST = 1;

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
  const [purchaseDialogOpen, setPurchaseDialogOpen] = useState(false);
  
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

  const handlePurchaseCredits = () => {
    handleUserMenuClose();
    setPurchaseDialogOpen(true);
  };

  const handlePurchaseDialogClose = () => {
    setPurchaseDialogOpen(false);
  };

  // Component for the visible Credit Chip + Tooltip
  const CreditDisplay = ({ onClick, credits }) => (
    <Tooltip title={helpTexts.navbarCreditsTooltip}>
      <Chip
        icon={<TokenIcon fontSize="small" />}
        label={`${credits ?? 0} credits`}
        size="small"
        color={credits > 0 ? "primary" : "default"}
        onClick={onClick}
        sx={{
          fontWeight: 500,
          transition: 'all 0.3s ease',
          ml: 1,
          cursor: 'pointer',
          color: theme.palette.primary.contrastText,
          backgroundColor: theme.palette.primary.main,
          border: `1px solid ${theme.palette.primary.dark}`,
          '& .MuiChip-icon': {
            color: theme.palette.primary.contrastText
          },
          '&:hover': {
             backgroundColor: theme.palette.primary.dark,
          },
        }}
      />
    </Tooltip>
  );

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
              color: theme.palette.primary.main, 
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
              backgroundColor: location.pathname === item.path ? theme.palette.action.hover : 'transparent',
              '&::after': {
                content: '""',
                position: 'absolute',
                bottom: 0,
                left: 0,
                width: location.pathname === item.path ? '100%' : '0%',
                height: '3px',
                backgroundColor: theme.palette.secondary.light,
                transition: 'width 0.3s ease-in-out',
                borderRadius: '3px 3px 0 0',
              },
              '&:hover': {
                backgroundColor: theme.palette.action.hover,
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
        // User menu and visible credits
        <>
          {/* Visible Credit Display */}
          <CreditDisplay onClick={handlePurchaseCredits} credits={user?.credits} />

          <Tooltip title="Account settings">
            <IconButton 
              onClick={handleUserMenuOpen}
              sx={{ 
                ml: 2,
                border: `2px solid ${theme.palette.primary.light}`,
                transition: 'all 0.3s ease',
                '&:hover': {
                  borderColor: theme.palette.primary.main,
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
            sx={{ '.MuiMenu-paper': { minWidth: 220 } }}
          >
            {user && (
              <Box sx={{ px: 2, py: 1 }}>
                <Typography variant="subtitle1" noWrap>
                  {user.full_name || 'User'}
                </Typography>
                <Typography variant="body2" color="text.secondary" noWrap>
                  {user.email}
                </Typography>
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
              color: theme.palette.primary.main,
              borderColor: theme.palette.primary.light,
              '&:hover': {
                borderColor: theme.palette.primary.main,
                backgroundColor: theme.palette.action.hover, 
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
  ), [location.pathname, handleKeyDown, theme, isAuthenticated, user, userMenuOpen, userMenuAnchorEl, handleUserMenuOpen, handleUserMenuClose, handleLogout, handlePurchaseCredits, navItems]);

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
            backgroundColor: theme.palette.action.hover,
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
            {/* ADDED Prominent Credit Purchase/Display MenuItem */}
            <Tooltip title={helpTexts.navbarCreditsTooltip} placement="left">
              <MenuItem onClick={() => { handleMenuClose(); handlePurchaseCredits(); }} sx={{ justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center'}}>
                  <TokenIcon fontSize="small" sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="body2">{user?.credits ?? 0} Credits</Typography>
                </Box>
                <Button size="small" variant="outlined" color="primary" sx={{ ml: 1, py: 0.2, px: 1, fontSize: '0.75rem' }}>Buy</Button>
              </MenuItem>
            </Tooltip>
             <Divider /> 
             
            {user && (
              <Box sx={{ px: 2, py: 1 }}>
                <Typography variant="subtitle2" noWrap>
                  {user.full_name || 'User'}
                </Typography>
                <Typography variant="body2" color="text.secondary" noWrap sx={{ fontSize: '0.8rem' }}>
                  {user.email}
                </Typography>
              </Box>
            )}
            <MenuItem onClick={() => { handleMenuClose(); handleLogout(); }}>
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
  ), [anchorEl, open, handleMenuOpen, handleMenuClose, theme, location.pathname, navItems, isAuthenticated, user, handleLogout, handlePurchaseCredits]);

  return (
    <>
      <AppBar 
        position="sticky" 
        sx={{ 
          backgroundColor: scrolled ? 'rgba(255, 255, 255, 0.85)' : 'rgba(255, 255, 255, 0.75)',
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
      
      <CreditPurchaseDialog
        open={purchaseDialogOpen}
        onClose={handlePurchaseDialogClose}
      />
    </>
  );
}

export default Navbar; 
import React from 'react';
import PropTypes from 'prop-types';
import { AppBar, Toolbar, IconButton, Tooltip, Box, ToggleButton, ToggleButtonGroup } from '@mui/material';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import MenuIcon from '@mui/icons-material/Menu';

/**
 * Mobile-only sticky bottom navigation bar for LearningPathView.
 * 
 * Provides quick access to submodule navigation (Prev/Next), 
 * intra-submodule tab switching (Content, Quiz, Chat, etc.),
 * and opening the module navigation drawer.
 */
const MobileBottomNavigation = ({
  onNavigate,
  activeModuleIndex,
  activeSubmoduleIndex,
  totalModules,
  totalSubmodulesInModule,
  activeTab,
  setActiveTab,
  availableTabs = [],
  onOpenMobileNav,
}) => {
  const isFirstSubmodule = activeModuleIndex === 0 && activeSubmoduleIndex === 0;
  const isLastSubmodule = activeModuleIndex === totalModules - 1 && activeSubmoduleIndex === totalSubmodulesInModule - 1;
  
  const handleTabChange = (event, newActiveTab) => {
    if (newActiveTab !== null) { 
      setActiveTab(newActiveTab);
    }
  };

  return (
    <AppBar 
      position="fixed" 
      color="inherit"
      sx={{ 
        top: 'auto', 
        bottom: 'calc(0px + env(safe-area-inset-bottom, 0px))',
        borderTop: (theme) => `1px solid ${theme.palette.divider}`,
        boxShadow: 'none',
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', px: { xs: 0.5, sm: 1 } }}>
        <Tooltip title="Modules Navigation" arrow>
          <IconButton
            data-tut="mobile-nav-open-button"
            color="primary"
            aria-label="open module navigation"
            onClick={onOpenMobileNav} 
            sx={{ p: { xs: 0.75, sm: 1 } }}
          >
            <MenuIcon sx={{ fontSize: { xs: '1.4rem', sm: '1.75rem' } }} />
          </IconButton>
        </Tooltip>

        <Tooltip title="Previous Submodule" arrow>
          <span data-tut="mobile-prev-button">
            <IconButton
              color="primary"
              aria-label="previous submodule"
              onClick={() => onNavigate('prev')}
              disabled={isFirstSubmodule}
              sx={{ p: { xs: 0.75, sm: 1 } }}
            >
              <NavigateBeforeIcon sx={{ fontSize: { xs: '1.4rem', sm: '1.75rem' } }} />
            </IconButton>
          </span>
        </Tooltip>

        <ToggleButtonGroup
          data-tut="mobile-tab-buttons"
          value={activeTab}
          exclusive
          onChange={handleTabChange}
          aria-label="submodule content type"
          size="small"
          sx={{ 
            flexShrink: 1, 
            minWidth: 0,
            overflowX: 'auto',
            whiteSpace: 'nowrap',
            '&::-webkit-scrollbar': {
              display: 'none',
            },
            scrollbarWidth: 'none',
            '& .MuiToggleButtonGroup-grouped': { 
               mx: { xs: 0.15, sm: 0.2 },
               border: 0,
               '&.Mui-disabled': { border: 0 },
               '&:not(:first-of-type)': { borderRadius: '50%', marginLeft: { xs: '2px', sm: '2px'} },
               '&:first-of-type': { borderRadius: '50%', marginLeft: { xs: '2px', sm: '2px'} }
            },
            mx: { xs: 0.1, sm: 0.25 },
          }}
        >
          {availableTabs.map((tab) => (
            <Tooltip key={tab.index} title={tab.tooltip || tab.label} arrow>
              <ToggleButton 
                value={tab.index} 
                aria-label={tab.label} 
                sx={{ 
                  borderRadius: '50%', 
                  p: { xs: 0.8, sm: 1 }
                }}
              >
                {React.cloneElement(tab.icon, { sx: { fontSize: { xs: '1.1rem', sm: '1.5rem' } } })} 
              </ToggleButton>
            </Tooltip>
          ))}
        </ToggleButtonGroup>
        
        <Tooltip title="Next Submodule" arrow>
          <span data-tut="mobile-next-button">
            <IconButton
              color="primary"
              aria-label="next submodule"
              onClick={() => onNavigate('next')}
              disabled={isLastSubmodule}
              sx={{ p: { xs: 0.75, sm: 1 } }}
            >
              <NavigateNextIcon sx={{ fontSize: { xs: '1.4rem', sm: '1.75rem' } }} />
            </IconButton>
          </span>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
};

MobileBottomNavigation.propTypes = {
  onNavigate: PropTypes.func.isRequired,
  onOpenMobileNav: PropTypes.func.isRequired,
  activeModuleIndex: PropTypes.number,
  activeSubmoduleIndex: PropTypes.number,
  totalModules: PropTypes.number,
  totalSubmodulesInModule: PropTypes.number,
  activeTab: PropTypes.number.isRequired,
  setActiveTab: PropTypes.func.isRequired,
  availableTabs: PropTypes.arrayOf(PropTypes.shape({
      index: PropTypes.number.isRequired,
      label: PropTypes.string.isRequired,
      icon: PropTypes.element.isRequired,
      tooltip: PropTypes.string, 
  })).isRequired,
};

export default MobileBottomNavigation; 
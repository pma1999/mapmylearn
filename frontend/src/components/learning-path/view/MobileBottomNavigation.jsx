import React from 'react';
import PropTypes from 'prop-types';
import { AppBar, Toolbar, IconButton, Tooltip, Box } from '@mui/material';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import MenuIcon from '@mui/icons-material/Menu';

/**
 * Mobile-only sticky bottom navigation bar for LearningPathView.
 * 
 * Provides quick access to submodule navigation.
 */
const MobileBottomNavigation = ({
  onNavigate,
  onOpenMobileNav,
  activeModuleIndex,
  activeSubmoduleIndex,
  totalModules,
  totalSubmodulesInModule,
}) => {
  const isFirstSubmodule = activeModuleIndex === 0 && activeSubmoduleIndex === 0;
  const isLastSubmodule = activeModuleIndex === totalModules - 1 && activeSubmoduleIndex === totalSubmodulesInModule - 1;
  
  return (
    <AppBar 
      position="fixed" 
      color="inherit" // Use inherit to better match theme, can be adjusted
      sx={{ 
        top: 'auto', 
        bottom: 0, 
        borderTop: (theme) => `1px solid ${theme.palette.divider}`,
        boxShadow: 'none', // Optional: remove shadow if desired
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-around' }}>
        <Tooltip title="Previous Submodule" arrow>
          <span> {/* Span needed for tooltip on disabled button */}
            <IconButton
              color="primary"
              aria-label="previous submodule"
              onClick={() => onNavigate('prev')}
              disabled={isFirstSubmodule}
            >
              <NavigateBeforeIcon />
            </IconButton>
          </span>
        </Tooltip>

        <Tooltip title="Modules Navigation" arrow>
          <IconButton
            color="primary"
            aria-label="open module navigation"
            onClick={onOpenMobileNav}
          >
            <MenuIcon />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="Next Submodule" arrow>
           <span> {/* Span needed for tooltip on disabled button */}
             <IconButton
               color="primary"
               aria-label="next submodule"
               onClick={() => onNavigate('next')}
               disabled={isLastSubmodule}
             >
               <NavigateNextIcon />
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
};

export default MobileBottomNavigation; 
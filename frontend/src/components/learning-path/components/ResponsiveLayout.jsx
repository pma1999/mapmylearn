import React from 'react';
import PropTypes from 'prop-types';
import { Grid, Box, Drawer, Typography } from '@mui/material';
import { DRAWER_WIDTH } from '../constants/viewConstants';

/**
 * Responsive layout component that handles mobile vs desktop layouts
 */
const ResponsiveLayout = ({
  isMobileLayout,
  theme,
  
  // Mobile drawer props
  mobileNavOpen,
  onMobileNavClose,
  drawerTitle = "Modules",
  
  // Content components
  navigationComponent,
  contentComponent,
  mobileBottomNavigation,
  
  // Layout props
  navigationGridProps = { xs: 12, md: 4 },
  contentGridProps = { xs: 12, md: 8 },
  containerSx = {}
}) => {
  if (isMobileLayout) {
    return (
      <>
        {/* Mobile Content Panel */}
        <Box sx={{ height: '100%' }}>
          {contentComponent}
        </Box>

        {/* Mobile Navigation Drawer */}
        <Drawer
          anchor="left"
          open={mobileNavOpen}
          onClose={onMobileNavClose}
          ModalProps={{ keepMounted: true }}
          PaperProps={{ sx: { width: DRAWER_WIDTH } }}
        >
          <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
            <Typography variant="h6">{drawerTitle}</Typography>
          </Box>
          {navigationComponent}
        </Drawer>

        {/* Mobile Bottom Navigation */}
        {mobileBottomNavigation}
      </>
    );
  }

  // Desktop Layout
  return (
    <Grid 
      container 
      spacing={{ xs: 0, md: 2 }} 
      sx={{ height: '100%', flexGrow: 1, ...containerSx }}
    >
      <Grid 
        item 
        {...navigationGridProps}
        sx={{ 
          height: { xs: 'auto', md: '100%' }, 
          pb: { xs: 2, md: 0 } 
        }}
      >
        {navigationComponent}
      </Grid>
      <Grid item {...contentGridProps}>
        {contentComponent}
      </Grid>
    </Grid>
  );
};

ResponsiveLayout.propTypes = {
  isMobileLayout: PropTypes.bool.isRequired,
  theme: PropTypes.object.isRequired,
  mobileNavOpen: PropTypes.bool.isRequired,
  onMobileNavClose: PropTypes.func.isRequired,
  drawerTitle: PropTypes.string,
  navigationComponent: PropTypes.node.isRequired,
  contentComponent: PropTypes.node.isRequired,
  mobileBottomNavigation: PropTypes.node,
  navigationGridProps: PropTypes.object,
  contentGridProps: PropTypes.object,
  containerSx: PropTypes.object
};

export default ResponsiveLayout;

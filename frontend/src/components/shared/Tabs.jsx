import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Box, Tab, Tabs as MuiTabs, useMediaQuery, useTheme } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * Reusable tabbed interface component
 * 
 * @param {Object} props Component props
 * @param {Array} props.tabs Array of tab objects with label and icon
 * @param {Array} props.children Array of tab panel content components
 * @param {string} props.defaultTab Optional default selected tab index
 * @param {string} props.ariaLabel Accessibility label for the tab list
 * @returns {JSX.Element} Tabs component
 */
const Tabs = ({ tabs, children, defaultTab = 0, ariaLabel = 'tabbed content' }) => {
  const [activeTab, setActiveTab] = useState(defaultTab);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  // Animation variants for tab content
  const contentVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
    exit: { opacity: 0, y: -10, transition: { duration: 0.2 } }
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <MuiTabs 
          value={activeTab} 
          onChange={handleTabChange} 
          aria-label={ariaLabel}
          variant={isMobile ? "scrollable" : "standard"}
          scrollButtons={isMobile ? "auto" : false}
          allowScrollButtonsMobile
          sx={{
            '& .MuiTab-root': {
              minWidth: { xs: 'auto', sm: 100 },
              py: { xs: 1, sm: 1.5 },
              px: { xs: 2, sm: 3 },
              fontSize: { xs: '0.8rem', sm: '0.9rem' },
              fontWeight: 500,
            }
          }}
        >
          {tabs.map((tab, index) => (
            <Tab 
              key={index} 
              label={tab.label} 
              icon={tab.icon} 
              iconPosition="start"
              id={`tab-${index}`}
              aria-controls={`tabpanel-${index}`}
              sx={{
                opacity: activeTab === index ? 1 : 0.7,
                transition: 'opacity 0.3s ease'
              }}
            />
          ))}
        </MuiTabs>
      </Box>
      
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial="hidden"
          animate="visible"
          exit="exit"
          variants={contentVariants}
        >
          <TabPanel value={activeTab} index={activeTab}>
            {children[activeTab]}
          </TabPanel>
        </motion.div>
      </AnimatePresence>
    </Box>
  );
};

/**
 * Tab panel component to display content for each tab
 */
const TabPanel = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
      style={{ height: '100%' }}
    >
      {value === index && (
        <Box sx={{ p: { xs: 1, sm: 2 }, height: '100%' }}>
          {children}
        </Box>
      )}
    </div>
  );
};

Tabs.propTypes = {
  tabs: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      icon: PropTypes.node
    })
  ).isRequired,
  children: PropTypes.arrayOf(PropTypes.node).isRequired,
  defaultTab: PropTypes.number,
  ariaLabel: PropTypes.string
};

TabPanel.propTypes = {
  children: PropTypes.node,
  index: PropTypes.number.isRequired,
  value: PropTypes.number.isRequired
};

export default Tabs; 
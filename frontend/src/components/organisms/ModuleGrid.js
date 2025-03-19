import React from 'react';
import { Box, Grid, Typography, Alert, useTheme, useMediaQuery } from '@mui/material';
import { motion } from 'framer-motion';
import ModuleCard from './ModuleCard';

const ModuleGrid = ({ modules }) => {
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));
  
  // Variants for staggered animation of modules
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2
      }
    }
  };

  if (!modules || modules.length === 0) {
    return (
      <Alert severity="warning" sx={{ mt: 2, borderRadius: 2 }}>
        No modules found in the learning path.
      </Alert>
    );
  }

  // For desktop, render in a grid if there are 3 or more modules
  // For mobile and tablet, always stack vertically
  const useGridLayout = isDesktop && modules.length >= 3;

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {useGridLayout ? (
        <Grid container spacing={3}>
          {modules.map((module, index) => (
            <Grid item xs={12} md={6} key={index}>
              <ModuleCard module={module} index={index} />
            </Grid>
          ))}
        </Grid>
      ) : (
        <Box>
          {modules.map((module, index) => (
            <ModuleCard key={index} module={module} index={index} />
          ))}
        </Box>
      )}
    </motion.div>
  );
};

export default ModuleGrid; 
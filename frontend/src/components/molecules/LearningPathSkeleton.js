import React from 'react';
import {
  Box,
  Paper,
  Skeleton,
  Stack,
  useTheme,
  useMediaQuery
} from '@mui/material';

const LearningPathSkeleton = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header Skeleton */}
      <Paper 
        elevation={2} 
        sx={{ 
          p: { xs: 2, sm: 3, md: 4 }, 
          borderRadius: 2, 
          mb: 4 
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Skeleton 
            variant="circular" 
            width={isMobile ? 32 : 40} 
            height={isMobile ? 32 : 40} 
            sx={{ mr: 2 }} 
          />
          <Skeleton 
            variant="text" 
            width={isMobile ? 150 : 200} 
            height={isMobile ? 32 : 40} 
          />
        </Box>
        
        <Skeleton 
          variant="text" 
          width="80%" 
          height={isMobile ? 28 : 36} 
          sx={{ mb: 1 }} 
        />
        <Skeleton 
          variant="text" 
          width="60%" 
          height={isMobile ? 28 : 36} 
          sx={{ mb: 3 }} 
        />
        
        <Skeleton variant="rectangular" height={1} sx={{ mb: 3 }} />
        
        {isMobile ? (
          <Stack spacing={1.5}>
            <Skeleton variant="rectangular" height={36} width="100%" />
            <Skeleton variant="rectangular" height={36} width="100%" />
            <Skeleton variant="rectangular" height={36} width="100%" />
          </Stack>
        ) : (
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Skeleton variant="rectangular" height={40} width={150} />
            <Skeleton variant="rectangular" height={40} width={150} />
            <Skeleton variant="rectangular" height={40} width={150} />
          </Box>
        )}
      </Paper>
      
      {/* Modules Skeleton */}
      {[1, 2, 3].map((i) => (
        <Paper 
          key={i} 
          elevation={3} 
          sx={{ 
            mb: 3,
            p: { xs: 2, sm: 3 },
            borderRadius: 2
          }}
        >
          <Box 
            sx={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 2
            }}
          >
            <Skeleton 
              variant="text" 
              width={isMobile ? '70%' : '60%'} 
              height={isMobile ? 28 : 32} 
            />
            <Skeleton 
              variant="circular" 
              width={24} 
              height={24} 
            />
          </Box>
          
          {i === 1 && (
            <Box sx={{ px: 1 }}>
              <Skeleton 
                variant="text" 
                width="100%" 
                height={20} 
                sx={{ mb: 1 }} 
              />
              <Skeleton 
                variant="text" 
                width="90%" 
                height={20} 
                sx={{ mb: 1 }} 
              />
              <Skeleton 
                variant="text" 
                width="95%" 
                height={20} 
                sx={{ mb: 2 }} 
              />
              
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Skeleton variant="rounded" width={70} height={24} />
                <Skeleton variant="rounded" width={90} height={24} />
                <Skeleton variant="rounded" width={80} height={24} />
              </Box>
              
              <Skeleton variant="rectangular" height={1} sx={{ my: 3 }} />
              
              <Skeleton 
                variant="text" 
                width="40%" 
                height={24} 
                sx={{ mb: 2 }} 
              />
              
              {/* Submodules Skeleton */}
              {[1, 2].map((j) => (
                <Paper 
                  key={j} 
                  variant="outlined" 
                  sx={{ 
                    mb: 2,
                    p: 2,
                    borderRadius: 2
                  }}
                >
                  <Skeleton 
                    variant="text" 
                    width="70%" 
                    height={24} 
                    sx={{ mb: 1 }} 
                  />
                  <Skeleton 
                    variant="text" 
                    width="100%" 
                    height={16} 
                    sx={{ mb: 0.5 }} 
                  />
                  <Skeleton 
                    variant="text" 
                    width="90%" 
                    height={16} 
                    sx={{ mb: 2 }} 
                  />
                  
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <Skeleton variant="rounded" width={100} height={30} />
                  </Box>
                </Paper>
              ))}
            </Box>
          )}
        </Paper>
      ))}
    </Box>
  );
};

export default LearningPathSkeleton; 
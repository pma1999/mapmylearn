import React from 'react';
import { Box, Skeleton, Paper } from '@mui/material';
import { styled } from '@mui/material/styles';

const Container = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  borderRadius: theme.shape.borderRadius * 1.5,
  border: `1px solid ${theme.palette.divider}`,
}));

const CuriositySkeleton = () => {
  return (
    <Container>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <Skeleton variant="rounded" width={90} height={28} />
        <Box sx={{ flexGrow: 1 }} />
        <Skeleton variant="circular" width={28} height={28} />
      </Box>
      <Skeleton variant="text" width="90%" height={24} />
      <Skeleton variant="text" width="85%" height={24} />
      <Skeleton variant="text" width="60%" height={24} />
    </Container>
  );
};

export default CuriositySkeleton;

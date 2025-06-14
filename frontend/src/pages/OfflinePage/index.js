import React, { useEffect, useState } from 'react';
import { Box, Typography, List, ListItemButton, ListItemText, Divider } from '@mui/material';
import { Link as RouterLink } from 'react-router';
import { getOfflinePaths } from '../../services/offlineService';

const OfflinePage = () => {
  const [paths, setPaths] = useState([]);

  useEffect(() => {
    const data = getOfflinePaths();
    setPaths(Object.values(data));
  }, []);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Offline Learning Paths
      </Typography>
      {paths.length === 0 ? (
        <Typography>No offline courses saved.</Typography>
      ) : (
        <List>
          {paths.map((p) => (
            <React.Fragment key={p.offline_id}>
              <ListItemButton component={RouterLink} to={`/offline/${p.offline_id}`}> 
                <ListItemText primary={p.topic || 'Untitled'} />
              </ListItemButton>
              <Divider />
            </React.Fragment>
          ))}
        </List>
      )}
    </Box>
  );
};

export default OfflinePage;

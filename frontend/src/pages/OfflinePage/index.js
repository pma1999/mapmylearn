import React, { useEffect, useState } from 'react';
import { Box, Typography, List, ListItem, ListItemButton, ListItemText, Divider, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { Link as RouterLink } from 'react-router';
import { getOfflinePaths, removeOfflinePath } from '../../services/offlineService';

const OfflinePage = () => {
  const [paths, setPaths] = useState([]);

  useEffect(() => {
    const data = getOfflinePaths();
    setPaths(Object.values(data));
  }, []);

  const handleDelete = (id) => {
    removeOfflinePath(id);
    const updated = getOfflinePaths();
    setPaths(Object.values(updated));
  };

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
              <ListItem
                secondaryAction={
                  <IconButton edge="end" aria-label="delete" onClick={() => handleDelete(p.offline_id)}>
                    <DeleteIcon />
                  </IconButton>
                }
                disablePadding
              >
                <ListItemButton component={RouterLink} to={`/offline/${p.offline_id}`}>
                  <ListItemText primary={p.topic || 'Untitled'} />
                </ListItemButton>
              </ListItem>
              <Divider />
            </React.Fragment>
          ))}
        </List>
      )}
    </Box>
  );
};

export default OfflinePage;

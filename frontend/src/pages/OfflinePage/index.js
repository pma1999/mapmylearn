import React, { useEffect, useState } from 'react';
import { Box, Typography, List, ListItem, ListItemButton, ListItemText, Divider, IconButton, Button } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { Link as RouterLink } from 'react-router';
import { getOfflinePaths, removeOfflinePath } from '../../services/offlineService';
import { usePwaIntro } from '../../contexts/PwaIntroContext';

const OfflinePage = () => {
  const [paths, setPaths] = useState([]);
  const { openPwaIntro } = usePwaIntro();

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
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="h5" gutterBottom sx={{ mr: 2 }}>
          Offline Learning Paths
        </Typography>
        <Button size="small" variant="outlined" onClick={openPwaIntro}>
          App Tips
        </Button>
      </Box>
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

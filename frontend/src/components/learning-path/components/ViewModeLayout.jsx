import React from 'react';
import PropTypes from 'prop-types';
import { Box } from '@mui/material';
import { VIEW_MODES } from '../constants/viewConstants';

/**
 * Layout component that handles overview vs focus mode rendering
 */
const ViewModeLayout = ({
  viewMode,
  overviewComponent,
  focusComponent
}) => {
  return (
    <Box sx={{ flexGrow: 1, overflow: 'hidden', position: 'relative' }}>
      {viewMode === VIEW_MODES.OVERVIEW ? (
        <Box sx={{ height: '100%', overflowY: 'auto' }}>
          {overviewComponent}
        </Box>
      ) : (
        focusComponent
      )}
    </Box>
  );
};

ViewModeLayout.propTypes = {
  viewMode: PropTypes.oneOf(Object.values(VIEW_MODES)).isRequired,
  overviewComponent: PropTypes.node,
  focusComponent: PropTypes.node.isRequired
};

export default ViewModeLayout;

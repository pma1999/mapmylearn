import React, { useState, useEffect, memo, useCallback } from 'react';
import PropTypes from 'prop-types';
import {
  Typography,
  Box,
  CardContent,
  IconButton,
  Divider,
  Button,
  Chip,
  Grid,
  useMediaQuery,
  useTheme,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Switch,
  FormControlLabel,
  Stack,
  Popover,
  TextField,
  InputAdornment
} from '@mui/material';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import DownloadIcon from '@mui/icons-material/Download';
import DeleteIcon from '@mui/icons-material/Delete';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import PublicIcon from '@mui/icons-material/Public';
import LockIcon from '@mui/icons-material/Lock';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ShareIcon from '@mui/icons-material/Share';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import NotesIcon from '@mui/icons-material/Notes';
import SourceIcon from '@mui/icons-material/Source';

import { formatDate } from '../utils';
import { StyledCard, StyledChip } from '../styledComponents';
import TagsInput from './TagsInput';
import ConfirmationDialog from './ConfirmationDialog';

// Function to generate the full shareable link
const generateShareLink = (shareId) => {
  if (!shareId) return '';
  const origin = typeof window !== 'undefined' ? window.location.origin : '';
  return `${origin}/shared/${shareId}`;
};

/**
 * Card component for displaying a single history entry
 * @param {Object} props - Component props
 * @param {Object} props.entry - History entry data
 * @param {Function} props.onView - Handler for viewing entry details
 * @param {Function} props.onDelete - Handler for deleting entry
 * @param {Function} props.onToggleFavorite - Handler for toggling favorite status
 * @param {Function} props.onUpdateTags - Handler for updating tags
 * @param {Function} props.onExport - Handler for exporting entry as JSON
 * @param {Function} props.onDownloadPDF - Handler for downloading entry as PDF
 * @param {Function} props.onTogglePublic - Handler for toggling public status
 * @param {Function} props.onCopyShareLink - Handler for copying share link
 * @param {boolean} props.virtualized - Whether the card is being rendered in a virtualized list
 * @returns {JSX.Element} History entry card component
 */
const HistoryEntryCard = memo(({ 
  entry, 
  onView, 
  onDelete, 
  onToggleFavorite, 
  onUpdateTags, 
  onExport,
  onDownloadPDF,
  onTogglePublic,
  onCopyShareLink,
  virtualized = false
}) => {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [actionsMenuAnchor, setActionsMenuAnchor] = useState(null);
  const [sharePopoverAnchor, setSharePopoverAnchor] = useState(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.debug(`Entry ${entry.topic} - ID: ${entry.id}, path_id: ${entry.path_id}`);
    }
  }, [entry]);

  const handleAddTag = useCallback(async (newTag) => {
    const updatedTags = [...(entry.tags || []), newTag];
    await onUpdateTags(entry.path_id, updatedTags);
  }, [entry.tags, entry.path_id, onUpdateTags]);

  const handleDeleteTag = useCallback(async (tagToDelete) => {
    const updatedTags = (entry.tags || []).filter(tag => tag !== tagToDelete);
    await onUpdateTags(entry.path_id, updatedTags);
  }, [entry.tags, entry.path_id, onUpdateTags]);

  const handleOpenActionsMenu = useCallback((event) => {
    event.stopPropagation();
    setActionsMenuAnchor(event.currentTarget);
  }, []);

  const handleCloseActionsMenu = useCallback(() => {
    setActionsMenuAnchor(null);
  }, []);

  const handleDownloadJSON = useCallback(() => {
    handleCloseActionsMenu();
    onExport(entry.path_id);
  }, [handleCloseActionsMenu, onExport, entry.path_id]);

  const handleDownloadPDF = useCallback(() => {
    handleCloseActionsMenu();
    onDownloadPDF(entry.path_id);
  }, [handleCloseActionsMenu, onDownloadPDF, entry.path_id]);
  
  const handleViewDetails = useCallback(() => {
    onView(entry.path_id);
  }, [onView, entry.path_id]);
  
  const handleToggleFavorite = useCallback((event) => {
    event.stopPropagation();
    onToggleFavorite(entry.path_id, !entry.favorite);
  }, [onToggleFavorite, entry.path_id, entry.favorite]);
  
  const handleConfirmDelete = useCallback(() => {
    handleCloseActionsMenu();
    setConfirmDelete(true);
  }, [handleCloseActionsMenu]);
  
  const handleCancelDelete = useCallback(() => {
    setConfirmDelete(false);
  }, []);
  
  const handleDelete = useCallback(() => {
    onDelete(entry.path_id);
    setConfirmDelete(false);
  }, [onDelete, entry.path_id]);

  const handleOpenSharePopover = useCallback((event) => {
    event.stopPropagation();
    setSharePopoverAnchor(event.currentTarget);
  }, []);

  const handleCloseSharePopover = useCallback(() => {
    setSharePopoverAnchor(null);
  }, []);

  const handlePublicSwitchChange = useCallback(async (event) => {
    await onTogglePublic(entry.path_id, event.target.checked);
  }, [onTogglePublic, entry.path_id]);

  const handleCopyLink = useCallback((event) => {
    event.stopPropagation();
    onCopyShareLink(generateShareLink(entry.share_id));
  }, [onCopyShareLink, entry.share_id]);

  const sharePopoverOpen = Boolean(sharePopoverAnchor);
  const sharePopoverId = sharePopoverOpen ? 'share-popover-' + entry.path_id : undefined;
  const fullShareLink = generateShareLink(entry.share_id);

  const modulesCount = entry.modules_count ||
    (entry.path_data?.modules?.length) || 0;

  const cardElevation = entry.favorite ? 4 : 1;

  const cardContent = (
    <StyledCard
      variant="outlined"
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderColor: entry.favorite ? 'warning.main' : undefined,
      }}
      onClick={handleViewDetails}
    >
      <CardContent sx={{ flexGrow: 1, p: { xs: 1, sm: 1.5 }, display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
          <Tooltip title={entry.topic} arrow placement="top-start">
            <Typography variant="h6" sx={{
              fontWeight: 'bold',
              fontSize: { xs: '1rem', sm: '1.1rem' },
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              mr: 1,
              flexGrow: 1,
              lineHeight: 1.3
            }}>
              {entry.topic}
            </Typography>
          </Tooltip>
          <Box sx={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
             <Tooltip title={entry.favorite ? "Remove from Favorites" : "Add to Favorites"} arrow>
                <span>
                  <IconButton
                    aria-label={entry.favorite ? "Remove from favorites" : "Add to favorites"}
                    color={entry.favorite ? "warning" : "default"}
                    onClick={handleToggleFavorite}
                    size="small"
                    sx={{ p: 0.5 }}
                  >
                    {entry.favorite ? <StarIcon fontSize="small" /> : <StarBorderIcon fontSize="small" />}
                  </IconButton>
                </span>
              </Tooltip>
            <Tooltip title="Actions" arrow>
              <span>
                <IconButton
                  aria-label="Actions"
                  size="small"
                  onClick={handleOpenActionsMenu}
                  sx={{ p: 0.5 }}
                >
                  <MoreVertIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
          </Box>
        </Box>

        <Stack direction="row" spacing={1} sx={{ mb: 1, flexWrap: 'wrap' }} alignItems="center">
           <Tooltip title={`Created: ${formatDate(entry.creation_date)}`} arrow>
             <Stack direction="row" alignItems="center" spacing={0.5} sx={{ color: 'text.secondary' }}>
               <CalendarTodayIcon sx={{ fontSize: '0.875rem' }} />
               <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                 {formatDate(entry.creation_date, { dateStyle: 'short' })}
               </Typography>
             </Stack>
           </Tooltip>
           {entry.last_modified_date && (
             <Tooltip title={`Modified: ${formatDate(entry.last_modified_date)}`} arrow>
               <Stack direction="row" alignItems="center" spacing={0.5} sx={{ color: 'text.secondary' }}>
                 <AccessTimeIcon sx={{ fontSize: '0.875rem' }} />
                 <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                   {formatDate(entry.last_modified_date, { dateStyle: 'short' })}
                 </Typography>
               </Stack>
             </Tooltip>
           )}
        </Stack>

        <Stack direction="row" spacing={0.5} sx={{ mb: 1, flexWrap: 'wrap' }} alignItems="center">
          <StyledChip
            icon={<NotesIcon fontSize="small" />}
            label={`${modulesCount} modules`}
            size="small"
            variant="outlined"
          />
          <StyledChip
            icon={<SourceIcon fontSize="small" />}
            label={entry.source === 'generated' ? 'Generated' : 'Imported'}
            size="small"
            color={entry.source === 'generated' ? 'primary' : 'secondary'}
            variant="outlined"
          />
        </Stack>

        <TagsInput
          tags={entry.tags || []}
          onAddTag={handleAddTag}
          onDeleteTag={handleDeleteTag}
          maxDisplayTags={isMobile ? 1 : 2}
        />

        <Box sx={{ flexGrow: 1 }} />

        <Divider sx={{ my: 1 }} />
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Tooltip title={entry.is_public ? "Manage Sharing" : "Share"} arrow>
            <span>
              <Button
                aria-describedby={sharePopoverId}
                variant="text"
                color={entry.is_public ? "success" : "primary"}
                size="small"
                startIcon={<ShareIcon />}
                onClick={handleOpenSharePopover}
                sx={{ textTransform: 'none' }}
              >
                {entry.is_public ? "Shared" : "Share"}
              </Button>
            </span>
          </Tooltip>
        </Box>
      </CardContent>

      <Menu
        anchorEl={actionsMenuAnchor}
        open={Boolean(actionsMenuAnchor)}
        onClose={handleCloseActionsMenu}
        onClick={(e) => e.stopPropagation()}
      >
        <MenuItem onClick={handleDownloadJSON}>
          <ListItemIcon>
            <FileDownloadIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText primaryTypographyProps={{ variant: 'body2' }}>Download JSON</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleDownloadPDF}>
          <ListItemIcon>
            <PictureAsPdfIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText primaryTypographyProps={{ variant: 'body2' }}>Download PDF</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleConfirmDelete} sx={{ color: 'error.main' }}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText primaryTypographyProps={{ variant: 'body2' }}>Delete</ListItemText>
        </MenuItem>
      </Menu>

      <Popover
        id={sharePopoverId}
        open={sharePopoverOpen}
        anchorEl={sharePopoverAnchor}
        onClose={handleCloseSharePopover}
        onClick={(e) => e.stopPropagation()}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <Box sx={{ p: 2, minWidth: 280 }}>
          <FormControlLabel
            control={
              <Switch
                checked={entry.is_public || false}
                onChange={handlePublicSwitchChange}
                size="small"
              />
            }
            label={<Typography variant="body2">{entry.is_public ? 'Publicly Shared' : 'Private'}</Typography>}
            sx={{ mb: 1 }}
          />
          {entry.is_public && entry.share_id && (
            <Box>
              <Typography variant="caption" display="block" gutterBottom>
                Anyone with the link can view:
              </Typography>
              <TextField
                fullWidth
                size="small"
                variant="outlined"
                value={fullShareLink}
                InputProps={{
                  readOnly: true,
                  endAdornment: (
                    <InputAdornment position="end">
                      <Tooltip title="Copy Link" arrow>
                        <IconButton size="small" onClick={handleCopyLink} edge="end">
                          <ContentCopyIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </InputAdornment>
                  ),
                }}
                sx={{ '& .MuiInputBase-input': { fontSize: '0.8rem' } }}
              />
            </Box>
          )}
        </Box>
      </Popover>

      <ConfirmationDialog
        open={confirmDelete}
        title="Delete Course"
        message={`Are you sure you want to delete "${entry.topic}"? This action cannot be undone.`}
        onConfirm={handleDelete}
        onCancel={handleCancelDelete}
        isDestructive={true}
      />
    </StyledCard>
  );

  return (
    virtualized ? (
       <Box sx={{ height: '100%' }}>{cardContent}</Box>
    ) : (
      <Grid item xs={12} sm={6} md={4} lg={3} xl={2}>
         {cardContent}
      </Grid>
    )
  );
});

HistoryEntryCard.propTypes = {
  entry: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    path_id: PropTypes.string.isRequired,
    topic: PropTypes.string.isRequired,
    creation_date: PropTypes.string,
    last_modified_date: PropTypes.string,
    favorite: PropTypes.bool,
    tags: PropTypes.arrayOf(PropTypes.string),
    source: PropTypes.string,
    is_public: PropTypes.bool,
    share_id: PropTypes.string,
    modules_count: PropTypes.number,
    path_data: PropTypes.object
  }).isRequired,
  onView: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onToggleFavorite: PropTypes.func.isRequired,
  onUpdateTags: PropTypes.func.isRequired,
  onExport: PropTypes.func.isRequired,
  onDownloadPDF: PropTypes.func.isRequired,
  onTogglePublic: PropTypes.func.isRequired,
  onCopyShareLink: PropTypes.func.isRequired,
  virtualized: PropTypes.bool
};

export default HistoryEntryCard; 
import React from 'react';
import PropTypes from 'prop-types';
import { Box, Paper, Typography, IconButton, Tooltip } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { styled } from '@mui/material/styles';
import CuriosityCategoryChip from './CuriosityCategoryChip';

const Text = styled(Typography)(({ theme }) => ({
  display: '-webkit-box',
  WebkitLineClamp: 3,
  WebkitBoxOrient: 'vertical',
  overflow: 'hidden',
}));

const Container = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  borderRadius: theme.shape.borderRadius * 1.5,
  border: `1px solid ${theme.palette.divider}`,
  background:
    theme.palette.mode === 'dark'
      ? 'linear-gradient(180deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.02) 100%)'
      : 'linear-gradient(180deg, rgba(0,0,0,0.02) 0%, rgba(0,0,0,0.00) 100%)',
}));

const CuriosityCard = ({ text, category, onCopy }) => {
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text || '');
      if (onCopy) onCopy();
    } catch (e) {
      // noop
    }
  };

  return (
    <Container elevation={0}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <CuriosityCategoryChip category={category} />
        <Box sx={{ flexGrow: 1 }} />
        <Tooltip title="Copy">
          <IconButton size="small" onClick={handleCopy} aria-label="Copy curiosity">
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
      <Text variant="body1" sx={{ fontWeight: 500 }}>{text}</Text>
    </Container>
  );
};

CuriosityCard.propTypes = {
  text: PropTypes.string,
  category: PropTypes.string,
  onCopy: PropTypes.func,
};

export default CuriosityCard;

import { styled } from '@mui/material/styles';
import { Box, Card, Chip, Stack } from '@mui/material';

/**
 * Styled card with hover animation
 */
export const StyledCard = styled(Card)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  transition: 'transform 0.2s ease, box-shadow 0.2s ease, all 0.3s ease-in-out',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: theme.shadows[4],
  }
}));

/**
 * Styled chip with margin
 */
export const StyledChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
}));

/**
 * Action buttons wrapper with responsive layout
 */
export const ActionButtonsWrapper = styled(Stack)(({ theme }) => ({
  [theme.breakpoints.down('sm')]: {
    marginTop: theme.spacing(2),
    justifyContent: 'flex-start',
    width: '100%',
  },
}));

/**
 * Page header wrapper with responsive layout
 */
export const PageHeaderWrapper = styled(Box)(({ theme }) => ({
  display: 'flex', 
  justifyContent: 'space-between', 
  alignItems: 'flex-start',
  marginBottom: theme.spacing(3),
  [theme.breakpoints.down('sm')]: {
    flexDirection: 'column',
    alignItems: 'stretch',
  },
})); 
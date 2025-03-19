import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Divider,
  useTheme,
  useMediaQuery,
  Fade,
  Collapse
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import CloseIcon from '@mui/icons-material/Close';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import MarkdownRenderer from '../MarkdownRenderer';
import { motion } from 'framer-motion';

const SubmoduleCard = ({ submodule, index, moduleIndex }) => {
  const [showContent, setShowContent] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const fullScreen = useMediaQuery(theme.breakpoints.down('md'));
  
  const handleToggleContent = () => {
    setShowContent(!showContent);
  };
  
  const handleOpenModal = () => {
    setModalOpen(true);
  };
  
  const handleCloseModal = () => {
    setModalOpen(false);
  };

  // Animation variants for the card
  const cardVariants = {
    hidden: { opacity: 0, x: -10 },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: { 
        duration: 0.3,
        delay: index * 0.05 
      }
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={cardVariants}
    >
      <Card 
        variant="outlined" 
        sx={{ 
          borderRadius: 2,
          transition: 'all 0.3s ease',
          borderWidth: 1,
          borderColor: 'grey.300',
          '&:hover': {
            borderColor: theme.palette.primary.light,
            boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.08)'
          }
        }}
      >
        <CardContent sx={{ p: { xs: 2, sm: 2.5 } }}>
          <Box 
            sx={{ 
              display: 'flex', 
              alignItems: 'flex-start',
              justifyContent: 'space-between'
            }}
          >
            <Box sx={{ flex: 1 }}>
              <Typography 
                variant="h6" 
                sx={{ 
                  fontWeight: 500,
                  fontSize: { xs: '1rem', sm: '1.1rem' },
                  mb: 1,
                  lineHeight: 1.4,
                  color: theme.palette.text.primary
                }}
              >
                {submodule.title}
              </Typography>
              
              <Typography 
                variant="body2" 
                color="text.secondary"
                sx={{ 
                  mb: 2,
                  fontSize: { xs: '0.85rem', sm: '0.9rem' },
                  lineHeight: 1.5
                }}
              >
                {submodule.description}
              </Typography>
            </Box>
            
            {isMobile ? (
              <IconButton
                onClick={handleToggleContent}
                aria-expanded={showContent}
                aria-label="show content"
                size="small"
                sx={{
                  ml: 1,
                  mt: -0.5
                }}
              >
                {showContent ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            ) : null}
          </Box>
          
          <Box 
            sx={{ 
              display: 'flex', 
              justifyContent: 'flex-end',
              alignItems: 'center',
              mt: 1
            }}
          >
            {!isMobile && (
              <Button
                size="small"
                startIcon={<ExpandMoreIcon />}
                onClick={handleToggleContent}
                color="primary"
                sx={{ mr: 1 }}
              >
                {showContent ? 'Hide Details' : 'Show Details'}
              </Button>
            )}
            
            <Button
              size="small"
              color="primary"
              variant="outlined"
              startIcon={<MenuBookIcon />}
              onClick={handleOpenModal}
            >
              Full View
            </Button>
          </Box>
          
          <Collapse in={showContent} timeout="auto" unmountOnExit>
            <Divider sx={{ my: 2 }} />
            
            <Box
              sx={{
                mt: 2,
                maxHeight: '250px',
                overflow: 'auto',
                borderRadius: 1,
                backgroundColor: 'grey.50',
                p: 2
              }}
            >
              <MarkdownRenderer>
                {submodule.content}
              </MarkdownRenderer>
            </Box>
          </Collapse>
        </CardContent>
      </Card>
      
      {/* Full Content Modal */}
      <Dialog
        open={modalOpen}
        onClose={handleCloseModal}
        fullScreen={fullScreen}
        maxWidth="md"
        fullWidth
        TransitionComponent={Fade}
        transitionDuration={300}
        scroll="paper"
        PaperProps={{
          sx: {
            borderRadius: { xs: 0, sm: 2 },
            maxHeight: '90vh'
          }
        }}
      >
        <DialogTitle
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            px: { xs: 2, sm: 3 },
            py: { xs: 1.5, sm: 2 },
            bgcolor: 'primary.main',
            color: 'white',
          }}
        >
          <Typography variant="h6" component="div" sx={{ flex: 1, pr: 2 }}>
            Module {moduleIndex + 1}.{index + 1}: {submodule.title}
          </Typography>
          <IconButton
            edge="end"
            color="inherit"
            onClick={handleCloseModal}
            aria-label="close"
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        
        <DialogContent dividers sx={{ p: { xs: 2, sm: 3 } }}>
          <Typography 
            variant="subtitle1" 
            color="text.secondary"
            paragraph
            sx={{ 
              mb: 3, 
              fontStyle: 'italic',
              borderLeft: '4px solid',
              borderColor: 'primary.light',
              pl: 2,
              py: 1,
              bgcolor: 'grey.50',
              borderRadius: '0 4px 4px 0'
            }}
          >
            {submodule.description}
          </Typography>
          
          <Box sx={{ mt: 2 }}>
            <MarkdownRenderer>
              {submodule.content}
            </MarkdownRenderer>
          </Box>
        </DialogContent>
        
        <DialogActions sx={{ px: { xs: 2, sm: 3 }, py: 2 }}>
          <Button onClick={handleCloseModal} color="primary">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </motion.div>
  );
};

export default SubmoduleCard; 
import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Alert,
  CircularProgress,
  Typography,
  Button,
  Modal,
  IconButton,
  Backdrop, // For Modal background
  Fade, // For Modal transition
  Tooltip,
  Stack // For zoom controls
} from '@mui/material';
import ZoomOutMapIcon from '@mui/icons-material/ZoomOutMap'; // Expand icon
import CloseIcon from '@mui/icons-material/Close'; // Close icon
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'; // Zoom In
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'; // Zoom Out
import RestartAltIcon from '@mui/icons-material/RestartAlt'; // Reset
import FileDownloadIcon from '@mui/icons-material/FileDownload';

// Import pan and zoom library
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';

// Import mermaid package for diagram rendering
import mermaid from 'mermaid';

const modalStyle = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '90vw',
  maxWidth: '1200px',
  height: '90vh',
  bgcolor: 'background.paper',
  border: '1px solid #ddd', // Softer border
  borderRadius: '8px', // Rounded corners
  boxShadow: '0px 5px 15px rgba(0,0,0,0.2)', // Softer shadow
  p: { xs: 2, sm: 3 }, // Reduced padding slightly
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden' // Prevent modal itself from scrolling, content will scroll
};

const modalHeaderStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  pb: 2, // Padding bottom for separation
  mb: 2, // Margin bottom for separation
  borderBottom: '1px solid #eee', // Separator line
  flexShrink: 0
};

const modalContentWrapperStyle = {
  flexGrow: 1,
  overflow: 'hidden', // Important: parent must hide overflow for react-zoom-pan-pinch
  position: 'relative', // For positioning zoom controls
  background: '#f9f9f9' // Slight background for contrast
};

const modalContentStyle = {
  width: '100%',
  height: '100%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center'
};

const zoomControlsStyle = {
  position: 'absolute',
  bottom: '20px',
  right: '20px',
  zIndex: 10, // Ensure controls are on top
  bgcolor: 'rgba(255, 255, 255, 0.8)',
  borderRadius: '4px',
  padding: '4px'
};

/**
 * MermaidVisualization - Component to render Mermaid.js diagrams
 * 
 * This component provides a clean, responsive way to display Mermaid diagrams.
 * It includes error handling and loading states for better UX.
 */
const MermaidVisualization = ({ 
  mermaidSyntax, 
  title = "Interactive Visualization",
  sx = {},
  ...props 
}) => {
  const elementRef = useRef(null); // For the inline view
  const [isRendering, setIsRendering] = useState(false);
  const [renderError, setRenderError] = useState(null);
  const [renderedSvgString, setRenderedSvgString] = useState('');

  const [modalOpen, setModalOpen] = useState(false);

  const handleOpenModal = () => setModalOpen(true);
  const handleCloseModal = () => setModalOpen(false);

  /**
   * Downloads the rendered SVG as an SVG file
   */
  const handleDownloadSVG = useCallback(() => {
    if (!renderedSvgString) {
      console.warn('Cannot download SVG: No SVG content available');
      return;
    }

    try {
      const blob = new Blob([renderedSvgString], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/\s+/g, '_').substring(0, 30)}.svg`;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      console.log('SVG download successful');
    } catch (error) {
      console.error('SVG download failed:', error);
    }
  }, [renderedSvgString, title]);

  // Initialize Mermaid with configuration
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'neutral', 
      securityLevel: 'loose', 
      themeVariables: {
        primaryColor: '#333333',
        primaryTextColor: '#ffffff',
        primaryBorderColor: '#555555',
        lineColor: '#777777',
        sectionBkgColor: '#f0f0f0',
        altSectionBkgColor: '#ffffff',
        gridColor: '#e0e0e0',
        secondaryColor: '#5fa8d3',
        tertiaryColor: '#adcbe3'
      },
      flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis'
      },
      sequence: {
        useMaxWidth: true,
        wrap: true
      },
      journey: {
        useMaxWidth: true
      },
      timeline: {
        useMaxWidth: true
      },
      gitgraph: {
        useMaxWidth: true
      },
      c4: {
        useMaxWidth: true
      }
    });
  }, []);

  // Render Mermaid diagram when syntax changes
  useEffect(() => {
    if (!mermaidSyntax) {
      setRenderedSvgString(''); 
      return;
    }

    setIsRendering(true);
    setRenderError(null);
    setRenderedSvgString('');

    const renderDiagram = async () => {
      try {
        const newDiagramId = `mermaid-diagram-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        const themedMermaidSyntax = `%%{init: {"theme": "neutral"}}%%
${mermaidSyntax}`;
        
        try {
          const parseResult = await mermaid.parse(themedMermaidSyntax);
          if (!(typeof parseResult === 'object' && parseResult !== null && parseResult.diagramType)) {
            console.error('❌ Mermaid.parse() invalid result. Result:', parseResult);
            throw new Error('Mermaid failed to parse the syntax.');
          }
        } catch (parseError) {
          console.error('❌ Mermaid.parse() failed:', parseError);
          setRenderError(`Syntax error: ${parseError.message || 'Invalid diagram syntax'}`);
          setIsRendering(false);
          return; 
        }
        
        const { svg } = await mermaid.render(newDiagramId, themedMermaidSyntax);
        
        if (!svg || svg.length === 0) {
          console.warn('⚠️ Rendered SVG is empty despite parsing success.');
          throw new Error('Rendered SVG is empty. The diagram content might be unsupported for rendering.');
        }
        setRenderedSvgString(svg); 
        
      } catch (error) {
        console.error('❌ Error in renderDiagram process:', error);
        setRenderError(error.message || 'Failed to render diagram');
      } finally {
        setIsRendering(false);
      }
    };

    renderDiagram();
  }, [mermaidSyntax]);

  if (!mermaidSyntax && !isRendering) {
    return null; // Don't render anything if no syntax and not loading
  }

  return (
    <Box sx={{ width: '100%', ...sx }} {...props}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="h6" component="h3" sx={{ textAlign: 'center', flexGrow: 1 }}>
          {title}
        </Typography>
        {renderedSvgString && !isRendering && (
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Tooltip title="Download SVG">
              <IconButton onClick={handleDownloadSVG} size="small" sx={{ mr: 1 }}>
                <FileDownloadIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Expand Visualization">
              <IconButton onClick={handleOpenModal} size="small">
                <ZoomOutMapIcon />
              </IconButton>
            </Tooltip>
          </Box>
        )}
      </Box>
      
      {isRendering && (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 3, minHeight: '200px' }}>
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>Rendering Diagram...</Typography>
        </Box>
      )}
      
      {renderError && !isRendering && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to render visualization: {renderError}
          {mermaidSyntax && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2" color="text.secondary">Raw Mermaid syntax (first 500 chars):</Typography>
              <Paper variant="outlined" sx={{ p: 1, mt: 1, bgcolor: 'grey.50', maxHeight: '100px', overflowY: 'auto' }}>
                <Typography component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.75rem', margin: 0}}>
                  {mermaidSyntax.substring(0, 500)}{mermaidSyntax.length > 500 ? '...' : ''}
                </Typography>
              </Paper>
            </Box>
          )}
        </Alert>
      )}
      
      {!isRendering && renderedSvgString && !renderError && (
        <Paper 
          variant="outlined" 
          sx={{ 
            bgcolor: 'background.paper', 
            width: '100%',      
            overflow: 'hidden', 
            display: 'flex',    
            alignItems: 'center',
            justifyContent: 'center',
            p: 0, 
            aspectRatio: '16/9' // Force an aspect ratio for the container, e.g., 16:9 or similar
          }}
        >
          <TransformWrapper
            initialScale={1} 
            minScale={0.1} 
            maxScale={10}  
            centerOnInit={true} 
            limitToBounds={true} 
            doubleClick={{ disabled: true }}
            wheel={{ step: 0.2 }} 
            pinch={{ step: 5 }} 
          >
            <TransformComponent 
              wrapperStyle={{ width: "100%", height: "100%" }} 
              contentStyle={{ display: "flex", alignItems: "center", justifyContent: "center", width: "100%", height: "100%" }}
            >
              <div 
                dangerouslySetInnerHTML={{ __html: renderedSvgString }} 
                style={{ display: 'inline-block', maxWidth: '100%', maxHeight: '100%' }} // Ensure SVG inside also tries to respect bounds
              />
            </TransformComponent>
          </TransformWrapper>
        </Paper>
      )}

      {/* Modal for Expanded View */}
      <Modal
        open={modalOpen}
        onClose={handleCloseModal}
        closeAfterTransition
        slots={{ backdrop: Backdrop }}
        slotProps={{ backdrop: { timeout: 500 }}}
      >
        <Fade in={modalOpen}>
          <Box sx={modalStyle}>
            <Box sx={modalHeaderStyle}>
              <Typography variant="h6" component="h2">{title} (Expanded)</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Tooltip title="Download SVG">
                  <IconButton onClick={handleDownloadSVG} size="small" sx={{ mr: 1 }}>
                    <FileDownloadIcon />
                  </IconButton>
                </Tooltip>
                <IconButton onClick={handleCloseModal} aria-label="close"><CloseIcon /></IconButton>
              </Box>
            </Box>
            <Box sx={modalContentWrapperStyle}>
              <TransformWrapper
                initialScale={1}
                minScale={0.1}
                maxScale={30} // Significantly increased maxScale for modal
                centerOnInit
                limitToBounds={false} // Allow panning beyond initial bounds
                doubleClick={{ mode: 'zoomIn', step: 0.7 }} // Enable double click to zoom in
                wheel={{ step: 0.2 }}
                pinch={{ step: 5 }}
              >
                {({ zoomIn, zoomOut, resetTransform, ...rest }) => (
                  <>
                    <Box sx={zoomControlsStyle}>
                      <Stack direction="row" spacing={0.5}>
                        <Tooltip title="Zoom In (Ctrl + Scroll)">
                          <IconButton onClick={() => zoomIn(0.3)} size="small"><AddCircleOutlineIcon /></IconButton>
                        </Tooltip>
                        <Tooltip title="Zoom Out (Ctrl + Scroll)">
                          <IconButton onClick={() => zoomOut(0.3)} size="small"><RemoveCircleOutlineIcon /></IconButton>
                        </Tooltip>
                        <Tooltip title="Reset Zoom">
                          <IconButton onClick={() => resetTransform()} size="small"><RestartAltIcon /></IconButton>
                        </Tooltip>
                      </Stack>
                    </Box>
                    <TransformComponent 
                        wrapperStyle={{ width: "100%", height: "100%" }} 
                        contentStyle={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}
                    >
                      <div 
                        dangerouslySetInnerHTML={{ __html: renderedSvgString }} 
                        style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center', 
                          width: '100%', 
                          height: '100%' 
                        }} 
                      />
                    </TransformComponent>
                  </>
                )}
              </TransformWrapper>
            </Box>
          </Box>
        </Fade>
      </Modal>
    </Box>
  );
};

export default MermaidVisualization; 
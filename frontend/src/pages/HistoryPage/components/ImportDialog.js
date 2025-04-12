import React, { useState, useRef } from 'react';
import PropTypes from 'prop-types';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  IconButton,
  Divider,
  Alert,
  CircularProgress,
  useMediaQuery,
  useTheme
} from '@mui/material';
import UploadIcon from '@mui/icons-material/Upload';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

/**
 * Dialog for importing learning paths from JSON
 * @param {Object} props - Component props
 * @param {boolean} props.open - Whether the dialog is open
 * @param {Function} props.onClose - Handler for dialog close
 * @param {Function} props.onImport - Handler for import action
 * @returns {JSX.Element} Import dialog component
 */
const ImportDialog = ({ open, onClose, onImport }) => {
  const [jsonInput, setJsonInput] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Helper function for parsing and validation
  const parseAndValidateJson = (jsonString) => {
    try {
      const parsedData = JSON.parse(jsonString);
      
      // Basic structural validation based on learning_path.json
      if (!parsedData || typeof parsedData !== 'object') {
        throw new Error("Invalid JSON structure: Must be an object.");
      }
      if (typeof parsedData.topic !== 'string' || !parsedData.topic.trim()) {
        throw new Error("Import failed: JSON is missing a valid 'topic' field (must be a non-empty string).");
      }
      if (typeof parsedData.language !== 'string' || !parsedData.language.trim()) {
        // Optional: Add language check if it's strictly required
        // throw new Error("Import failed: JSON is missing a valid 'language' field (must be a non-empty string).");
      }
      // Check for the 'modules' array instead of 'nodes'
      if (!Array.isArray(parsedData.modules)) {
        throw new Error("Import failed: JSON is missing a valid 'modules' field (must be an array).");
      }
      // Optional: Add a check if modules array should not be empty
      // if (parsedData.modules.length === 0) {
      //   throw new Error("Import failed: 'modules' array cannot be empty.");
      // }
      
      return parsedData; // Return the validated object
    } catch (parseError) {
      // Rethrow specific errors or a generic one if JSON.parse fails
      if (parseError.message.startsWith('Import failed:')) {
        throw parseError;
      }
      throw new Error(`Invalid JSON format: ${parseError.message}`);
    }
  };

  const handleImport = async () => {
    if (!jsonInput.trim()) {
      setError('Please enter JSON data or upload a file');
      return;
    }

    try {
      setLoading(true);
      setError('');
      // Parse and validate JSON
      const learningPathObject = parseAndValidateJson(jsonInput);
      
      await onImport(learningPathObject); // Pass the object
      onClose(); // Close dialog on success
    } catch (err) {
      setError(err.message || 'Invalid JSON format');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Check file type
    if (!file.name.endsWith('.json')) {
      setError('Please upload a JSON file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target.result;
        // Validate JSON content directly, no need to parse twice
        parseAndValidateJson(content); // Validate structure
        setJsonInput(content); // Keep the raw string in the input field for display
        setError('');
      } catch (err) {
        // Use the error message from validation
        setError(err.message || 'The uploaded file contains invalid JSON or structure.');
      }
    };

    reader.onerror = () => {
      setError('Error reading the file');
    };

    reader.readAsText(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (!file.name.endsWith('.json')) {
        setError('Please upload a JSON file');
        return;
      }
      
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const content = e.target.result;
          parseAndValidateJson(content); // Validate structure
          setJsonInput(content); // Keep the raw string in the input field
          setError('');
        } catch (err) {
          // Use the error message from validation
          setError(err.message || 'The uploaded file contains invalid JSON or structure.');
        }
      };
      
      reader.onerror = () => {
        setError('Error reading the file');
      };
      
      reader.readAsText(file);
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      fullScreen={isMobile}
    >
      <DialogTitle>
        {isMobile && (
          <IconButton
            edge="start"
            color="inherit"
            onClick={onClose}
            aria-label="close"
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
        )}
        Import Learning Path
      </DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>
          Paste a valid learning path JSON or upload a JSON file to import it into your history.
        </DialogContentText>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Box
          sx={{
            border: '2px dashed',
            borderColor: 'divider',
            borderRadius: 1,
            p: { xs: 1, sm: 2 },
            mb: 2,
            textAlign: 'center',
            cursor: 'pointer'
          }}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".json"
            style={{ display: 'none' }}
            onChange={handleFileUpload}
            ref={fileInputRef}
          />
          <Typography sx={{ mb: 1, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
            Drag & drop a JSON file here or click to browse
          </Typography>
          <Button
            variant="outlined"
            component="span"
            startIcon={<UploadIcon />}
            size={isMobile ? "small" : "medium"}
          >
            Choose File
          </Button>
        </Box>
        
        <Divider sx={{ my: 2 }}>
          <Typography variant="body2" color="text.secondary">OR</Typography>
        </Divider>
        
        <TextField
          multiline
          rows={isMobile ? 6 : 10}
          fullWidth
          variant="outlined"
          value={jsonInput}
          onChange={(e) => setJsonInput(e.target.value)}
          placeholder="Paste your JSON here..."
          error={!!error}
        />
      </DialogContent>
      <DialogActions sx={{ 
        px: { xs: 2, sm: 3 }, 
        py: { xs: 2, sm: 1 }, 
        flexDirection: isMobile ? 'column' : 'row', 
        alignItems: isMobile ? 'stretch' : 'center' 
      }}>
        <Button 
          onClick={onClose}
          fullWidth={isMobile}
          sx={{ mb: isMobile ? 1 : 0 }}
        >
          Cancel
        </Button>
        <Button
          onClick={handleImport}
          color="primary"
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={16} /> : <UploadIcon />}
          fullWidth={isMobile}
        >
          Import
        </Button>
      </DialogActions>
    </Dialog>
  );
};

ImportDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onImport: PropTypes.func.isRequired
};

export default ImportDialog; 
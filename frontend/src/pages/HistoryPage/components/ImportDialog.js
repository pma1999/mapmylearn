import React, { useState, useRef, useCallback } from 'react';
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
  useTheme,
  Chip
} from '@mui/material';
import UploadIcon from '@mui/icons-material/Upload';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';

/**
 * Dialog for importing courses from JSON
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
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState(null);
  const [isValidJson, setIsValidJson] = useState(null);
  const fileInputRef = useRef(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleClose = () => {
    setJsonInput('');
    setError('');
    setLoading(false);
    setIsDragging(false);
    setFileName(null);
    setIsValidJson(null);
    onClose();
  };

  const parseAndValidateJson = useCallback((jsonString) => {
    if (!jsonString?.trim()) {
      setIsValidJson(null);
      return null;
    }
    try {
      const parsedData = JSON.parse(jsonString);
      
      if (!parsedData || typeof parsedData !== 'object') {
        throw new Error("Invalid JSON structure: Must be an object.");
      }
      if (typeof parsedData.topic !== 'string' || !parsedData.topic.trim()) {
        throw new Error("Missing required field: 'topic' (string).");
      }
      if (!Array.isArray(parsedData.modules)) {
        throw new Error("Missing required field: 'modules' (array).");
      }
      
      setIsValidJson(true);
      return parsedData;
    } catch (parseError) {
      let specificError = `Invalid JSON format: ${parseError.message}`;
      if (parseError.message.startsWith('Missing required field:')) {
        specificError = parseError.message;
      }
      setError(specificError);
      setIsValidJson(false);
      throw new Error(specificError);
    }
  }, []);

  const handleImport = async () => {
    if (!jsonInput.trim()) {
      setError('Please enter JSON data or upload a file');
      setIsValidJson(false);
      return;
    }

    try {
      setLoading(true);
      setError('');
      const learningPathObject = parseAndValidateJson(jsonInput);
      
      await onImport(learningPathObject);
      handleClose();
    } catch (err) {
      setError(err.message || 'Import failed');
      setIsValidJson(false);
    } finally {
      setLoading(false);
    }
  };

  const processFile = useCallback((file) => {
    if (!file) return;

    if (!file.name.endsWith('.json')) {
      setError('Please upload a valid JSON file (ends with .json)');
      setFileName(file.name);
      setIsValidJson(false);
      setJsonInput('');
      return;
    }

    setFileName(file.name);
    setError('');
    setIsValidJson(null);

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      setJsonInput(content);
      try {
        parseAndValidateJson(content);
      } catch (err) {
        console.error("Error validating uploaded file content:", err);
      }
    };

    reader.onerror = () => {
      setError('Error reading the file');
      setIsValidJson(false);
    };

    reader.readAsText(file);
  }, [parseAndValidateJson]);

  const handleFileUpload = useCallback((event) => {
    processFile(event.target.files[0]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [processFile]);

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.relatedTarget && e.currentTarget.contains(e.relatedTarget)) {
        return;
    }
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
      e.dataTransfer.clearData();
    }
  }, [processFile]);

  const handleTextInputChange = (e) => {
    const text = e.target.value;
    setJsonInput(text);
    setFileName(null);
    setIsValidJson(null);
    if (error) setError('');
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose}
      maxWidth="md" 
      fullWidth
      fullScreen={isMobile}
    >
      <DialogTitle>
        {isMobile && (
          <IconButton
            edge="start"
            color="inherit"
            onClick={handleClose}
            aria-label="close"
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
        )}
        Import Course
      </DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>
          Paste a valid course JSON or upload/drop a JSON file to import it into your history.
        </DialogContentText>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        {fileName && !error && isValidJson === true && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Valid JSON structure detected in "{fileName}". Ready to import.
          </Alert>
        )}
        {fileName && !error && isValidJson === false && (
          <Alert severity="warning" sx={{ mb: 2 }}>
             File "{fileName}" selected, but the JSON structure appears invalid or incomplete. Please check the content.
          </Alert>
        )}
        
        <Box
          sx={{
            border: '2px dashed',
            borderColor: isDragging ? 'primary.main' : 'divider',
            backgroundColor: isDragging ? 'action.hover' : 'transparent',
            borderRadius: 1,
            p: { xs: 2, sm: 3 },
            mb: 2,
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'border-color 0.2s ease-in-out, background-color 0.2s ease-in-out'
          }}
          onClick={() => fileInputRef.current?.click()}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".json,application/json"
            style={{ display: 'none' }}
            onChange={handleFileUpload}
            ref={fileInputRef}
          />
          <UploadIcon sx={{ fontSize: 40, color: 'action.active', mb: 1 }}/>
          <Typography sx={{ mb: 1, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
            {isDragging ? "Drop the JSON file here" : "Drag & drop a JSON file or click to browse"}
          </Typography>
          {fileName && (
              <Chip 
                icon={<InsertDriveFileIcon />} 
                label={fileName} 
                size="small" 
                color={isValidJson === true ? "success" : isValidJson === false ? "error" : "default"}
                variant="outlined"
                sx={{ mt: 1 }} 
                onDelete={!loading ? () => { 
                    setFileName(null); 
                    setJsonInput(''); 
                    setIsValidJson(null);
                    setError('');
                } : undefined}
             />
          )}
          {!fileName && (
            <Button
              variant="outlined"
              component="span"
              size={isMobile ? "small" : "medium"}
              sx={{ mt: 1 }}
            >
              Choose File
            </Button>
          )}
        </Box>
        
        <Divider sx={{ my: 2 }}>
          <Typography variant="body2" color="text.secondary">OR PASTE JSON</Typography>
        </Divider>
        
        <TextField
          multiline
          rows={isMobile ? 5 : 8}
          fullWidth
          variant="outlined"
          value={jsonInput}
          onChange={handleTextInputChange}
          placeholder="Paste your course JSON content here..."
          error={isValidJson === false}
          sx={{ 
             fontFamily: 'monospace',
            '& .MuiInputBase-input': { fontSize: '0.85rem' } 
          }}
        />
      </DialogContent>
      <DialogActions sx={{ 
        px: { xs: 2, sm: 3 }, 
        py: { xs: 2, sm: 1 }, 
        flexDirection: isMobile ? 'column' : 'row', 
        alignItems: isMobile ? 'stretch' : 'center' 
      }}>
        <Button 
          onClick={handleClose}
          fullWidth={isMobile}
          sx={{ mb: isMobile ? 1 : 0 }}
          disabled={loading}
        >
          Cancel
        </Button>
        <Button
          onClick={handleImport}
          color="primary"
          variant="contained"
          disabled={loading || isValidJson === false || !jsonInput.trim()}
          startIcon={loading ? <CircularProgress size={16} color="inherit" /> : <UploadIcon />}
          fullWidth={isMobile}
        >
          {loading ? 'Importing...' : 'Import Course'}
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
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  TextField,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  Button,
  Divider
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';

// Correct the import path for the API service again
import { sendMessage, clearChatHistory } from '../../services/api'; 

const SubmoduleChat = ({ pathId, moduleIndex, submoduleIndex, userId }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  // Generate a unique thread ID based on path, submodule, and user
  // IMPORTANT: Ensure userId is available and stable
  const [threadId, setThreadId] = useState(`user-${userId || 'anon'}-path-${pathId}-mod-${moduleIndex}-sub-${submoduleIndex}`);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Regenerate threadId if props change (e.g., navigating to a different submodule)
  useEffect(() => {
    setThreadId(`user-${userId || 'anon'}-path-${pathId}-mod-${moduleIndex}-sub-${submoduleIndex}`);
    setMessages([]); // Clear messages when context changes
    setError(null);
    setIsLoading(false);
  }, [pathId, moduleIndex, submoduleIndex, userId]);

  const handleSendMessage = useCallback(async () => {
    const messageText = inputValue.trim();
    if (!messageText || isLoading) return;

    const userMessage = { sender: 'user', text: messageText, timestamp: new Date() };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendMessage({
        path_id: pathId,
        module_index: moduleIndex,
        submodule_index: submoduleIndex,
        user_message: messageText,
        thread_id: threadId,
      });

      const aiMessage = { sender: 'ai', text: response.ai_response, timestamp: new Date() };
      setMessages((prev) => [...prev, aiMessage]);
      // Backend might refine/return thread_id, update if necessary (though likely stable with this format)
      // setThreadId(response.thread_id);
    } catch (err) {
      console.error("Error sending message:", err);
      setError(err.response?.data?.error?.message || err.message || 'Failed to get response from the assistant.');
      // Optionally remove the user's message if the send failed catastrophically
      // setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading, pathId, moduleIndex, submoduleIndex, threadId, userId]); // Added userId dependency

  const handleClearChat = useCallback(async () => {
    setError(null);
    setIsLoading(true);
    try {
      // Call backend to potentially clear server-side state if using persistent storage
      // With MemorySaver, this might not be strictly needed, but good practice
      await clearChatHistory({ thread_id: threadId });
      setMessages([]); // Clear frontend state regardless
      // Optionally reset threadId if backend confirms deletion or if desired
      // setThreadId(`user-${userId || 'anon'}-path-${pathId}-mod-${moduleIndex}-sub-${submoduleIndex}-cleared-${Date.now()}`);
    } catch (err) {
      console.error("Error clearing chat history:", err);
      setError(err.response?.data?.error?.message || err.message || 'Failed to clear chat history.');
    } finally {
      setIsLoading(false);
    }
  }, [threadId, pathId, moduleIndex, submoduleIndex, userId]); // Added dependencies

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault(); // Prevent new line on Enter
      handleSendMessage();
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(80vh - 200px)', maxHeight: '600px', p: 1 }}> {/* Adjust height as needed */}
      {/* Header/Clear Button */} 
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 1, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Typography variant="subtitle1">Chat with Submodule Assistant</Typography>
        <Button
          size="small"
          variant="outlined"
          color="warning"
          startIcon={<DeleteSweepIcon />}
          onClick={handleClearChat}
          disabled={isLoading || messages.length === 0}
        >
          Clear Chat
        </Button>
      </Box>

      {/* Message List */} 
      <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
        <List>
          {messages.map((msg, index) => (
            <ListItem key={index} sx={{ py: 1, display: 'flex', flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row' }}>
              <Paper 
                elevation={1} 
                sx={{
                  p: 1.5,
                  borderRadius: msg.sender === 'user' ? '15px 15px 0 15px' : '15px 15px 15px 0',
                  bgcolor: msg.sender === 'user' ? 'primary.light' : 'grey.200',
                  color: msg.sender === 'user' ? 'primary.contrastText' : 'text.primary',
                  maxWidth: '75%',
                  wordBreak: 'break-word',
                  ml: msg.sender === 'user' ? 1 : 0,
                  mr: msg.sender === 'ai' ? 1 : 0,
                }}
              >
                <ListItemText 
                  primary={msg.text}
                  secondary={msg.timestamp?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  secondaryTypographyProps={{
                    color: msg.sender === 'user' ? 'rgba(255, 255, 255, 0.7)' : 'text.secondary',
                    textAlign: msg.sender === 'user' ? 'right' : 'left',
                    fontSize: '0.75rem',
                    mt: 0.5
                  }}
                />
              </Paper>
            </ListItem>
          ))}
          {/* Invisible element to scroll to */} 
          <div ref={messagesEndRef} /> 
        </List>
      </Box>

      {/* Loading Indicator */} 
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 1 }}>
          <CircularProgress size={24} />
        </Box>
      )}

      {/* Error Display */} 
      {error && (
        <Alert severity="error" sx={{ mt: 1, mx: 1 }}>
          {error}
        </Alert>
      )}

      {/* Input Area */} 
      <Divider sx={{ my: 1 }} />
      <Box sx={{ p: 1, display: 'flex', alignItems: 'center' }}>
        <TextField
          fullWidth
          variant="outlined"
          size="small"
          placeholder="Ask something about this submodule..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          multiline
          maxRows={4}
          sx={{ mr: 1 }}
        />
        <IconButton 
          color="primary" 
          onClick={handleSendMessage} 
          disabled={!inputValue.trim() || isLoading}
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Box>
  );
};

export default SubmoduleChat; 
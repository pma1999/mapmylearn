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
  Divider,
  Link,
  ListItemIcon
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';
import ReactMarkdown from 'react-markdown';

// Correct the import path for the API service again
import { sendMessage, clearChatHistory } from '../../services/api'; 

// Define the component map for react-markdown -> MUI integration
const markdownComponents = {
  p: ({ node, ...props }) => <Typography variant="body1" paragraph {...props} />,
  h1: ({ node, ...props }) => <Typography variant="h1" component="h1" gutterBottom {...props} />,
  h2: ({ node, ...props }) => <Typography variant="h2" component="h2" gutterBottom {...props} />,
  h3: ({ node, ...props }) => <Typography variant="h3" component="h3" gutterBottom {...props} />,
  h4: ({ node, ...props }) => <Typography variant="h4" component="h4" gutterBottom {...props} />,
  h5: ({ node, ...props }) => <Typography variant="h5" component="h5" gutterBottom {...props} />,
  h6: ({ node, ...props }) => <Typography variant="h6" component="h6" gutterBottom {...props} />,
  ul: ({ node, ...props }) => <List dense sx={{ pt: 0, mt: 0, listStyleType: 'disc' }} {...props} />,
  ol: ({ node, ...props }) => <List dense component="ol" sx={{ pt: 0, mt: 0, listStyleType: 'decimal', pl: 4 }} {...props} />,
  li: ({ node, ordered, ...props }) => (
     ordered ?
     <ListItem sx={{ display: 'list-item', pt: 0, pb: 0.5 }} dense {...props} />
     :
     <ListItem sx={{ pt: 0, pb: 0.5 }} dense>
        <ListItemIcon sx={{ minWidth: 'auto', mr: 1, alignSelf: 'flex-start', mt: '6px' }}>
            <FiberManualRecordIcon sx={{ fontSize: '0.6em' }} />
        </ListItemIcon>
        {/* Wrap children in Typography for consistent styling within list items */}
        <Typography component="span" variant="body1">{props.children}</Typography>
     </ListItem>
  ),
  strong: ({ node, ...props }) => <Typography component="span" sx={{ fontWeight: 'bold' }} {...props} />,
  em: ({ node, ...props }) => <Typography component="span" sx={{ fontStyle: 'italic' }} {...props} />,
  a: ({ node, ...props }) => <Link target="_blank" rel="noopener noreferrer" {...props} />,
  code: ({ node, inline, className, children, ...props }) => {
    const match = /language-(\w+)/.exec(className || '');
    return !inline ? (
      <Paper component="pre" sx={{ p: 1.5, my: 1, overflowX: 'auto', bgcolor: 'grey.100', fontFamily: 'monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }} {...props}>
        <code>{children}</code>
      </Paper>
    ) : (
      <Typography
        component="code"
        sx={{
          px: '5px',
          py: '2px',
          borderRadius: '4px',
          bgcolor: 'rgba(0,0,0,0.08)',
          fontFamily: 'monospace',
          fontSize: '0.875rem'
        }}
        {...props}
      >
        {children}
      </Typography>
    );
  },
  blockquote: ({ node, ...props }) => (
    <Paper
      component="blockquote" // Use blockquote for semantics
      sx={{ pl: 2, my: 1, borderLeft: '4px solid', borderColor: 'divider', fontStyle: 'italic' }}
      {...props}
    >
      {props.children} {/* Explicitly render children */}
    </Paper>
  ),
  hr: ({ node, ...props }) => <Divider sx={{ my: 2 }} {...props} />,
  img: ({ node, ...props }) => <Box component="img" sx={{ maxWidth: '100%', height: 'auto' }} {...props} />,
  // table elements omitted as per spec
};

const SubmoduleChat = ({ pathId, moduleIndex, submoduleIndex, userId, submoduleContent, isTemporaryPath }) => {
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

  // Regenerate threadId and clear state if the context (path/submodule) changes
  useEffect(() => {
    // Ensure pathId is present before creating threadId or clearing state
    if (pathId) {
      setThreadId(`user-${userId || 'anon'}-path-${pathId}-mod-${moduleIndex}-sub-${submoduleIndex}`);
      setMessages([]); // Clear messages when context changes
      setError(null);
      setIsLoading(false);
    } else {
      // Handle case where pathId is initially null/undefined if necessary
      // e.g., show a message or disable chat input
      setError("Chat context (pathId) is not available.");
    }
  }, [pathId, moduleIndex, submoduleIndex, userId]); // Dependencies are correct

  const handleSendMessage = useCallback(async () => {
    const messageText = inputValue.trim();
    // Ensure pathId exists before sending
    if (!pathId || !messageText || isLoading) return;

    const userMessage = { sender: 'user', text: messageText, timestamp: new Date() };
    // Use functional update to ensure we have the latest messages state
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    const currentMessages = [...messages, userMessage]; // Use updated messages for condition check
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      // Base payload for the API call
      const payload = {
        path_id: pathId,
        module_index: moduleIndex,
        submodule_index: submoduleIndex,
        user_message: messageText,
        thread_id: threadId,
      };

      // Conditionally add context for the first message of a temporary path
      if (isTemporaryPath && currentMessages.length === 1) {
        payload.submodule_context = submoduleContent;
        console.log("Sending initial message for temporary path with context."); // Debug log
      }

      // Call the API service function
      const response = await sendMessage(payload);

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
    // Update dependencies for useCallback
  }, [inputValue, isLoading, pathId, moduleIndex, submoduleIndex, threadId, userId, isTemporaryPath, submoduleContent, messages]);

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
    // Update dependencies for useCallback
  }, [threadId, pathId, moduleIndex, submoduleIndex, userId]);

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
                {/* Conditionally render Markdown for AI, plain text for user */}
                {msg.sender === 'ai' ? (
                  <ReactMarkdown components={markdownComponents}>
                    {msg.text}
                  </ReactMarkdown>
                ) : (
                  <ListItemText
                    primary={msg.text}
                    sx={{ margin: 0 }} // Ensure no extra margin from ListItemText
                  />
                )}
                {/* Display timestamp separately for both message types */}
                <Typography
                  variant="caption"
                  display="block"
                  sx={{
                    color: msg.sender === 'user' ? 'rgba(255, 255, 255, 0.7)' : 'text.secondary',
                    textAlign: msg.sender === 'user' ? 'right' : 'left',
                    fontSize: '0.75rem',
                    mt: 0.5
                  }}
                >
                  {msg.timestamp?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </Typography>
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
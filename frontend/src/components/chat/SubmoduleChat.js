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
  ListItemIcon,
  Snackbar
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import ReactMarkdown from 'react-markdown';

// Correct the import path for the API service again
import { sendMessage, clearChatHistory, purchaseChatAllowance } from '../../services/api';
import { useAuth } from '../../services/authContext';

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

const SubmoduleChat = ({ pathId, moduleIndex, submoduleIndex, userId, submoduleContent, isTemporaryPath, pathData }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [error, setError] = useState(null);
  const [showPurchasePrompt, setShowPurchasePrompt] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const { fetchUserCredits } = useAuth();

  const [threadId, setThreadId] = useState(() => 
    pathId ? `user-${userId || 'anon'}-path-${pathId}-mod-${moduleIndex}-sub-${submoduleIndex}` : null
  );
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (pathId) {
      setThreadId(`user-${userId || 'anon'}-path-${pathId}-mod-${moduleIndex}-sub-${submoduleIndex}`);
      setMessages([]);
      setError(null);
      setIsLoading(false);
      setShowPurchasePrompt(false);
      setIsPurchasing(false);
    } else {
      setError("Chat context (pathId) is not available.");
      setThreadId(null);
    }
  }, [pathId, moduleIndex, submoduleIndex, userId]);

  const handleSendMessage = useCallback(async () => {
    const messageText = inputValue.trim();
    if (!pathId || !messageText || isLoading || isPurchasing) return;

    const userMessage = { sender: 'user', text: messageText, timestamp: new Date() };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);
    setShowPurchasePrompt(false);

    try {
      const payload = {
        path_id: pathId,
        module_index: moduleIndex,
        submodule_index: submoduleIndex,
        user_message: messageText,
        thread_id: threadId,
      };

      if (isTemporaryPath && pathData && typeof pathData === 'object') {
        payload.path_data = pathData;
        console.debug('Attaching ephemeral path_data to chat payload', payload.path_data);
      }

      const response = await sendMessage(payload);
      const aiMessage = { sender: 'ai', text: response.ai_response, timestamp: new Date() };
      setMessages((prev) => [...prev, aiMessage]);

    } catch (err) {
      console.error("Error sending message:", err);
      if (err.response?.status === 429) {
        setError("You've reached your daily free message limit.");
        setShowPurchasePrompt(true);
        setMessages((prev) => prev.slice(0, -1));
      } else {
        setError(err.message || 'Failed to get response from the assistant.');
        setMessages((prev) => prev.slice(0, -1)); 
      }
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading, isPurchasing, pathId, moduleIndex, submoduleIndex, threadId, userId, isTemporaryPath, pathData, messages]);

  const handleClearChat = useCallback(async () => {
    setError(null);
    setShowPurchasePrompt(false);
    setIsLoading(true);
    try {
      await clearChatHistory({ thread_id: threadId });
      setMessages([]);
    } catch (err) {
      console.error("Error clearing chat history:", err);
      setError(err.message || 'Failed to clear chat history.');
    } finally {
      setIsLoading(false);
    }
  }, [threadId]);

  const handlePurchaseAllowance = useCallback(async () => {
    setError(null);
    setIsPurchasing(true);
    try {
      const response = await purchaseChatAllowance();
      setShowPurchasePrompt(false);
      setSnackbar({
        open: true,
        message: response.message || 'Chat allowance purchased successfully!',
        severity: 'success',
      });
      fetchUserCredits();
    } catch (err) {
      console.error("Error purchasing chat allowance:", err);
      setError(err.message || 'Failed to purchase chat allowance. Do you have enough credits?');
      setSnackbar({
        open: true,
        message: err.message || 'Failed to purchase allowance.',
        severity: 'error',
      });
    } finally {
      setIsPurchasing(false);
    }
  }, [fetchUserCredits]);

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleCloseSnackbar = (event, reason) => {
    if (reason === 'clickaway') {
      return;
    }
    setSnackbar({ ...snackbar, open: false });
  };

  return (
    <Box data-tut="submodule-chat" sx={{ display: 'flex', flexDirection: 'column', height: 'calc(80vh - 200px)', maxHeight: '600px', p: 1 }}>
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
                {msg.sender === 'ai' ? (
                  <ReactMarkdown components={markdownComponents}>
                    {msg.text}
                  </ReactMarkdown>
                ) : (
                  <ListItemText
                    primary={msg.text}
                    sx={{ margin: 0 }}
                  />
                )}
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
          <div ref={messagesEndRef} /> 
        </List>
      </Box>

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 1 }}>
          <CircularProgress size={24} />
        </Box>
      )}

      {showPurchasePrompt && (
        <Alert 
          severity="warning" 
          sx={{ mt: 1, mx: 1, display: 'flex', alignItems: 'center' }} 
          action={
            <Button 
              color="primary" 
              size="small" 
              onClick={handlePurchaseAllowance} 
              disabled={isPurchasing}
              startIcon={isPurchasing ? <CircularProgress size={16} color="inherit" /> : <ShoppingCartIcon />}
            >
              {isPurchasing ? 'Purchasing...' : 'Purchase More (10 Credits)'} 
            </Button>
          }
        >
          {error || "You've reached your daily free message limit."}
        </Alert>
      )}

      {error && !showPurchasePrompt && (
        <Alert severity="error" sx={{ mt: 1, mx: 1 }}>
          {error}
        </Alert>
      )}

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
          disabled={isLoading || isPurchasing || showPurchasePrompt}
          multiline
          maxRows={4}
          sx={{ mr: 1 }}
        />
        <IconButton 
          color="primary" 
          onClick={handleSendMessage} 
          disabled={!inputValue.trim() || isLoading || isPurchasing || showPurchasePrompt}
        >
          <SendIcon />
        </IconButton>
      </Box>
      
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SubmoduleChat; 
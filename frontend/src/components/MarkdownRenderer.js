import React, { useMemo } from 'react';
import { Box, useTheme } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import { sanitizeContent } from '../utils/sanitizer';

/**
 * StyledMarkdown component for rendering markdown content with proper styling
 * and syntax highlighting for code blocks using the application theme.
 */
const MarkdownRenderer = ({ children }) => {
  const theme = useTheme();

  // Process the content to handle "```markdown\n" at the beginning
  // and sanitize the content to prevent XSS attacks
  const processedContent = useMemo(() => {
    if (!children) return '';
    
    // Check if content starts with ```markdown\n and remove it if it does
    // This pattern specifically targets only the beginning of the content
    const content = String(children);
    let processed = content;
    
    if (processed.startsWith('```markdown\n')) {
      processed = processed.replace(/^```markdown\n/, '');
    }
    
    // Sanitize the content with our custom sanitizer
    return sanitizeContent(processed);
  }, [children]);

  return (
    <Box 
      data-tut="markdown-content"
      sx={{
      color: theme.palette.text.primary,
      fontSize: theme.typography.body1.fontSize,
      lineHeight: theme.typography.body1.lineHeight,
      wordWrap: 'break-word',

      '& h1, & h2, & h3, & h4, & h5, & h6': {
        mt: theme.spacing(4),
        mb: theme.spacing(2),
        fontWeight: theme.typography.fontWeightBold,
        lineHeight: 1.3,
        color: theme.palette.text.primary,
        paddingBottom: theme.spacing(1),
        borderBottom: `1px solid ${theme.palette.divider}`,
      },
      '& h1': { fontSize: theme.typography.h2.fontSize },
      '& h2': { fontSize: theme.typography.h3.fontSize },
      '& h3': { 
        fontSize: theme.typography.h4.fontSize, 
        borderBottom: 'none',
        pb: 0,
        mt: theme.spacing(3),
        mb: theme.spacing(1.5),
        fontWeight: theme.typography.fontWeightMedium,
      },
      '& h4': { 
        fontSize: theme.typography.h5.fontSize, 
        borderBottom: 'none', 
        pb: 0, 
        mt: theme.spacing(3),
        mb: theme.spacing(1.5),
        fontWeight: theme.typography.fontWeightMedium,
      },
      '& h5': { 
        fontSize: theme.typography.h6.fontSize, 
        borderBottom: 'none', 
        pb: 0, 
        mt: theme.spacing(3),
        mb: theme.spacing(1.5),
        fontWeight: theme.typography.fontWeightMedium,
      },
      '& h6': { 
        fontSize: theme.typography.subtitle1.fontSize, 
        borderBottom: 'none', 
        pb: 0, 
        mt: theme.spacing(3),
        mb: theme.spacing(1.5),
        color: theme.palette.text.secondary,
        fontWeight: theme.typography.fontWeightMedium,
      },
      '& p': { 
        my: theme.spacing(1.5),
        lineHeight: theme.typography.body1.lineHeight,
      },
      '& ul, & ol': { 
        pl: theme.spacing(4),
        my: theme.spacing(1.5),
        '& ul, & ol': { 
           my: theme.spacing(1),
        }
      },
      '& li': { 
        mb: theme.spacing(1),
        pl: theme.spacing(0.5),
        lineHeight: theme.typography.body1.lineHeight,
        '&::marker': {
           color: theme.palette.text.secondary,
        }
      },
      '& blockquote': { 
        borderLeft: `4px solid ${theme.palette.primary.light}`,
        pl: theme.spacing(2),
        pr: theme.spacing(2),
        py: theme.spacing(1),
        my: theme.spacing(2.5),
        fontStyle: 'normal',
        color: theme.palette.text.secondary,
        backgroundColor: theme.palette.action.hover,
        borderRadius: theme.shape.borderRadius / 2,
        '& p': { 
          my: theme.spacing(1),
        }
      },
      '& code': {
        fontFamily: '\'SFMono-Regular\', Consolas, \'Liberation Mono\', Menlo, Courier, monospace',
        backgroundColor: theme.palette.action.hover,
        color: theme.palette.text.primary,
        padding: '0.2em 0.4em',
        borderRadius: theme.shape.borderRadius / 2,
        fontSize: '0.9em',
        wordBreak: 'break-word',
      },
      '& pre': {
        padding: theme.spacing(2),
        borderRadius: theme.shape.borderRadius,
        overflowX: 'auto',
        my: theme.spacing(2.5),
        border: `1px solid ${theme.palette.divider}`,
        backgroundColor: theme.palette.mode === 'dark' ? theme.palette.grey[900] : '#f8f9fa',
        '& code': {
          fontFamily: 'inherit',
          backgroundColor: 'transparent',
          color: 'inherit',
          padding: 0,
          borderRadius: 0,
          fontSize: '0.875em',
          lineHeight: 1.5,
        }
      },
      '& a': {
        color: theme.palette.primary.main,
        textDecoration: 'none',
        fontWeight: theme.typography.fontWeightMedium,
        '&:hover': {
          textDecoration: 'underline',
          color: theme.palette.primary.dark,
        }
      },
      '& img': {
        maxWidth: '100%',
        height: 'auto',
        borderRadius: theme.shape.borderRadius,
        display: 'block',
        my: theme.spacing(2.5),
        border: `1px solid ${theme.palette.divider}`,
      },
      '& table': {
        borderCollapse: 'separate',
        borderSpacing: 0,
        width: '100%',
        my: theme.spacing(2.5),
        borderRadius: theme.shape.borderRadius,
        border: `1px solid ${theme.palette.divider}`,
        overflow: 'hidden',
      },
      '& th, & td': {
        padding: theme.spacing(1.5),
        textAlign: 'left',
        borderBottom: `1px solid ${theme.palette.divider}`,
        lineHeight: 1.5,
      },
      '& th': {
        backgroundColor: theme.palette.background.default,
        fontWeight: theme.typography.fontWeightBold,
        color: theme.palette.text.primary,
      },
      '& td': {
         color: theme.palette.text.primary,
      },
      '& tr:last-child th, & tr:last-child td': {
        borderBottom: 'none',
      },
      '& tr:nth-of-type(even)': {
      },
      '& hr': {
        my: theme.spacing(4),
        border: 'none',
        height: '1px',
        backgroundColor: theme.palette.divider,
      },
      '& input[type="checkbox"]': {
        mr: theme.spacing(1),
        transform: 'translateY(2px)',
      }
    }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[]}
        disallowedElements={['script', 'style', 'iframe']}
        skipHtml={true}
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            return !inline && match ? (
              <SyntaxHighlighter
                style={oneLight}
                language={match[1]}
                PreTag="div"
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className={className} {...props}>
                {children}
              </code>
            );
          }
        }}
      >
        {processedContent}
      </ReactMarkdown>
    </Box>
  );
};

export default MarkdownRenderer;
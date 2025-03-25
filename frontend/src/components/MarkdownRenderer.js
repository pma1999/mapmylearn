import React, { useMemo } from 'react';
import { Box } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import { sanitizeContent } from '../utils/sanitizer';

/**
 * StyledMarkdown component for rendering markdown content with proper styling
 * and syntax highlighting for code blocks
 */
const MarkdownRenderer = ({ children }) => {
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
    <Box sx={{
      '& h1': { 
        fontSize: '1.8rem',
        fontWeight: 'bold',
        my: 2,
        borderBottom: '1px solid',
        borderColor: 'grey.300',
        pb: 1
      },
      '& h2': { 
        fontSize: '1.5rem',
        fontWeight: 'bold',
        my: 1.8,
        borderBottom: '1px solid',
        borderColor: 'grey.200',
        pb: 0.5
      },
      '& h3': { 
        fontSize: '1.3rem',
        fontWeight: 'bold',
        my: 1.5 
      },
      '& p': { 
        my: 1,
        lineHeight: 1.6
      },
      '& ul, & ol': { 
        pl: 4,
        my: 1.5
      },
      '& li': { 
        mb: 0.8,
        pl: 0.5
      },
      '& blockquote': { 
        borderLeft: '4px solid',
        borderColor: 'grey.400',
        pl: 2,
        py: 0.5,
        my: 1.5,
        fontStyle: 'italic',
        bgcolor: 'grey.100',
        borderRadius: 1
      },
      '& code': {
        fontFamily: 'monospace',
        bgcolor: 'grey.100',
        p: 0.5,
        borderRadius: 0.5,
        fontSize: '0.9em'
      },
      '& pre': {
        bgcolor: 'grey.900',
        color: 'common.white',
        p: 2,
        borderRadius: 1,
        overflowX: 'auto',
        my: 2,
        '& code': {
          bgcolor: 'transparent',
          color: 'inherit',
          p: 0
        }
      },
      '& a': {
        color: 'primary.main',
        textDecoration: 'none',
        '&:hover': {
          textDecoration: 'underline'
        }
      },
      '& img': {
        maxWidth: '100%',
        height: 'auto',
        borderRadius: 1,
        display: 'block',
        my: 2
      },
      '& table': {
        borderCollapse: 'collapse',
        width: '100%',
        my: 2,
        borderRadius: 1,
        overflow: 'hidden',
        boxShadow: '0 0 0 1px rgba(0,0,0,0.1)'
      },
      '& th': {
        bgcolor: 'grey.100',
        fontWeight: 'bold',
        p: 1.5,
        textAlign: 'left',
        borderBottom: '2px solid',
        borderColor: 'grey.300'
      },
      '& td': {
        p: 1.5,
        borderBottom: '1px solid',
        borderColor: 'grey.200'
      },
      '& tr:last-child td': {
        borderBottom: 'none'
      },
      '& tr:nth-of-type(even)': {
        bgcolor: 'grey.50'
      },
      '& hr': {
        my: 3,
        border: 'none',
        height: '1px',
        bgcolor: 'grey.300'
      },
      '& input[type="checkbox"]': {
        mr: 1
      }
    }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        // Disable raw HTML in markdown
        rehypePlugins={[]}
        disallowedElements={['script', 'style', 'iframe']}
        skipHtml={true}
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            return !inline && match ? (
              <SyntaxHighlighter
                style={vscDarkPlus}
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
/**
 * Mock `react-markdown` to avoid importing the ESM distribution during tests.
 * This lightweight mock converts a few markdown patterns to HTML so our
 * component tests can assert on rendered tags without pulling the full library.
 */
jest.mock('remark-gfm', () => () => {}); // mock remark-gfm so tests don't import ESM modules

jest.mock('react-markdown', () => {
  const React = require('react');
  return ({ children }) => {
    const raw = String(children || '');
    const html = raw
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>')
      .replace(/^# (.*)$/gm, '<h1>$1</h1>');
    return React.createElement('div', { dangerouslySetInnerHTML: { __html: html } });
  };
});

import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import MarkdownInline from '../MarkdownInline';

describe('MarkdownInline', () => {
  it('renders emphasis and links and does not generate header ids', () => {
    const markdown = `This is *italic* and [link](https://example.com)

# Heading`;

    const { container, asFragment } = render(
      <MarkdownInline variant="body1">{markdown}</MarkdownInline>
    );

    // Emphasis should be rendered (em tag)
    const em = container.querySelector('em');
    expect(em).toBeTruthy();
    expect(em).toHaveTextContent('italic');

    // Link should be rendered with correct href
    const a = container.querySelector('a');
    expect(a).toBeTruthy();
    expect(a).toHaveAttribute('href', 'https://example.com');

    // Heading should render but NOT have an id when used via MarkdownInline (enableTocIds=false)
    const h1 = container.querySelector('h1');
    if (h1) {
      expect(h1).not.toHaveAttribute('id');
    }

    // Snapshot (will be written on first run)
    expect(asFragment()).toMatchSnapshot();
  });

  it('returns null for empty children', () => {
    const { container } = render(<MarkdownInline variant="body1">{''}</MarkdownInline>);
    // Expect no meaningful DOM nodes for empty content (only the Typography wrapper may exist)
    expect(container.textContent).toBe('');
  });
});

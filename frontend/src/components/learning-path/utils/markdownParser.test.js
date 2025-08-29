import { stripMarkdownFormatting, parseMarkdownHeaders, generateHeaderId } from './markdownParser';

describe('stripMarkdownFormatting', () => {
  test('should remove bold formatting (**text**)', () => {
    expect(stripMarkdownFormatting('**Bold Text**')).toBe('Bold Text');
  });

  test('should remove bold formatting (__text__)', () => {
    expect(stripMarkdownFormatting('__Bold Text__')).toBe('Bold Text');
  });

  test('should remove italic formatting (*text*)', () => {
    expect(stripMarkdownFormatting('*Italic Text*')).toBe('Italic Text');
  });

  test('should remove italic formatting (_text_)', () => {
    expect(stripMarkdownFormatting('_Italic Text_')).toBe('Italic Text');
  });

  test('should remove strikethrough formatting (~~text~~)', () => {
    expect(stripMarkdownFormatting('~~Strikethrough Text~~')).toBe('Strikethrough Text');
  });

  test('should remove inline code formatting (`text`)', () => {
    expect(stripMarkdownFormatting('Header with `code` example')).toBe('Header with code example');
  });

  test('should handle mixed formatting', () => {
    expect(stripMarkdownFormatting('**Bold** and *italic* text')).toBe('Bold and italic text');
  });

  test('should handle complex nested formatting', () => {
    expect(stripMarkdownFormatting('**Bold** with _italic_ and `code` plus ~~strike~~')).toBe('Bold with italic and code plus strike');
  });

  test('should handle empty string', () => {
    expect(stripMarkdownFormatting('')).toBe('');
  });

  test('should handle null/undefined', () => {
    expect(stripMarkdownFormatting(null)).toBe('');
    expect(stripMarkdownFormatting(undefined)).toBe('');
  });

  test('should handle plain text without formatting', () => {
    expect(stripMarkdownFormatting('Plain text header')).toBe('Plain text header');
  });

  test('should handle multiple consecutive formatting markers', () => {
    expect(stripMarkdownFormatting('**Bold** **More Bold**')).toBe('Bold More Bold');
  });

  test('should handle partial formatting (unclosed markers)', () => {
    expect(stripMarkdownFormatting('**Incomplete bold text')).toBe('Incomplete bold text');
  });
});

describe('parseMarkdownHeaders with formatting', () => {
  test('should parse headers with bold formatting', () => {
    const markdown = '# **Bold Header**\n\nSome content\n\n## *Italic Header*';
    const headers = parseMarkdownHeaders(markdown);
    
    expect(headers).toHaveLength(2);
    expect(headers[0].title).toBe('Bold Header');
    expect(headers[0].level).toBe(1);
    expect(headers[1].title).toBe('Italic Header');
    expect(headers[1].level).toBe(2);
  });

  test('should parse headers with mixed formatting', () => {
    const markdown = '### **Bold** and *italic* text\n\nContent here';
    const headers = parseMarkdownHeaders(markdown);
    
    expect(headers).toHaveLength(1);
    expect(headers[0].title).toBe('Bold and italic text');
    expect(headers[0].level).toBe(3);
  });

  test('should parse headers with inline code', () => {
    const markdown = '#### Header with `code` example';
    const headers = parseMarkdownHeaders(markdown);
    
    expect(headers).toHaveLength(1);
    expect(headers[0].title).toBe('Header with code example');
    expect(headers[0].level).toBe(4);
  });

  test('should parse headers with strikethrough', () => {
    const markdown = '##### ~~Strikethrough~~ text';
    const headers = parseMarkdownHeaders(markdown);
    
    expect(headers).toHaveLength(1);
    expect(headers[0].title).toBe('Strikethrough text');
    expect(headers[0].level).toBe(5);
  });

  test('should generate consistent IDs for formatted headers', () => {
    const markdown = '# **Bold Header**\n\n## Bold Header';
    const headers = parseMarkdownHeaders(markdown);
    
    expect(headers).toHaveLength(2);
    expect(headers[0].id).toBe('bold-header');
    expect(headers[1].id).toBe('bold-header-1'); // Should get unique ID
  });

  test('should preserve originalText for reference', () => {
    const markdown = '# **Bold Header**';
    const headers = parseMarkdownHeaders(markdown);
    
    expect(headers[0].originalText).toBe('# **Bold Header**');
    expect(headers[0].title).toBe('Bold Header');
  });

  test('should handle complex formatting combinations', () => {
    const markdown = '###### Complex **Bold** _Italic_ `Code` ~~Strike~~ Header';
    const headers = parseMarkdownHeaders(markdown);
    
    expect(headers).toHaveLength(1);
    expect(headers[0].title).toBe('Complex Bold Italic Code Strike Header');
    expect(headers[0].level).toBe(6);
    expect(headers[0].id).toBe('complex-bold-italic-code-strike-header');
  });

  test('should skip headers that become empty after stripping', () => {
    const markdown = '# **\n\n## Valid Header';
    const headers = parseMarkdownHeaders(markdown);
    
    expect(headers).toHaveLength(1);
    expect(headers[0].title).toBe('Valid Header');
  });

  test('should maintain header order and positions', () => {
    const markdown = '# First **Bold**\n\n## Second *Italic*\n\n### Third `Code`';
    const headers = parseMarkdownHeaders(markdown);
    
    expect(headers).toHaveLength(3);
    expect(headers[0].title).toBe('First Bold');
    expect(headers[0].position).toBe(0);
    expect(headers[1].title).toBe('Second Italic');
    expect(headers[2].title).toBe('Third Code');
    expect(headers[1].position).toBeGreaterThan(headers[0].position);
    expect(headers[2].position).toBeGreaterThan(headers[1].position);
  });
});

describe('Integration with existing functionality', () => {
  test('should work with regular headers without formatting', () => {
    const markdown = '# Regular Header\n\n## Another Regular Header';
    const headers = parseMarkdownHeaders(markdown);
    
    expect(headers).toHaveLength(2);
    expect(headers[0].title).toBe('Regular Header');
    expect(headers[1].title).toBe('Another Regular Header');
  });

  test('should generate proper IDs that match HTML rendering expectations', () => {
    const markdown = '# API **Endpoints** and _Methods_';
    const headers = parseMarkdownHeaders(markdown);
    
    expect(headers[0].id).toBe('api-endpoints-and-methods');
    expect(headers[0].title).toBe('API Endpoints and Methods');
  });

  test('should handle real-world documentation scenarios', () => {
    const realWorldMarkdown = `
# **Introduction to React**

## *Getting Started*

### **Installation** Guide

#### Using \`npm install\`

##### ~~Deprecated~~ Methods

###### Advanced **Configuration** Options
    `;
    
    const headers = parseMarkdownHeaders(realWorldMarkdown);
    
    expect(headers).toHaveLength(6);
    expect(headers[0].title).toBe('Introduction to React');
    expect(headers[1].title).toBe('Getting Started');
    expect(headers[2].title).toBe('Installation Guide');
    expect(headers[3].title).toBe('Using npm install');
    expect(headers[4].title).toBe('Deprecated Methods');
    expect(headers[5].title).toBe('Advanced Configuration Options');
  });
});

describe('Unicode character handling', () => {
  test('should handle the specific problematic header correctly', () => {
    const text = '# La Interdependencia: La *Virtù* se Muestra de Manera Efectiva Solo en Medio de la *Fortuna*';
    const headers = parseMarkdownHeaders(text);
    
    expect(headers).toHaveLength(1);
    expect(headers[0].title).toBe('La Interdependencia: La Virtù se Muestra de Manera Efectiva Solo en Medio de la Fortuna');
    expect(headers[0].id).toBe('la-interdependencia-la-virtu-se-muestra-de-manera-efectiva-solo-en-medio-de-la-fortuna');
  });

  test('should handle accented characters properly', () => {
    const text = '# La Interdependencia: La *Virtù* se Muestra';
    const headers = parseMarkdownHeaders(text);
    
    expect(headers).toHaveLength(1);
    expect(headers[0].title).toBe('La Interdependencia: La Virtù se Muestra');
    expect(headers[0].id).toBe('la-interdependencia-la-virtu-se-muestra');
  });

  test('should handle Spanish characters', () => {
    const text = '## Diseño y **Configuración** del Sistema';
    const headers = parseMarkdownHeaders(text);
    
    expect(headers).toHaveLength(1);
    expect(headers[0].title).toBe('Diseño y Configuración del Sistema');
    expect(headers[0].id).toBe('diseno-y-configuracion-del-sistema');
  });

  test('should handle French characters', () => {
    const text = '### Les *Éléments* de la **Création**';
    const headers = parseMarkdownHeaders(text);
    
    expect(headers).toHaveLength(1);
    expect(headers[0].title).toBe('Les Éléments de la Création');
    expect(headers[0].id).toBe('les-elements-de-la-creation');
  });

  test('should handle German characters', () => {
    const text = '#### Das **Überblick** der *Lösungen*';
    const headers = parseMarkdownHeaders(text);
    
    expect(headers).toHaveLength(1);
    expect(headers[0].title).toBe('Das Überblick der Lösungen');
    expect(headers[0].id).toBe('das-uberblick-der-losungen');
  });

  test('should handle mixed Unicode and ASCII', () => {
    const text = '##### Café **Münchën** and ~~American~~ Style';
    const headers = parseMarkdownHeaders(text);
    
    expect(headers).toHaveLength(1);
    expect(headers[0].title).toBe('Café Münchën and American Style');
    expect(headers[0].id).toBe('cafe-munchen-and-american-style');
  });

  test('should handle emoji and special Unicode (removed but gracefully)', () => {
    const text = '# Testing 📚 **Bold** with 💻 *Italic*';
    const headers = parseMarkdownHeaders(text);
    
    expect(headers).toHaveLength(1);
    expect(headers[0].title).toBe('Testing 📚 Bold with 💻 Italic');
    expect(headers[0].id).toBe('testing-bold-with-italic');
  });
});

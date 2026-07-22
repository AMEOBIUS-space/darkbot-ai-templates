# Markdown to HTML Converter

> Tables, code blocks, TOC, footnotes, images, and all standard Markdown

## Features

- Headings (h1-h6) with auto-generated slugs
- Bold, italic, strikethrough, inline code
- Fenced code blocks with language class
- Tables with headers
- Links and images
- Ordered and unordered lists
- Blockquotes
- Horizontal rules
- Footnotes ([^id] refs + definitions)
- Table of contents generation (configurable max level)

## Quick Start

```python
from converter import MarkdownConverter

conv = MarkdownConverter()
html = conv.convert("# Title\n\n**bold** and *italic*\n\n| Col1 | Col2 |\n|------|------|\n| a | b |")
toc = conv.generate_toc(max_level=3)
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)

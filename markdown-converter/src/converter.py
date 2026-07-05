"""Markdown to HTML Converter — tables, code blocks, TOC, footnotes, images."""
import re
import html
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class Heading:
    level: int
    text: str
    slug: str


class MarkdownConverter:
    """Convert Markdown to HTML with extensions."""

    def __init__(self):
        self.headings: List[Heading] = []
        self.footnotes: Dict[str, str] = {}
        self._footnote_refs: List[str] = []

    def convert(self, markdown: str) -> str:
        """Convert markdown to HTML."""
        self.headings = []
        self.footnotes = {}
        self._footnote_refs = []

        lines = markdown.split("\n")
        html_lines = []
        in_code_block = False
        code_lang = ""
        in_table = False
        table_header = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Code blocks (fenced)
            if line.strip().startswith("```"):
                if in_code_block:
                    html_lines.append("</code></pre>")
                    in_code_block = False
                    code_lang = ""
                else:
                    code_lang = line.strip()[3:].strip()
                    cls = f' class="language-{code_lang}"' if code_lang else ""
                    html_lines.append(f'<pre><code{cls}>')
                    in_code_block = True
                i += 1
                continue

            if in_code_block:
                html_lines.append(html.escape(line))
                i += 1
                continue

            # Tables
            if "|" in line and not in_table and i + 1 < len(lines) and re.match(r"^\s*\|[\s\-:|]+\|\s*$", lines[i + 1]):
                in_table = True
                table_header = [c.strip() for c in line.strip().strip("|").split("|")]
                html_lines.append("<table>")
                html_lines.append("<thead><tr>")
                for h in table_header:
                    html_lines.append(f"<th>{self._inline(h)}</th>")
                html_lines.append("</tr></thead><tbody>")
                i += 2  # Skip header + separator
                continue

            if in_table:
                if "|" not in line or not line.strip():
                    html_lines.append("</tbody></table>")
                    in_table = False
                    # Don't increment, reprocess line
                    continue
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                html_lines.append("<tr>")
                for c in cells:
                    html_lines.append(f"<td>{self._inline(c)}</td>")
                html_lines.append("</tr>")
                i += 1
                continue

            if in_table:
                html_lines.append("</tbody></table>")
                in_table = False

            # Headings
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                slug = self._slugify(text)
                self.headings.append(Heading(level=level, text=text, slug=slug))
                html_lines.append(f'<h{level} id="{slug}">{self._inline(text)}</h{level}>')
                i += 1
                continue

            # Blockquotes
            if line.strip().startswith(">"):
                quote_text = line.strip()[1:].strip()
                html_lines.append(f"<blockquote>{self._inline(quote_text)}</blockquote>")
                i += 1
                continue

            # Horizontal rule
            if re.match(r"^(-{3,}|\*{3,}|_{3,})$", line.strip()):
                html_lines.append("<hr/>")
                i += 1
                continue

            # Unordered lists
            if re.match(r"^\s*[-*+]\s+", line):
                list_items = []
                while i < len(lines) and re.match(r"^\s*[-*+]\s+", lines[i]):
                    item_text = re.sub(r"^\s*[-*+]\s+", "", lines[i])
                    list_items.append(f"<li>{self._inline(item_text)}</li>")
                    i += 1
                html_lines.append("<ul>" + "".join(list_items) + "</ul>")
                continue

            # Ordered lists
            if re.match(r"^\s*\d+\.\s+", line):
                list_items = []
                while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                    item_text = re.sub(r"^\s*\d+\.\s+", "", lines[i])
                    list_items.append(f"<li>{self._inline(item_text)}</li>")
                    i += 1
                html_lines.append("<ol>" + "".join(list_items) + "</ol>")
                continue

            # Empty lines
            if not line.strip():
                html_lines.append("")
                i += 1
                continue

            # Regular paragraph
            html_lines.append(f"<p>{self._inline(line)}</p>")
            i += 1

        if in_table:
            html_lines.append("</tbody></table>")

        # Add footnotes
        if self._footnote_refs:
            html_lines.append('<div class="footnotes"><hr/><ol>')
            for ref in self._footnote_refs:
                fn = self.footnotes.get(ref, "")
                html_lines.append(f'<li id="fn:{ref}">{self._inline(fn)} '
                                  f'<a href="#fnref:{ref}" title="return">&#8617;</a></li>')
            html_lines.append("</ol></div>")

        return "\n".join(html_lines)

    def _inline(self, text: str) -> str:
        """Process inline elements."""
        # Footnotes [^id]
        text = re.sub(r"\[\^([^\]]+)\]", lambda m: self._footnote_ref(m.group(1)), text)

        # Images ![alt](src)
        text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
                      lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}"/>', text)

        # Links [text](url)
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                      lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)

        # Bold
        text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)

        # Italic
        text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
        text = re.sub(r"_([^_]+)_", r"<em>\1</em>", text)

        # Inline code
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

        # Strikethrough
        text = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", text)

        return text

    def _footnote_ref(self, ref_id: str) -> str:
        if ref_id not in self._footnote_refs:
            self._footnote_refs.append(ref_id)
        return f'<sup><a href="#fn:{ref_id}" id="fnref:{ref_id}">[{len(self._footnote_refs)}]</a></sup>'

    @staticmethod
    def _slugify(text: str) -> str:
        slug = re.sub(r"[^\w\s-]", "", text.lower())
        slug = re.sub(r"[\s]+", "-", slug.strip())
        return slug

    def generate_toc(self, max_level: int = 3) -> str:
        """Generate table of contents from headings."""
        if not self.headings:
            return ""
        lines = ['<div class="toc"><ul>']
        for h in self.headings:
            if h.level <= max_level:
                indent = "  " * (h.level - 1)
                lines.append(f'{indent}<li><a href="#{h.slug}">{html.escape(h.text)}</a></li>')
        lines.append("</ul></div>")
        return "\n".join(lines)

    def parse_footnotes(self, markdown: str) -> str:
        """Extract footnote definitions from markdown."""
        def extract(m):
            ref_id = m.group(1)
            content = m.group(2).strip()
            self.footnotes[ref_id] = content
            return ""
        return re.sub(r"^\[\^([^\]]+)\]:\s*(.+)$", extract, markdown, flags=re.MULTILINE)

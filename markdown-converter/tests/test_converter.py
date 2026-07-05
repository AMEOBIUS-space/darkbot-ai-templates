import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from converter import MarkdownConverter


def test_heading():
    c = MarkdownConverter()
    html_out = c.convert("# Hello World")
    assert "<h1" in html_out
    assert "Hello World" in html_out
    assert 'id="hello-world"' in html_out

def test_heading_levels():
    c = MarkdownConverter()
    html_out = c.convert("### Subheading")
    assert "<h3" in html_out

def test_bold():
    c = MarkdownConverter()
    html_out = c.convert("**bold text**")
    assert "<strong>bold text</strong>" in html_out

def test_italic():
    c = MarkdownConverter()
    html_out = c.convert("*italic text*")
    assert "<em>italic text</em>" in html_out

def test_inline_code():
    c = MarkdownConverter()
    html_out = c.convert("Use `code` here")
    assert "<code>code</code>" in html_out

def test_code_block():
    c = MarkdownConverter()
    html_out = c.convert("```python\nprint('hello')\n```")
    assert "<pre><code" in html_out
    assert 'language-python' in html_out
    assert "print" in html_out

def test_link():
    c = MarkdownConverter()
    html_out = c.convert("[Google](https://google.com)")
    assert '<a href="https://google.com">Google</a>' in html_out

def test_image():
    c = MarkdownConverter()
    html_out = c.convert("![Alt text](https://img.com/test.png)")
    assert '<img src="https://img.com/test.png"' in html_out
    assert 'alt="Alt text"' in html_out

def test_unordered_list():
    c = MarkdownConverter()
    html_out = c.convert("- item 1\n- item 2\n- item 3")
    assert "<ul>" in html_out
    assert "<li>item 1</li>" in html_out
    assert "</ul>" in html_out

def test_ordered_list():
    c = MarkdownConverter()
    html_out = c.convert("1. first\n2. second")
    assert "<ol>" in html_out
    assert "<li>first</li>" in html_out

def test_blockquote():
    c = MarkdownConverter()
    html_out = c.convert("> This is a quote")
    assert "<blockquote>" in html_out

def test_horizontal_rule():
    c = MarkdownConverter()
    html_out = c.convert("---")
    assert "<hr/>" in html_out

def test_table():
    c = MarkdownConverter()
    md = "| Name | Age |\n|------|-----|\n| Alice | 30 |\n| Bob | 25 |"
    html_out = c.convert(md)
    assert "<table>" in html_out
    assert "<th>Name</th>" in html_out
    assert "<td>Alice</td>" in html_out

def test_strikethrough():
    c = MarkdownConverter()
    html_out = c.convert("~~deleted~~")
    assert "<del>deleted</del>" in html_out

def test_toc():
    c = MarkdownConverter()
    c.convert("# Title 1\n## Subtitle\n### Deep\n# Title 2")
    toc = c.generate_toc(max_level=2)
    assert "Title 1" in toc
    assert "Subtitle" in toc
    assert "Deep" not in toc  # max_level=2

def test_toc_empty():
    c = MarkdownConverter()
    assert c.generate_toc() == ""

def test_paragraph():
    c = MarkdownConverter()
    html_out = c.convert("Just a paragraph")
    assert "<p>Just a paragraph</p>" in html_out

def test_nested_formatting():
    c = MarkdownConverter()
    html_out = c.convert("**bold text** and *italic*")
    assert "<strong>bold text</strong>" in html_out
    assert "<em>italic</em>" in html_out

def test_slugify():
    assert MarkdownConverter._slugify("Hello World!") == "hello-world"
    assert MarkdownConverter._slugify("Test_Case 123") == "test_case-123"

def test_multiple_headings():
    c = MarkdownConverter()
    html_out = c.convert("# First\n## Second\n### Third")
    assert len(c.headings) == 3
    assert c.headings[0].level == 1
    assert c.headings[2].level == 3

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from engine import TemplateEngine, TemplateFilters


def test_variable():
    e = TemplateEngine()
    result = e.render("Hello {{ name }}!", {"name": "Alice"})
    assert result == "Hello Alice!"

def test_variable_nested():
    e = TemplateEngine()
    result = e.render("{{ user.name }} is {{ user.age }}", {"user": {"name": "Bob", "age": 30}})
    assert "Bob" in result
    assert "30" in result

def test_filter_upper():
    e = TemplateEngine()
    result = e.render("{{ name|upper }}", {"name": "alice"})
    assert result == "ALICE"

def test_filter_lower():
    e = TemplateEngine()
    result = e.render("{{ name|lower }}", {"name": "ALICE"})
    assert result == "alice"

def test_filter_truncate():
    e = TemplateEngine()
    result = e.render("{{ text|truncate:10 }}", {"text": "This is a long text"})
    assert "..." in result
    assert len(result) <= 13

def test_filter_default():
    e = TemplateEngine()
    result = e.render("{{ name|default:Anonymous }}", {"name": ""})
    assert "Anonymous" in result

def test_filter_escape():
    e = TemplateEngine()
    result = e.render("{{ text|escape }}", {"text": "<script>alert(1)</script>"})
    assert "<script>" not in result
    assert "&lt;script&gt;" in result

def test_conditional_true():
    e = TemplateEngine()
    result = e.render("{% if show %}Visible{% endif %}", {"show": True})
    assert "Visible" in result

def test_conditional_false():
    e = TemplateEngine()
    result = e.render("{% if show %}Visible{% endif %}", {"show": False})
    assert "Visible" not in result

def test_conditional_else():
    e = TemplateEngine()
    result = e.render("{% if show %}Yes{% else %}No{% endif %}", {"show": False})
    assert "No" in result

def test_conditional_equals():
    e = TemplateEngine()
    result = e.render("{% if status == 'active' %}Active{% endif %}", {"status": "active"})
    assert "Active" in result

def test_loop():
    e = TemplateEngine()
    result = e.render("{% for item in items %}{{ item }} {% endfor %}", {"items": ["a", "b", "c"]})
    assert "a" in result
    assert "b" in result
    assert "c" in result

def test_loop_with_index():
    e = TemplateEngine()
    result = e.render("{% for item in items %}{{ loop_index }}:{{ item }} {% endfor %}", {"items": ["x", "y"]})
    assert "0:x" in result
    assert "1:y" in result

def test_comments():
    e = TemplateEngine()
    result = e.render("Hello {# this is a comment #}World", {})
    assert "comment" not in result
    assert "HelloWorld" in result or "Hello World" in result

def test_register_and_render():
    e = TemplateEngine()
    e.register("greeting", "Hello {{ name }}!")
    result = e.render_template("greeting", {"name": "World"})
    assert result == "Hello World!"

def test_template_not_found():
    e = TemplateEngine()
    try:
        e.render_template("nonexistent", {})
        assert False
    except ValueError:
        pass

def test_include():
    e = TemplateEngine()
    e.register("header", "<header>Title</header>")
    result = e.render('{% include "header" %}Body', {})
    assert "<header>" in result
    assert "Body" in result

def test_add_custom_filter():
    e = TemplateEngine()
    e.add_filter("double", lambda x: str(x) * 2)
    result = e.render("{{ val|double }}", {"val": "ab"})
    assert result == "abab"

def test_multiple_filters():
    e = TemplateEngine()
    result = e.render("{{ name|trim|upper }}", {"name": "  alice  "})
    assert result == "ALICE"

def test_block():
    e = TemplateEngine()
    result = e.render("{% block content %}Default{% endblock %}", {})
    assert "Default" in result

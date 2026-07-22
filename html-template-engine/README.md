# HTML Template Engine

> Variables, conditionals, loops, filters, blocks, and includes

## Features

- {{ variable }} with dot-notation (user.name)
- 11 built-in filters (upper, lower, trim, escape, truncate, default, join, reverse, replace, capitalize, length)
- Custom filter registration
- Filter chaining ({{ name|trim|upper }})
- Conditionals ({% if %}, {% else %}, {% endif %})
- Equality checks ({% if status == 'active' %})
- Loops ({% for item in items %}) with loop_index, loop_first, loop_last
- Blocks ({% block name %}content{% endblock %})
- Includes ({% include "name" %})
- Comments ({# comment #})
- Named template registration

## Quick Start

```python
from engine import TemplateEngine

engine = TemplateEngine()
engine.register("page", """
<h1>{{ title }}</h1>
{% if user %}<p>Welcome {{ user.name|upper }}</p>{% endif %}
<ul>{% for item in items %}<li>{{ loop_index }}: {{ item }}</li>{% endfor %}</ul>
""")
html = engine.render_template("page", {"title": "My Page", "user": {"name": "alice"}, "items": ["a", "b"]})
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)

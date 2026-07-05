"""HTML Template Engine — variables, conditionals, loops, inheritance, and filters."""
import re
import html
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field


class TemplateFilters:
    """Built-in template filters."""

    @staticmethod
    def upper(s: str) -> str:
        return str(s).upper()

    @staticmethod
    def lower(s: str) -> str:
        return str(s).lower()

    @staticmethod
    def capitalize(s: str) -> str:
        return str(s).capitalize()

    @staticmethod
    def trim(s: str) -> str:
        return str(s).strip()

    @staticmethod
    def length(s) -> int:
        return len(s)

    @staticmethod
    def default(s, default_val: str = "") -> str:
        return s if s else default_val

    @staticmethod
    def escape(s: str) -> str:
        return html.escape(str(s))

    @staticmethod
    def truncate(s: str, length: int = 50, suffix: str = "...") -> str:
        s = str(s)
        return s[:length] + suffix if len(s) > length else s

    @staticmethod
    def join(items: list, separator: str = ", ") -> str:
        return separator.join(str(i) for i in items)

    @staticmethod
    def reverse(s) -> str:
        if isinstance(s, str):
            return s[::-1]
        return list(reversed(s))

    @staticmethod
    def replace(s: str, old: str, new: str) -> str:
        return str(s).replace(old, new)


class TemplateEngine:
    """Simple HTML template engine with Jinja2-like syntax."""

    FILTERS = {
        "upper": TemplateFilters.upper,
        "lower": TemplateFilters.lower,
        "capitalize": TemplateFilters.capitalize,
        "trim": TemplateFilters.trim,
        "length": TemplateFilters.length,
        "default": TemplateFilters.default,
        "escape": TemplateFilters.escape,
        "truncate": TemplateFilters.truncate,
        "join": TemplateFilters.join,
        "reverse": TemplateFilters.reverse,
        "replace": TemplateFilters.replace,
    }

    def __init__(self):
        self.templates: Dict[str, str] = {}
        self._blocks: Dict[str, str] = {}

    def register(self, name: str, template: str):
        """Register a named template."""
        self.templates[name] = template

    def add_filter(self, name: str, filter_func: Callable):
        """Add a custom filter."""
        self.FILTERS[name] = filter_func

    def render(self, template_str: str, context: Dict) -> str:
        """Render a template string with context."""
        result = template_str

        # Process conditionals {% if %}...{% endif %}
        result = self._process_conditionals(result, context)

        # Process loops {% for item in items %}...{% endfor %}
        result = self._process_loops(result, context)

        # Process variables {{ var }} and {{ var|filter }}
        result = self._process_variables(result, context)

        # Process block includes {% block name %}content{% endblock %}
        result = self._process_blocks(result, context)

        # Process includes {% include "name" %}
        result = self._process_includes(result, context)

        # Process comments {# comment #}
        result = re.sub(r"\{#.*?#\}", "", result, flags=re.DOTALL)

        return result

    def render_template(self, name: str, context: Dict) -> str:
        """Render a registered template by name."""
        template = self.templates.get(name)
        if not template:
            raise ValueError(f"Template '{name}' not found")
        return self.render(template, context)

    def _process_variables(self, template: str, context: Dict) -> str:
        """Process {{ variable }} and {{ variable|filter:arg }}."""
        def replace_var(match):
            expr = match.group(1).strip()
            parts = expr.split("|")
            value = self._resolve_value(parts[0].strip(), context)

            for filter_expr in parts[1:]:
                filter_expr = filter_expr.strip()
                if ":" in filter_expr:
                    fname, farg = filter_expr.split(":", 1)
                    fname = fname.strip()
                    farg = farg.strip().strip('"').strip("'")
                    if fname in self.FILTERS:
                        # Try to coerce numeric args
                        try:
                            coerced_arg = int(farg) if farg.lstrip('-').isdigit() else farg
                            value = self.FILTERS[fname](value, coerced_arg)
                        except TypeError:
                            value = self.FILTERS[fname](value)
                else:
                    if filter_expr in self.FILTERS:
                        value = self.FILTERS[filter_expr](value)
            return str(value) if value is not None else ""

        return re.sub(r"\{\{\s*(.+?)\s*\}\}", replace_var, template)

    def _resolve_value(self, expr: str, context: Dict) -> Any:
        """Resolve a dotted expression like 'user.name'."""
        parts = expr.split(".")
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, "")
            elif isinstance(value, list):
                try:
                    value = value[int(part)]
                except (ValueError, IndexError):
                    value = ""
            else:
                value = getattr(value, part, "")
        return value

    def _process_conditionals(self, template: str, context: Dict) -> str:
        """Process {% if %} and {% else %} blocks."""
        pattern = r"\{%\s*if\s+(.+?)\s*%\}(.*?)(?:\{%\s*else\s*%\}(.*?))?\{%\s*endif\s*%\}"
        def replace_conditional(match):
            condition = match.group(1).strip()
            true_block = match.group(2)
            else_block = match.group(3) or ""

            if self._eval_condition(condition, context):
                return true_block
            return else_block

        return re.sub(pattern, replace_conditional, template, flags=re.DOTALL)

    def _eval_condition(self, condition: str, context: Dict) -> bool:
        """Evaluate a simple condition."""
        # Handle "var == value"
        if "==" in condition:
            left, right = condition.split("==", 1)
            left_val = self._resolve_value(left.strip(), context)
            right_val = right.strip().strip('"').strip("'")
            return str(left_val) == right_val
        # Handle "var != value"
        if "!=" in condition:
            left, right = condition.split("!=", 1)
            left_val = self._resolve_value(left.strip(), context)
            right_val = right.strip().strip('"').strip("'")
            return str(left_val) != right_val
        # Handle truthy check
        value = self._resolve_value(condition, context)
        return bool(value)

    def _process_loops(self, template: str, context: Dict) -> str:
        """Process {% for item in items %} blocks."""
        pattern = r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}"
        def replace_loop(match):
            item_var = match.group(1)
            list_var = match.group(2)
            body = match.group(3)
            items = context.get(list_var, [])
            result = []
            for i, item in enumerate(items):
                loop_context = {**context, item_var: item, "loop_index": i, "loop_first": i == 0, "loop_last": i == len(items) - 1}
                result.append(self._process_variables(body, loop_context))
            return "".join(result)
        return re.sub(pattern, replace_loop, template, flags=re.DOTALL)

    def _process_blocks(self, template: str, context: Dict) -> str:
        """Process {% block name %}content{% endblock %}."""
        pattern = r"\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*%\}"
        def replace_block(match):
            block_name = match.group(1)
            block_content = match.group(2)
            if block_name in self._blocks:
                return self._blocks[block_name]
            self._blocks[block_name] = block_content
            return block_content
        return re.sub(pattern, replace_block, template, flags=re.DOTALL)

    def _process_includes(self, template: str, context: Dict) -> str:
        """Process {% include "name" %}."""
        def replace_include(match):
            include_name = match.group(1).strip().strip('"').strip("'")
            included = self.templates.get(include_name, "")
            return self.render(included, context)
        return re.sub(r"\{%\s*include\s+[\"']([^\"']+)[\"']\s*%\}", replace_include, template)

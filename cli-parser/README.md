# CLI Argument Parser

> Flags, subcommands, type coercion, choices, and help generation

## Features

- 6 types: string, integer, float, boolean, list, choice
- Short and long options (--port / -p)
- --flag=value and --flag value syntax
- Boolean flags (no value needed)
- Positional arguments
- Default values
- Required field validation
- Choice validation (enum)
- List type (comma-separated)
- Subcommands with their own arguments
- Help text generation
- Get method for easy access

## Quick Start

```python
from parser import CLIParser, ArgType

parser = CLIParser(prog="myapp", description="My CLI app")
parser.add_argument("--host", default="localhost", help="Server host")
parser.add_argument("--port", short="p", arg_type=ArgType.INTEGER, default=8080, help="Port")
parser.add_argument("--env", arg_type=ArgType.CHOICE, choices=["dev", "prod"], default="dev")
parser.add_argument("--verbose", flag=True, help="Verbose mode")

args = parser.parse(["--host", "0.0.0.0", "--port", "3000", "--verbose"])
print(args["host"], args["port"], args["verbose"])
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)

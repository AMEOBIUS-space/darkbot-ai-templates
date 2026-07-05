"""CLI Argument Parser — flags, subcommands, help generation, type coercion."""
import sys
import re
from typing import Dict, List, Optional, Callable, Any, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum


class ArgType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    CHOICE = "choice"


@dataclass
class Argument:
    name: str
    short: str = ""
    help: str = ""
    arg_type: ArgType = ArgType.STRING
    required: bool = False
    default: Any = None
    choices: List[str] = field(default_factory=list)
    flag: bool = False  # Boolean flag (no value needed)
    positional: bool = False
    nargs: str = ""  # "+", "*", "?", or number
    metavar: str = ""
    env: str = ""  # Environment variable fallback


@dataclass
class Subcommand:
    name: str
    help: str = ""
    arguments: List[Argument] = field(default_factory=list)
    handler: Optional[Callable] = None


class CLIParser:
    """CLI argument parser with subcommands, types, and help generation."""

    def __init__(self, prog: str = "", description: str = ""):
        self.prog = prog or sys.argv[0]
        self.description = description
        self.arguments: List[Argument] = []
        self.subcommands: Dict[str, Subcommand] = {}
        self._parsed: Dict[str, Any] = {}

    def add_argument(self, name: str, **kwargs) -> Argument:
        """Add an argument. Use --name for optional, just name for positional."""
        arg = Argument(name=name, **kwargs)
        if name.startswith("--"):
            arg.flag = kwargs.get("flag", False)
            if "short" in kwargs:
                arg.short = kwargs["short"]
        else:
            arg.positional = True
        self.arguments.append(arg)
        return arg

    def add_subcommand(self, cmd: Subcommand):
        """Add a subcommand."""
        self.subcommands[cmd.name] = cmd

    def parse(self, args: List[str] = None) -> Dict[str, Any]:
        """Parse command-line arguments."""
        args = args or sys.argv[1:]
        result = {}
        remaining = []
        i = 0

        # Check for subcommand
        if args and args[0] in self.subcommands:
            subcmd = self.subcommands[args[0]]
            result["_subcommand"] = args[0]
            sub_args, remaining = self._parse_args(args[1:], subcmd.arguments)
            # Clean sub-arg keys
            cleaned = {}
            for k, v in sub_args.items():
                cleaned[k.lstrip("-") if k.startswith("--") else k] = v
            result.update(cleaned)
            return result

        # Parse regular arguments
        parsed, remaining = self._parse_args(args, self.arguments)
        result.update(parsed)

        # Remaining positional args
        for j, arg in enumerate(self.arguments):
            if arg.positional and j < len(remaining):
                result[arg.name.lstrip("-")] = self._coerce(remaining[j], arg)

        # Apply defaults
        for arg in self.arguments:
            clean_name = arg.name.lstrip("-") if not arg.positional else arg.name
            if clean_name not in result or result[clean_name] is None:
                if arg.default is not None:
                    result[clean_name] = arg.default
                elif arg.required:
                    raise ValueError(f"Missing required argument: {arg.name}")

        self._parsed = result
        return result

    def _parse_args(self, args: List[str], arguments: List[Argument]) -> Tuple[Dict, List[str]]:
        """Parse a list of args against argument definitions."""
        result = {}
        remaining = []
        arg_map = {}
        for arg in arguments:
            if not arg.positional:
                clean_name = arg.name.lstrip("-")
                arg_map[f"--{clean_name}"] = arg
                if arg.short:
                    arg_map[f"-{arg.short}"] = arg

        i = 0
        while i < len(args):
            arg_str = args[i]

            if arg_str in arg_map:
                arg = arg_map[arg_str]
                if arg.flag:
                    result[arg.name.lstrip("-")] = True
                    i += 1
                else:
                    if i + 1 < len(args):
                        result[arg.name.lstrip("-")] = self._coerce(args[i + 1], arg)
                        i += 2
                    else:
                        raise ValueError(f"Argument {arg_str} requires a value")
            elif arg_str.startswith("--") and "=" in arg_str:
                key, val = arg_str.split("=", 1)
                arg = arg_map.get(key)
                if arg:
                    result[arg.name.lstrip("-")] = self._coerce(val, arg)
                    i += 1
                else:
                    remaining.append(arg_str)
                    i += 1
            elif not arg_str.startswith("-"):
                remaining.append(arg_str)
                i += 1
            else:
                i += 1  # Skip unknown flags

        return result, remaining

    @staticmethod
    def _coerce(value: str, arg: Argument) -> Any:
        """Coerce string value to the argument's type."""
        if arg.arg_type == ArgType.INTEGER:
            try:
                return int(value)
            except ValueError:
                raise ValueError(f"Invalid integer for {arg.name}: {value}")
        elif arg.arg_type == ArgType.FLOAT:
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"Invalid float for {arg.name}: {value}")
        elif arg.arg_type == ArgType.BOOLEAN:
            return value.lower() in ("true", "1", "yes", "on")
        elif arg.arg_type == ArgType.LIST:
            return value.split(",")
        elif arg.arg_type == ArgType.CHOICE:
            if value not in arg.choices:
                raise ValueError(f"Invalid choice for {arg.name}: {value}. Must be one of {arg.choices}")
            return value
        return value

    def format_help(self) -> str:
        """Generate help text."""
        lines = [f"Usage: {self.prog} [OPTIONS]", ""]
        if self.description:
            lines.append(self.description)
            lines.append("")

        if self.subcommands:
            lines.append("Subcommands:")
            for name, cmd in self.subcommands.items():
                lines.append(f"  {name:15s}  {cmd.help}")
            lines.append("")

        lines.append("Options:")
        for arg in self.arguments:
            if arg.positional:
                continue
            short = f"-{arg.short}, " if arg.short else "    "
            flag_str = "  " + short + f"--{arg.name}"
            if not arg.flag:
                metavar = arg.metavar or arg.name.upper()
                flag_str += f" {metavar}"
            if arg.help:
                flag_str += f"  {arg.help}"
            if arg.default is not None:
                flag_str += f" (default: {arg.default})"
            lines.append(flag_str)

        lines.append("  -h, --help      Show this help message")
        return "\n".join(lines)

    def get(self, name: str, default: Any = None) -> Any:
        """Get a parsed argument value."""
        return self._parsed.get(name, default)

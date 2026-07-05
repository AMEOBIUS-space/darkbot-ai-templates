import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from parser import CLIParser, Argument, Subcommand, ArgType


def test_string_arg():
    p = CLIParser(prog="test")
    p.add_argument("--name", arg_type=ArgType.STRING)
    result = p.parse(["--name", "Alice"])
    assert result["name"] == "Alice"

def test_integer_arg():
    p = CLIParser(prog="test")
    p.add_argument("--port", arg_type=ArgType.INTEGER)
    result = p.parse(["--port", "8080"])
    assert result["port"] == 8080
    assert isinstance(result["port"], int)

def test_float_arg():
    p = CLIParser(prog="test")
    p.add_argument("--rate", arg_type=ArgType.FLOAT)
    result = p.parse(["--rate", "0.5"])
    assert result["rate"] == 0.5

def test_boolean_flag():
    p = CLIParser(prog="test")
    p.add_argument("--verbose", flag=True)
    result = p.parse(["--verbose"])
    assert result["verbose"] is True

def test_boolean_flag_absent():
    p = CLIParser(prog="test")
    p.add_argument("--verbose", flag=True, default=False)
    result = p.parse([])
    assert result["verbose"] is False

def test_default_value():
    p = CLIParser(prog="test")
    p.add_argument("--host", default="localhost")
    result = p.parse([])
    assert result["host"] == "localhost"

def test_required_missing():
    p = CLIParser(prog="test")
    p.add_argument("--api-key", required=True)
    try:
        p.parse([])
        assert False
    except ValueError:
        pass

def test_choice_arg():
    p = CLIParser(prog="test")
    p.add_argument("--env", arg_type=ArgType.CHOICE, choices=["dev", "prod", "staging"])
    result = p.parse(["--env", "prod"])
    assert result["env"] == "prod"

def test_choice_invalid():
    p = CLIParser(prog="test")
    p.add_argument("--env", arg_type=ArgType.CHOICE, choices=["dev", "prod"])
    try:
        p.parse(["--env", "invalid"])
        assert False
    except ValueError:
        pass

def test_list_arg():
    p = CLIParser(prog="test")
    p.add_argument("--tags", arg_type=ArgType.LIST)
    result = p.parse(["--tags", "a,b,c"])
    assert result["tags"] == ["a", "b", "c"]

def test_short_option():
    p = CLIParser(prog="test")
    p.add_argument("--output", short="o")
    result = p.parse(["-o", "result.txt"])
    assert result["output"] == "result.txt"

def test_equals_syntax():
    p = CLIParser(prog="test")
    p.add_argument("--name")
    result = p.parse(["--name=Alice"])
    assert result["name"] == "Alice"

def test_positional_arg():
    p = CLIParser(prog="test")
    p.add_argument("file")
    result = p.parse(["input.txt"])
    assert result["file"] == "input.txt"

def test_subcommand():
    p = CLIParser(prog="git")
    sub = Subcommand(name="commit", help="Commit changes",
                     arguments=[Argument(name="--message", short="m")])
    p.add_subcommand(sub)
    result = p.parse(["commit", "--message", "Initial"])
    assert result["_subcommand"] == "commit"
    assert result["message"] == "Initial"

def test_multiple_args():
    p = CLIParser(prog="test")
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", arg_type=ArgType.INTEGER, default=8080)
    p.add_argument("--debug", flag=True, default=False)
    result = p.parse(["--host", "0.0.0.0", "--port", "3000", "--debug"])
    assert result["host"] == "0.0.0.0"
    assert result["port"] == 3000
    assert result["debug"] is True

def test_get_method():
    p = CLIParser(prog="test")
    p.add_argument("--name", default="default")
    p.parse(["--name", "test"])
    assert p.get("name") == "test"
    assert p.get("nonexistent", "fallback") == "fallback"

def test_format_help():
    p = CLIParser(prog="myapp", description="A test app")
    p.add_argument("--name", help="Your name")
    p.add_argument("--port", short="p", arg_type=ArgType.INTEGER, help="Port number", default=8080)
    p.add_argument("--verbose", flag=True, help="Enable verbose mode")
    help_text = p.format_help()
    assert "Usage" in help_text
    assert "--name" in help_text
    assert "--port" in help_text
    assert "--verbose" in help_text
    assert "A test app" in help_text

def test_subcommand_help():
    p = CLIParser(prog="git", description="Git CLI")
    sub = Subcommand(name="push", help="Push to remote")
    p.add_subcommand(sub)
    help_text = p.format_help()
    assert "push" in help_text
    assert "Push to remote" in help_text

def test_integer_invalid():
    p = CLIParser(prog="test")
    p.add_argument("--port", arg_type=ArgType.INTEGER)
    try:
        p.parse(["--port", "not_a_number"])
        assert False
    except ValueError:
        pass

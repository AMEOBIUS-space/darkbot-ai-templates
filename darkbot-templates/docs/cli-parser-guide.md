# CLI Parser: argparse Alternative for Simple Tools

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

`argparse` is powerful but verbose. For small CLIs — scripts, bots, tools — this template gives you flags, positional args, subcommands, and auto-generated help in a fluent API.

## Usage

```python
from darkbot_templates.templates.cli_parser import CLI

cli = CLI("mytool", "A freelance automation tool")

# Add a subcommand
serve = cli.command("serve", "Start the webhook server")
serve.flag("port", short="p", help="Port number", flag_type=int, default=8080)
serve.flag("host", short="h", help="Bind address", default="0.0.0.0")
serve.flag("debug", short="d", help="Debug mode", action="store_true")

@serve.handler
def serve_handler(args):
    print(f"Starting on {args.host}:{args.port} (debug={args.debug})")

# Run
cli.run()
```

```bash
$ mytool serve --port 9000 --debug
Starting on 0.0.0.0:9000 (debug=True)

$ mytool serve --help
Usage: mytool serve [options]

Options:
  -p, --port INT    Port number (default: 8080)
  -h, --host STR    Bind address (default: 0.0.0.0)
  -d, --debug       Debug mode (flag)
      --help        Show this help
```

## Multiple Subcommands

```python
cli = CLI("bidbot", "Freelance bid automation")

# Subcommand: scan
scan = cli.command("scan", "Scan platforms for jobs")
scan.flag("platform", short="p", help="Platform (kwork, laborx, weblancer)", required=True)
scan.flag("limit", short="n", help="Max results", flag_type=int, default=20)

# Subcommand: bid
bid = cli.command("bid", "Submit a bid")
bid.positional("job_id", help="Job ID to bid on", pos_type=str)
bid.flag("amount", short="a", help="Bid amount", flag_type=float, required=True)
bid.flag("message", short="m", help="Cover letter", default="")

# Subcommand: status
status = cli.command("status", "Show bid statistics")

cli.run()
```

## Flags and Options

```python
cmd = cli.command("process", "Process data")

# String flag with short alias
cmd.flag("input", short="i", help="Input file", required=True)

# Integer flag
cmd.flag("workers", short="w", flag_type=int, default=4)

# Boolean flag (store_true)
cmd.flag("verbose", short="v", action="store_true")

# Count flag (-vv = 2)
cmd.flag("verbose", short="v", action="count")
```

## Positional Arguments

```python
cmd = cli.command("download", "Download a file")

# Required positional
cmd.positional("url", help="URL to download")

# Optional positional (has default)
cmd.positional("output", help="Output path", required=False)

@cmd.handler
def download_handler(args):
    fetch(args.url, args.output or "output.bin")
```

## Auto-Generated Help

```bash
$ bidbot --help
Usage: bidbot <command> [options]

Commands:
  scan     Scan platforms for jobs
  bid      Submit a bid
  status   Show bid statistics

Run 'bidbot <command> --help' for command-specific options.
```

## Freelance Tool Example

```python
from darkbot_templates.templates.cli_parser import CLI
from darkbot_templates.templates.sqlite_orm import Database

cli = CLI("freelance", "Freelance management CLI")
db = Database("freelance.db")

# Add bid
add = cli.command("add", "Record a new bid")
add.positional("platform", help="Platform name")
add.positional("job_id", help="Job ID")
add.flag("amount", short="a", flag_type=float, required=True)

@add.handler
def add_handler(args):
    db.table("bids").insert({
        "platform": args.platform,
        "job_id": args.job_id,
        "amount": args.amount,
    })
    print(f"Recorded: {args.platform} #{args.job_id} = ${args.amount}")

# List bids
lst = cli.command("list", "List all bids")
lst.flag("status", short="s", help="Filter by status")

@lst.handler
def list_handler(args):
    q = db.table("bids")
    if args.status:
        q = q.where("status", "=", args.status)
    for bid in q.all():
        print(f"  {bid['platform']:10s} #{bid['job_id']:10s}  ${bid['amount']:8.2f}  {bid['status']}")

cli.run()
```

## Testing

```bash
pytest tests/test_jsonrpc_cli.py -k cli -v
```

## References

- [argparse](https://docs.python.org/3/library/argparse.html) — when you need more power
- [Click](https://click.palletsprojects.com/) — decorator-based CLI framework
- [Typer](https://typer.tiangolo.com/) — type-hint-based CLIs

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*

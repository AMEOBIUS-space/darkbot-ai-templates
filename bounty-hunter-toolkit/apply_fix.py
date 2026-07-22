#!/usr/bin/env python3
"""Bounty Hunter Toolkit — apply secure-coding fix patterns to source files.

This module ships a curated set of "bad → good" code snippets covering common
Python and Solidity security issues. Each pattern performs a literal
search-and-replace: if the vulnerable snippet is present in a target file it is
swapped for the hardened equivalent.

Usage:
    python apply_fix.py --list
    python apply_fix.py --pattern sql_injection --file app.py
    python apply_fix.py --apply sql_injection --file app.py
    python apply_fix.py --find "jwt"
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


class ApplyFixError(Exception):
    """Base error raised for recoverable failures while applying a fix."""


class UnknownPatternError(ApplyFixError):
    """Raised when a requested pattern name is not registered."""


class PatternNotFoundError(ApplyFixError):
    """Raised when a pattern's vulnerable snippet is absent from the target file."""


@dataclass(frozen=True)
class FixPattern:
    """A single search-and-replace security fix pattern.

    Attributes:
        lang: Source language the pattern targets (e.g. ``"python"``).
        desc: Human-readable description of what the fix does.
        bad: The vulnerable snippet to search for.
        good: The hardened snippet to replace it with.
        cwe: CWE identifier (e.g. ``"CWE-89"``).
        severity: Severity level: critical, high, medium, low.
    """

    lang: str
    desc: str
    bad: str
    good: str
    cwe: str = ""
    severity: str = "medium"


PATTERNS: dict[str, FixPattern] = {
    "sql_injection": FixPattern(
        lang="python",
        desc="Replace f-string SQL with parameterized queries",
        bad='cursor.execute(f"SELECT * FROM users WHERE name = \'{name}\'")',
        good='cursor.execute("SELECT * FROM users WHERE name = ?", (name,))',
    ),
    "jwt_none": FixPattern(
        lang="python",
        desc="Force explicit JWT algorithms",
        bad="jwt.decode(token, key, algorithms=None)",
        good='jwt.decode(token, key, algorithms=["HS256", "HS384", "HS512"])',
    ),
    "xxe": FixPattern(
        lang="python",
        desc="Use defusedxml instead of xml.etree",
        bad="import xml.etree.ElementTree as ET",
        good="import defusedxml.ElementTree as DET",
    ),
    "ssti": FixPattern(
        lang="python",
        desc="Use Jinja2 variables instead of f-string templates",
        bad='render_template_string(f"Hello {user_input}")',
        good='render_template_string("Hello {{ name }}", name=user_input)',
    ),
    "csrf": FixPattern(
        lang="python",
        desc="Add per-session CSRF token validation",
        bad="# No CSRF protection",
        good='if request.headers.get("X-CSRF-Token") != session.get("csrf_token"): abort(403)',
    ),
    "open_redirect": FixPattern(
        lang="python",
        desc="Validate redirect URL is same-origin",
        bad='return redirect(request.args.get("next"))',
        good='url = urlparse(request.args.get("next", "/")); if url.netloc: abort(400); return redirect(url.path)',
    ),
    "nosql_injection": FixPattern(
        lang="python",
        desc="Validate input types for NoSQL queries",
        bad='db.users.find({"username": request.json["username"]})',
        good='username = request.json.get("username"); if not isinstance(username, str): abort(400); db.users.find({"username": username})',
    ),
    "yaml_rce": FixPattern(
        lang="python",
        desc="Use yaml.safe_load instead of yaml.load",
        bad="yaml.load(data)",
        good="yaml.safe_load(data)",
    ),
    "pickle_rce": FixPattern(
        lang="python",
        desc="Use restricted unpickler",
        bad="pickle.loads(data)",
        good="pickle.loads(data, fix_imports=False, encoding='ascii')  # Use RestrictedUnpickler for production",
    ),
    "crlf_injection": FixPattern(
        lang="python",
        desc="Strip CR/LF from header values",
        bad='response.headers["Location"] = user_input',
        good='response.headers["Location"] = user_input.replace("\\r", "").replace("\\n", "")',
    ),
}

SOLIDITY_PATTERNS: dict[str, FixPattern] = {
    "zero_amount": FixPattern(
        lang="solidity",
        desc="Add zero-amount check",
        bad="function deposit(uint256 amount) external { token.transferFrom(msg.sender, address(this), amount); }",
        good='function deposit(uint256 amount) external { require(amount > 0, "Zero amount"); token.transferFrom(msg.sender, address(this), amount); }',
    ),
    "reentrancy": FixPattern(
        lang="solidity",
        desc="Add nonReentrant modifier",
        bad="function withdraw() external { /* no guard */ }",
        good="function withdraw() external nonReentrant { /* guarded */ }",
    ),
    "batch_ops": FixPattern(
        lang="solidity",
        desc="Add batch operations with length check",
        bad="function register(address agent) external { /* single */ }",
        good='function batchRegister(address[] calldata agents) external { require(agents.length <= 100, "Batch too large"); for (uint i = 0; i < agents.length; i++) { _register(agents[i]); } }',
    ),
    "permit_replay": FixPattern(
        lang="solidity",
        desc="Add chainId to permit hash",
        bad='bytes32 hash = keccak256(abi.encodePacked("\\x19\\x01", domainSeparator, structHash));',
        good='bytes32 hash = keccak256(abi.encodePacked("\\x19\\x01", keccak256(abi.encode(block.chainid, address(this))), structHash));',
    ),
    "indexed_events": FixPattern(
        lang="solidity",
        desc="Add indexed parameters to events",
        bad="event Swap(address sender, address recipient, uint256 amount);",
        good="event Swap(address indexed sender, address indexed recipient, uint256 amount);",
    ),
}


@dataclass(frozen=True)
class Pattern:
    """Public pattern view returned by :class:`PatternMatcher`.

    Attributes:
        name: Pattern identifier.
        description: Human-readable summary of the fix.
        vulnerable_code: The vulnerable snippet.
        fixed_code: The hardened snippet.
    """

    name: str
    description: str
    vulnerable_code: str
    fixed_code: str


class PatternMatcher:
    """Find and apply security fix patterns by keyword query."""

    def __init__(self, patterns: dict[str, FixPattern] | None = None) -> None:
        self._patterns = patterns if patterns is not None else all_patterns()

    def find(self, query: str) -> list[Pattern]:
        """Return patterns whose name, description, or snippets match ``query``.

        The query is split into whitespace-separated terms; a pattern matches if
        every term appears in at least one of its fields.
        """
        terms = [term for term in query.lower().split() if term]
        if not terms:
            return []

        matches: list[Pattern] = []
        for name, pattern in self._patterns.items():
            haystack = f"{name} {pattern.desc} {pattern.bad} {pattern.good}".lower()
            if all(term in haystack for term in terms):
                matches.append(
                    Pattern(
                        name=name,
                        description=pattern.desc,
                        vulnerable_code=pattern.bad,
                        fixed_code=pattern.good,
                    )
                )
        return matches

    def apply(self, pattern_name: str, file_path: str | Path) -> int:
        """Apply a named pattern to ``file_path``.

        This is a convenience wrapper around :func:`apply_fix`.
        """
        return apply_fix(pattern_name, file_path)


CWE_MAP = {
    "sql_injection": "CWE-89",
    "jwt_none": "CWE-347",
    "xxe": "CWE-611",
    "ssti": "CWE-94",
    "csrf": "CWE-352",
    "open_redirect": "CWE-601",
    "nosql_injection": "CWE-943",
    "yaml_rce": "CWE-502",
    "pickle_rce": "CWE-502",
    "crlf_injection": "CWE-93",
    "zero_amount": "CWE-20",
    "reentrancy": "CWE-833",
    "batch_ops": "CWE-1287",
    "permit_replay": "CWE-294",
    "indexed_events": "CWE-200",
}

SEVERITY_MAP = {
    "sql_injection": "critical",
    "jwt_none": "high",
    "xxe": "high",
    "ssti": "critical",
    "csrf": "medium",
    "open_redirect": "medium",
    "nosql_injection": "critical",
    "yaml_rce": "critical",
    "pickle_rce": "critical",
    "crlf_injection": "medium",
    "zero_amount": "high",
    "reentrancy": "critical",
    "batch_ops": "medium",
    "permit_replay": "high",
    "indexed_events": "low",
}


def _enrich_patterns() -> None:
    """Apply CWE IDs and severity to patterns after module load."""
    for name, cwe in CWE_MAP.items():
        for pattern_dict in (PATTERNS, SOLIDITY_PATTERNS):
            if name in pattern_dict:
                p = pattern_dict[name]
                object.__setattr__(p, "cwe", cwe)
                object.__setattr__(p, "severity", SEVERITY_MAP.get(name, "medium"))


_enrich_patterns()


def all_patterns() -> dict[str, FixPattern]:
    """Return the merged mapping of every registered pattern."""
    return {**PATTERNS, **SOLIDITY_PATTERNS}


def list_patterns() -> None:
    """Print all Python and Solidity patterns grouped by language."""
    print("Python patterns:")
    for name, pattern in PATTERNS.items():
        print(f"  {name}: {pattern.desc}")
    print("\nSolidity patterns:")
    for name, pattern in SOLIDITY_PATTERNS.items():
        print(f"  {name}: {pattern.desc}")


def apply_fix(pattern_name: str, file_path: str | Path) -> int:
    """Apply a named fix pattern to ``file_path``.

    Args:
        pattern_name: Key of the pattern to apply (see :func:`all_patterns`).
        file_path: Path to the source file to modify in place.

    Returns:
        ``0`` if the fix was applied successfully.

    Raises:
        UnknownPatternError: If ``pattern_name`` is not registered.
        PatternNotFoundError: If the pattern's vulnerable snippet is absent.
        FileNotFoundError: If ``file_path`` does not exist.
        IsADirectoryError: If ``file_path`` refers to a directory.
        PermissionError: If the file cannot be read or written.
        UnicodeDecodeError: If the file is not valid UTF-8 text.
    """
    patterns = all_patterns()
    if pattern_name not in patterns:
        raise UnknownPatternError(f"Unknown pattern: {pattern_name}")

    pattern = patterns[pattern_name]
    path = Path(file_path)

    content = path.read_text(encoding="utf-8")

    if pattern.bad not in content:
        raise PatternNotFoundError(
            f"Pattern {pattern_name} not found in {file_path}"
        )

    fixed = content.replace(pattern.bad, pattern.good)
    path.write_text(fixed, encoding="utf-8")
    print(f"Applied {pattern_name} to {file_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code (``0`` on success, non-zero on error).
    """
    parser = argparse.ArgumentParser(description="Bounty Hunter Toolkit")
    parser.add_argument("--list", action="store_true", help="List all patterns")
    parser.add_argument(
        "--pattern", "--apply", help="Pattern to apply (alias: --apply)"
    )
    parser.add_argument("--file", help="File to fix")
    parser.add_argument("--find", help="Find patterns matching a query")
    args = parser.parse_args(argv)

    if args.find:
        matcher = PatternMatcher()
        for p in matcher.find(args.find):
            print(f"{p.name}: {p.description}")
            print(f"  Vulnerable: {p.vulnerable_code[:80]}")
            print(f"  Fixed: {p.fixed_code[:80]}")
        return 0

    if args.list:
        list_patterns()
        return 0

    if args.pattern and args.file:
        try:
            return apply_fix(args.pattern, args.file)
        except ApplyFixError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        except FileNotFoundError:
            print(f"File not found: {args.file}", file=sys.stderr)
            return 1
        except IsADirectoryError:
            print(f"Not a file: {args.file}", file=sys.stderr)
            return 1
        except PermissionError:
            print(f"Permission denied: {args.file}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"I/O error: {args.file}: {exc}", file=sys.stderr)
            return 1
        except UnicodeDecodeError:
            print(f"File is not valid UTF-8 text: {args.file}", file=sys.stderr)
            return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

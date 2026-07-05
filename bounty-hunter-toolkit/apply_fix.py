#!/usr/bin/env python3
"""Bounty Hunter Toolkit — apply fix patterns to code files."""

import argparse
import sys
import json
from pathlib import Path

PATTERNS = {
    "sql_injection": {
        "lang": "python",
        "desc": "Replace f-string SQL with parameterized queries",
        "bad": 'cursor.execute(f"SELECT * FROM users WHERE name = \'{name}\'")',
        "good": 'cursor.execute("SELECT * FROM users WHERE name = ?", (name,))',
    },
    "jwt_none": {
        "lang": "python",
        "desc": "Force explicit JWT algorithms",
        "bad": 'jwt.decode(token, key, algorithms=None)',
        "good": 'jwt.decode(token, key, algorithms=["HS256", "HS384", "HS512"])',
    },
    "xxe": {
        "lang": "python",
        "desc": "Use defusedxml instead of xml.etree",
        "bad": "import xml.etree.ElementTree as ET",
        "good": "import defusedxml.ElementTree as DET",
    },
    "ssti": {
        "lang": "python",
        "desc": "Use Jinja2 variables instead of f-string templates",
        "bad": 'render_template_string(f"Hello {user_input}")',
        "good": 'render_template_string("Hello {{ name }}", name=user_input)',
    },
    "csrf": {
        "lang": "python",
        "desc": "Add per-session CSRF token validation",
        "bad": "# No CSRF protection",
        "good": 'if request.headers.get("X-CSRF-Token") != session.get("csrf_token"): abort(403)',
    },
    "open_redirect": {
        "lang": "python",
        "desc": "Validate redirect URL is same-origin",
        "bad": 'return redirect(request.args.get("next"))',
        "good": 'url = urlparse(request.args.get("next", "/")); if url.netloc: abort(400); return redirect(url.path)',
    },
    "nosql_injection": {
        "lang": "python",
        "desc": "Validate input types for NoSQL queries",
        "bad": 'db.users.find({"username": request.json["username"]})',
        "good": 'username = request.json.get("username"); if not isinstance(username, str): abort(400); db.users.find({"username": username})',
    },
    "yaml_rce": {
        "lang": "python",
        "desc": "Use yaml.safe_load instead of yaml.load",
        "bad": "yaml.load(data)",
        "good": "yaml.safe_load(data)",
    },
    "pickle_rce": {
        "lang": "python",
        "desc": "Use restricted unpickler",
        "bad": "pickle.loads(data)",
        "good": "pickle.loads(data, fix_imports=False, encoding='ascii')  # Use RestrictedUnpickler for production",
    },
    "crlf_injection": {
        "lang": "python",
        "desc": "Strip CR/LF from header values",
        "bad": 'response.headers["Location"] = user_input',
        "good": 'response.headers["Location"] = user_input.replace("\\r", "").replace("\\n", "")',
    },
}

SOLIDITY_PATTERNS = {
    "zero_amount": {
        "lang": "solidity",
        "desc": "Add zero-amount check",
        "bad": "function deposit(uint256 amount) external { token.transferFrom(msg.sender, address(this), amount); }",
        "good": 'function deposit(uint256 amount) external { require(amount > 0, "Zero amount"); token.transferFrom(msg.sender, address(this), amount); }',
    },
    "reentrancy": {
        "lang": "solidity",
        "desc": "Add nonReentrant modifier",
        "bad": "function withdraw() external { /* no guard */ }",
        "good": "function withdraw() external nonReentrant { /* guarded */ }",
    },
    "batch_ops": {
        "lang": "solidity",
        "desc": "Add batch operations with length check",
        "bad": "function register(address agent) external { /* single */ }",
        "good": 'function batchRegister(address[] calldata agents) external { require(agents.length <= 100, "Batch too large"); for (uint i = 0; i < agents.length; i++) { _register(agents[i]); } }',
    },
    "permit_replay": {
        "lang": "solidity",
        "desc": "Add chainId to permit hash",
        "bad": "bytes32 hash = keccak256(abi.encodePacked(\"\\x19\\x01\", domainSeparator, structHash));",
        "good": "bytes32 hash = keccak256(abi.encodePacked(\"\\x19\\x01\", keccak256(abi.encode(block.chainid, address(this))), structHash));",
    },
    "indexed_events": {
        "lang": "solidity",
        "desc": "Add indexed parameters to events",
        "bad": "event Swap(address sender, address recipient, uint256 amount);",
        "good": "event Swap(address indexed sender, address indexed recipient, uint256 amount);",
    },
}


def list_patterns():
    print("Python patterns:")
    for name, p in PATTERNS.items():
        print(f"  {name}: {p['desc']}")
    print("\nSolidity patterns:")
    for name, p in SOLIDITY_PATTERNS.items():
        print(f"  {name}: {p['desc']}")


def apply_fix(pattern_name, file_path):
    all_patterns = {**PATTERNS, **SOLIDITY_PATTERNS}
    if pattern_name not in all_patterns:
        print(f"Unknown pattern: {pattern_name}")
        return 1
    
    p = all_patterns[pattern_name]
    content = Path(file_path).read_text()
    
    if p["bad"] in content:
        fixed = content.replace(p["bad"], p["good"])
        Path(file_path).write_text(fixed)
        print(f"Applied {pattern_name} to {file_path}")
        return 0
    else:
        print(f"Pattern {pattern_name} not found in {file_path}")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bounty Hunter Toolkit")
    parser.add_argument("--list", action="store_true", help="List all patterns")
    parser.add_argument("--pattern", help="Pattern to apply")
    parser.add_argument("--file", help="File to fix")
    args = parser.parse_args()
    
    if args.list:
        list_patterns()
    elif args.pattern and args.file:
        sys.exit(apply_fix(args.pattern, args.file))
    else:
        parser.print_help()

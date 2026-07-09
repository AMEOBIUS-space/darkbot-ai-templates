# PLAN.md — Harness Engineering MCP Products

## Task

Build 3 high-quality MCP servers that solve real harness engineering problems, inspired by awesome-harness-engineering patterns. Zero dependencies, pure Python stdlib.

## Context

We have 104 low-value MCP products (base64 encode, emoji strip). Zero stars, zero sales. The awesome-harness-engineering list shows what the industry actually needs: context management, tool output compression, permission guards, observability. Pivot from quantity to quality.

## Products (in priority order)

### 1. mcp-context-guard — Tool Output Compression & Context Budget Management

**Problem:** Tool outputs (file reads, search results, logs) bloat context windows. Agents waste tokens processing irrelevant data.

**Solution:** MCP server that intercepts, summarizes, deduplicates, and budget-manages tool outputs before they enter context.

**Tools (12):**
- `compress` — Summarize text to N tokens (extractive + frequency-based)
- `budget` — Set token budget, track usage, warn on overflow
- `deduplicate` — Find and remove duplicate/near-duplicate content blocks
- `extract_key` — Extract key sentences/sections from long text
- `truncate_smart` — Context-aware truncation (keep structure, cut verbosity)
- `chunk` — Split large text into token-sized chunks
- `token_count` — Estimate token count (word-based heuristic, no tiktoken)
- `summarize_history` — Compress conversation history into key points
- `filter_relevant` — BM25-like relevance scoring, return top-K passages
- `merge_context` — Combine multiple sources, deduplicate, sort by relevance
- `stats` — Context usage statistics
- `reset` — Reset budgets and stats

**Inspired by:** headroom, context-mode, LLMLingua, Autonomous Context Compression

### 2. mcp-permission-guard — Pre-Action Authorization with Intent Taxonomy

**Problem:** Agents execute destructive actions without guardrails. Permission prompts are noise (93% auto-approved).

**Solution:** MCP server that maps tool calls to intent categories, evaluates risk, and provides deterministic allow/deny/require-approval decisions.

**Tools (10):**
- `register_rule` — Define allow/deny/ask rules by intent category
- `evaluate` — Check an action against rules, get decision
- `classify_intent` — Map a tool call to intent taxonomy (filesystem_delete, network_outbound, etc.)
- `audit_log` — Get audit trail of all evaluated actions
- `risk_assess` — Score risk 0-100 based on intent + arguments + context
- `list_rules` — Show all registered rules
- `remove_rule` — Delete a rule
- `set_policy` — Set global policy (allow_all, deny_all, ask_all, rules_based)
- `get_policy` — Get current policy
- `stats` — Decision statistics

**Inspired by:** nah, Open Agent Passport, Claude Code Auto Mode, Beyond Permission Prompts

### 3. mcp-agent-trace — Observability & Tracing for Agent Loops

**Problem:** Agent decisions are black boxes. No way to trace what happened, what tokens were spent on, where loops occurred.

**Solution:** MCP server that records agent loop events, builds trace trees, computes metrics, and exports traces.

**Tools (12):**
- `start_trace` — Begin a new trace session
- `end_trace` — End session, compute summary metrics
- `log_event` — Record a structured event (tool_call, decision, error, milestone)
- `get_trace` — Get full trace tree for a session
- `get_metrics` — Token usage, tool calls, latency, loop detection
- `detect_loops` — Find repeated action patterns
- `export_trace` — Export as JSON for external analysis
- `list_sessions` — List all trace sessions
- `get_timeline` — Chronological event timeline
- `annotate` — Add human annotation to an event
- `stats` — Aggregate statistics across sessions
- `reset` — Clear all traces

**Inspired by:** AgentDoG, Azure SRE Agent observability, LangChain middleware hooks

## Milestones

- [ ] **M1: mcp-context-guard** — 12 tools, 40+ tests, README with benchmarks | verify: `python -m pytest tests/ -v`
- [ ] **M2: mcp-permission-guard** — 10 tools, 35+ tests, README with examples | verify: `python -m pytest tests/ -v`
- [ ] **M3: mcp-agent-trace** — 12 tools, 40+ tests, README with use cases | verify: `python -m pytest tests/ -v`
- [ ] **Final: PR to awesome-harness-engineering** — Submit all 3 to the awesome list

## Scope boundaries

In scope:
- 3 MCP servers, pure Python stdlib, zero deps
- Comprehensive tests (35-45 per product)
- Quality README with real use cases and benchmarks
- PR to awesome-harness-engineering (not punkpeye/awesome-mcp-servers)

Out of scope:
- More low-value utility servers (base64, emoji, etc.)
- Non-Python implementations
- External service integrations

## Open questions

- [ ] Should we use BM25 from scratch or simpler TF-IDF? — Start with simpler, upgrade if needed
- [ ] Token estimation without tiktoken? — Word count * 1.3 heuristic, documented as approximation

## Risks

- Token estimation accuracy — mitigated by documenting as heuristic
- BM25 implementation complexity — start with TF-IDF, simpler
- Permission rules storage — in-memory dict, persist to JSON file

---
*Created: 2026-07-07*

"""Loop Detector engine — zero dependencies.
Detects when agents are stuck in repeating action patterns.
Tracks action sequences, identifies cycles, and suggests breakouts.
"""
import json, time, hashlib, collections
from typing import Any, Dict, List, Optional, Tuple

class LoopDetector:
    @staticmethod
    def create_store() -> Dict:
        return {
            "stats": {"actions": 0, "loops_found": 0, "breakouts": 0, "errors": 0},
            "actions": [],  # list of {id, tool, args_hash, timestamp, sequence}
            "loops": [],    # detected loops
            "config": {"min_cycle_len": 2, "max_cycle_len": 5, "min_repeats": 2, "window_size": 50},
            "counter": 0,
        }

    @staticmethod
    def _track(store: Dict, op: str, count: int = 1):
        store["stats"][op] = store["stats"].get(op, 0) + count

    @staticmethod
    def _gen_id() -> str:
        return hashlib.sha256(str(time.time()).encode()).hexdigest()[:10]

    @staticmethod
    def record_action(store: Dict, tool: str, args: Dict = None, result_summary: str = "") -> Dict:
        LoopDetector._track(store, "actions")
        args_str = json.dumps(args or {}, sort_keys=True)
        args_hash = hashlib.sha256(args_str.encode()).hexdigest()[:12]

        action = {
            "id": LoopDetector._gen_id(),
            "tool": tool,
            "args_hash": args_hash,
            "args": args or {},
            "result_summary": result_summary,
            "timestamp": time.time(),
            "sequence": len(store["actions"]),
        }
        store["actions"].append(action)
        if len(store["actions"]) > store["config"]["window_size"] * 2:
            store["actions"] = store["actions"][-store["config"]["window_size"]:]

        return {"success": True, "action_id": action["id"], "sequence": action["sequence"]}

    @staticmethod
    def detect_loops(store: Dict, window: int = None) -> Dict:
        LoopDetector._track(store, "loops_found", 0)  # will increment if found
        cfg = store["config"]
        w = window or cfg["window_size"]
        actions = store["actions"][-w:]
        if len(actions) < cfg["min_cycle_len"] * cfg["min_repeats"]:
            return {"success": True, "loops": [], "count": 0, "actions_analyzed": len(actions)}

        # Build sequence of (tool, args_hash) tuples
        seq = [(a["tool"], a["args_hash"]) for a in actions]
        loops = []

        for cycle_len in range(cfg["min_cycle_len"], cfg["max_cycle_len"] + 1):
            if len(seq) < cycle_len * cfg["min_repeats"]:
                continue
            # Check for repeating pattern of length cycle_len
            for start in range(len(seq) - cycle_len * cfg["min_repeats"] + 1):
                pattern = tuple(seq[start:start + cycle_len])
                repeats = 1
                pos = start + cycle_len
                while pos + cycle_len <= len(seq):
                    next_pattern = tuple(seq[pos:pos + cycle_len])
                    if next_pattern == pattern:
                        repeats += 1
                        pos += cycle_len
                    else:
                        break
                if repeats >= cfg["min_repeats"]:
                    loop = {
                        "id": LoopDetector._gen_id(),
                        "pattern": [{"tool": p[0], "args_hash": p[1]} for p in pattern],
                        "cycle_length": cycle_len,
                        "repeats": repeats,
                        "start_sequence": actions[start]["sequence"],
                        "end_sequence": actions[min(start + cycle_len * repeats - 1, len(actions) - 1)]["sequence"],
                        "actions_in_loop": cycle_len * repeats,
                        "tools_involved": list(set(p[0] for p in pattern)),
                    }
                    # Avoid duplicate loops (same pattern, overlapping range)
                    is_dup = False
                    for existing in loops:
                        if existing["cycle_length"] == cycle_len and existing["pattern"] == loop["pattern"]:
                            is_dup = True
                            break
                    if not is_dup:
                        loops.append(loop)

        # Sort by impact (actions wasted)
        loops.sort(key=lambda l: -l["actions_in_loop"])

        if loops:
            LoopDetector._track(store, "loops_found", len(loops))
            store["loops"].extend(loops)
            if len(store["loops"]) > 100:
                store["loops"] = store["loops"][-50:]

        return {
            "success": True,
            "loops": loops,
            "count": len(loops),
            "actions_analyzed": len(actions),
            "window": w,
        }

    @staticmethod
    def suggest_breakout(store: Dict, loop_id: str = None) -> Dict:
        LoopDetector._track(store, "breakouts")
        if loop_id:
            loop = next((l for l in store["loops"] if l["id"] == loop_id), None)
            if not loop:
                return {"success": False, "error": "Loop not found"}
        else:
            loops = store.get("loops", [])
            if not loops:
                return {"success": True, "suggestions": [], "message": "No loops detected yet"}
            loop = loops[-1]

        tools = loop["tools_involved"]
        suggestions = []

        # Generic suggestions based on loop pattern
        if any("read" in t.lower() or "search" in t.lower() for t in tools):
            suggestions.append("Stop reading and start writing. You may have enough context.")
        if any("write" in t.lower() or "edit" in t.lower() or "patch" in t.lower() for t in tools):
            suggestions.append("Run tests to verify your changes instead of making more edits.")
        if any("test" in t.lower() for t in tools):
            suggestions.append("Tests are cycling. Check if there's a flaky test or an actual regression.")
        if any("bash" in t.lower() or "exec" in t.lower() or "terminal" in t.lower() for t in tools):
            suggestions.append("Shell commands are repeating. Check if a process is stuck or waiting for input.")
        if len(tools) == 1:
            suggestions.append(f"You are calling '{tools[0]}' repeatedly. Try a different approach.")
        if loop["repeats"] >= 3:
            suggestions.append("High repetition count. Consider escalating to a human or trying a fundamentally different strategy.")

        # Always add a meta-suggestion
        suggestions.append("Break the cycle: summarize what you've tried, identify what's not working, and choose a different tool or approach.")

        return {
            "success": True,
            "loop_id": loop.get("id"),
            "loop_pattern": loop.get("pattern"),
            "suggestions": suggestions,
            "repeats": loop.get("repeats"),
        }

    @staticmethod
    def get_action_history(store: Dict, limit: int = 20) -> Dict:
        actions = store["actions"][-limit:]
        return {
            "success": True,
            "actions": [{"sequence": a["sequence"], "tool": a["tool"], "args_hash": a["args_hash"], "result_summary": a["result_summary"], "timestamp": a["timestamp"]} for a in actions],
            "total": len(store["actions"]),
        }

    @staticmethod
    def configure(store: Dict, min_cycle_len: int = None, max_cycle_len: int = None, min_repeats: int = None, window_size: int = None) -> Dict:
        if min_cycle_len is not None: store["config"]["min_cycle_len"] = min_cycle_len
        if max_cycle_len is not None: store["config"]["max_cycle_len"] = max_cycle_len
        if min_repeats is not None: store["config"]["min_repeats"] = min_repeats
        if window_size is not None: store["config"]["window_size"] = window_size
        return {"success": True, "config": store["config"]}

    @staticmethod
    def get_config(store: Dict) -> Dict:
        return {"success": True, "config": store["config"]}

    @staticmethod
    def clear_actions(store: Dict) -> Dict:
        count = len(store["actions"])
        store["actions"] = []
        return {"success": True, "cleared": count}

    @staticmethod
    def get_stats(store: Dict) -> Dict:
        return {"success": True, **store["stats"], "total_actions": len(store["actions"]), "total_loops": len(store["loops"])}

    @staticmethod
    def reset(store: Dict) -> Dict:
        old = LoopDetector.get_stats(store)
        store["stats"] = {"actions": 0, "loops_found": 0, "breakouts": 0, "errors": 0}
        store["actions"] = []
        store["loops"] = []
        return {"success": True, "reset": old}

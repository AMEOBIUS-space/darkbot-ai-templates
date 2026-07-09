"""Tool Registry engine — zero dependencies.
Dynamic tool registration, capability discovery, usage tracking, health checks.
"""
import json, time, hashlib, collections
from typing import Any, Dict, List, Optional, Tuple

class ToolRegistry:
    @staticmethod
    def create_store() -> Dict:
        return {
            "stats": {"registered": 0, "called": 0, "disabled": 0, "errors": 0, "health_checks": 0},
            "tools": {},  # tool_name -> {name, description, schema, version, enabled, usage_count, last_called, health_status, category}
            "categories": {},  # category -> [tool_names]
            "call_history": [],
        }

    @staticmethod
    def _track(store: Dict, op: str):
        store["stats"][op] = store["stats"].get(op, 0) + 1

    @staticmethod
    def register(store: Dict, name: str, description: str = "", schema: Dict = None,
                 category: str = "general", version: str = "1.0.0", tags: List[str] = None) -> Dict:
        ToolRegistry._track(store, "registered")
        store["tools"][name] = {
            "name": name,
            "description": description,
            "schema": schema or {"type": "object", "properties": {}},
            "category": category,
            "version": version,
            "tags": tags or [],
            "enabled": True,
            "usage_count": 0,
            "success_count": 0,
            "error_count": 0,
            "last_called": None,
            "registered_at": time.time(),
            "health_status": "unknown",
            "avg_latency_ms": 0,
        }
        if category not in store["categories"]:
            store["categories"][category] = []
        if name not in store["categories"][category]:
            store["categories"][category].append(name)
        return {"success": True, "name": name, "category": category}

    @staticmethod
    def unregister(store: Dict, name: str) -> Dict:
        if name not in store["tools"]:
            return {"success": False, "error": "Tool not found"}
        tool = store["tools"][name]
        cat = tool["category"]
        if cat in store["categories"] and name in store["categories"][cat]:
            store["categories"][cat].remove(name)
        del store["tools"][name]
        return {"success": True, "unregistered": name}

    @staticmethod
    def enable(store: Dict, name: str) -> Dict:
        if name not in store["tools"]:
            return {"success": False, "error": "Tool not found"}
        store["tools"][name]["enabled"] = True
        return {"success": True, "name": name, "enabled": True}

    @staticmethod
    def disable(store: Dict, name: str) -> Dict:
        if name not in store["tools"]:
            return {"success": False, "error": "Tool not found"}
        ToolRegistry._track(store, "disabled")
        store["tools"][name]["enabled"] = False
        return {"success": True, "name": name, "enabled": False}

    @staticmethod
    def record_call(store: Dict, name: str, success: bool, latency_ms: float = 0) -> Dict:
        if name not in store["tools"]:
            return {"success": False, "error": "Tool not found"}
        ToolRegistry._track(store, "called")
        tool = store["tools"][name]
        tool["usage_count"] += 1
        tool["last_called"] = time.time()
        if success:
            tool["success_count"] += 1
        else:
            tool["error_count"] += 1
            ToolRegistry._track(store, "errors")
        # Rolling average latency
        if latency_ms > 0:
            n = tool["usage_count"]
            tool["avg_latency_ms"] = round((tool["avg_latency_ms"] * (n - 1) + latency_ms) / n, 2)

        # Record in history
        store["call_history"].append({"tool": name, "success": success, "latency_ms": latency_ms, "timestamp": time.time()})
        if len(store["call_history"]) > 500:
            store["call_history"] = store["call_history"][-250:]

        return {"success": True, "tool": name, "usage_count": tool["usage_count"], "success_rate": round(tool["success_count"] / tool["usage_count"], 4)}

    @staticmethod
    def get_tool(store: Dict, name: str) -> Dict:
        if name not in store["tools"]:
            return {"success": False, "error": "Tool not found"}
        return {"success": True, "tool": store["tools"][name]}

    @staticmethod
    def list_tools(store: Dict, category: str = None, enabled_only: bool = False) -> Dict:
        tools = []
        for name, tool in store["tools"].items():
            if category and tool["category"] != category:
                continue
            if enabled_only and not tool["enabled"]:
                continue
            tools.append({
                "name": name,
                "description": tool["description"][:60],
                "category": tool["category"],
                "enabled": tool["enabled"],
                "usage_count": tool["usage_count"],
                "health": tool["health_status"],
            })
        return {"success": True, "tools": tools, "total": len(tools)}

    @staticmethod
    def search(store: Dict, query: str) -> Dict:
        query_lower = query.lower()
        results = []
        for name, tool in store["tools"].items():
            score = 0
            if query_lower in name.lower():
                score += 10
            if query_lower in tool["description"].lower():
                score += 5
            for tag in tool.get("tags", []):
                if query_lower in tag.lower():
                    score += 3
            if tool["category"].lower() == query_lower:
                score += 7
            if score > 0:
                results.append({"name": name, "score": score, "description": tool["description"][:60]})
        results.sort(key=lambda x: -x["score"])
        return {"success": True, "results": results[:20], "total": len(results)}

    @staticmethod
    def health_check(store: Dict, name: str = None) -> Dict:
        ToolRegistry._track(store, "health_checks")
        if name:
            if name not in store["tools"]:
                return {"success": False, "error": "Tool not found"}
            tool = store["tools"][name]
            issues = []
            if tool["error_count"] > tool["success_count"] and tool["usage_count"] > 5:
                issues.append("High error rate")
            if tool["avg_latency_ms"] > 5000:
                issues.append("High latency")
            if not tool["enabled"]:
                issues.append("Disabled")
            status = "healthy" if not issues else "unhealthy"
            tool["health_status"] = status
            return {"success": True, "tool": name, "status": status, "issues": issues}
        else:
            results = {}
            for name, tool in store["tools"].items():
                issues = []
                if tool["error_count"] > tool["success_count"] and tool["usage_count"] > 5:
                    issues.append("High error rate")
                if tool["avg_latency_ms"] > 5000:
                    issues.append("High latency")
                if not tool["enabled"]:
                    issues.append("Disabled")
                status = "healthy" if not issues else "unhealthy"
                tool["health_status"] = status
                results[name] = status
            healthy = sum(1 for s in results.values() if s == "healthy")
            return {"success": True, "tools": results, "healthy": healthy, "total": len(results)}

    @staticmethod
    def get_categories(store: Dict) -> Dict:
        return {"success": True, "categories": {cat: len(tools) for cat, tools in store["categories"].items()}, "total": len(store["categories"])}

    @staticmethod
    def get_stats(store: Dict) -> Dict:
        return {
            "success": True,
            **store["stats"],
            "total_tools": len(store["tools"]),
            "enabled_tools": sum(1 for t in store["tools"].values() if t["enabled"]),
            "total_categories": len(store["categories"]),
        }

    @staticmethod
    def reset(store: Dict) -> Dict:
        old = ToolRegistry.get_stats(store)
        store["stats"] = {"registered": 0, "called": 0, "disabled": 0, "errors": 0, "health_checks": 0}
        store["tools"] = {}
        store["categories"] = {}
        store["call_history"] = []
        return {"success": True, "reset": old}

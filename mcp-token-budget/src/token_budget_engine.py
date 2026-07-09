"""Token Budget engine — zero dependencies.
Track token usage, estimate costs, set budgets per model/provider, alert on overruns.
"""
import json, time, hashlib, collections
from typing import Any, Dict, List, Optional, Tuple

class TokenBudget:
    # Approximate pricing per 1M tokens (USD)
    MODEL_PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "claude-sonnet-4": {"input": 3.00, "output": 15.00},
        "claude-haiku-3.5": {"input": 0.25, "output": 1.25},
        "claude-opus-4": {"input": 15.00, "output": 75.00},
        "gemini-2-flash": {"input": 0.10, "output": 0.40},
        "gemini-2-pro": {"input": 1.25, "output": 5.00},
        "deepseek-v3": {"input": 0.27, "output": 1.10},
        "llama-3.1-70b": {"input": 0.59, "output": 0.79},
    }

    @staticmethod
    def create_store() -> Dict:
        return {
            "stats": {"logged": 0, "alerts": 0, "errors": 0},
            "budget": {"limit_usd": 0, "spent_usd": 0.0},
            "usage": [],  # list of {model, input_tokens, output_tokens, cost, timestamp, label}
            "by_model": {},  # model -> {input_tokens, output_tokens, cost, calls}
            "alerts": [],
        }

    @staticmethod
    def _track(store: Dict, op: str):
        store["stats"][op] = store["stats"].get(op, 0) + 1

    @staticmethod
    def estimate_tokens(text: str) -> int:
        import re
        words = len(re.findall(r"\b\w+\b", text))
        return max(1, int(words * 1.3))

    @staticmethod
    def get_pricing(model: str) -> Dict:
        model_lower = model.lower()
        for key, pricing in TokenBudget.MODEL_PRICING.items():
            if key in model_lower:
                return {"model": key, **pricing}
        return {"model": model, "input": 3.00, "output": 15.00, "note": "Estimated pricing (unknown model)"}

    @staticmethod
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> Dict:
        pricing = TokenBudget.get_pricing(model)
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total = input_cost + output_cost
        return {
            "model": pricing["model"],
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total, 6),
            "pricing_input_per_m": pricing["input"],
            "pricing_output_per_m": pricing["output"],
        }

    @staticmethod
    def log_usage(store: Dict, model: str, input_tokens: int, output_tokens: int, label: str = "") -> Dict:
        TokenBudget._track(store, "logged")
        cost = TokenBudget.estimate_cost(model, input_tokens, output_tokens)
        entry = {
            "id": hashlib.sha256(str(time.time()).encode()).hexdigest()[:10],
            "model": cost["model"],
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost["total_cost"],
            "label": label,
            "timestamp": time.time(),
        }
        store["usage"].append(entry)
        if len(store["usage"]) > 1000:
            store["usage"] = store["usage"][-500:]

        # Update by_model
        m = entry["model"]
        if m not in store["by_model"]:
            store["by_model"][m] = {"input_tokens": 0, "output_tokens": 0, "cost": 0.0, "calls": 0}
        store["by_model"][m]["input_tokens"] += input_tokens
        store["by_model"][m]["output_tokens"] += output_tokens
        store["by_model"][m]["cost"] += entry["cost"]
        store["by_model"][m]["calls"] += 1

        # Update budget
        store["budget"]["spent_usd"] += entry["cost"]

        # Check budget alert
        alert = None
        if store["budget"]["limit_usd"] > 0:
            spent = store["budget"]["spent_usd"]
            limit = store["budget"]["limit_usd"]
            pct = spent / limit * 100
            if pct >= 100:
                alert = {"level": "exceeded", "spent": round(spent, 4), "limit": limit, "pct": round(pct, 1)}
                TokenBudget._track(store, "alerts")
                store["alerts"].append({**alert, "timestamp": time.time()})
            elif pct >= 80:
                alert = {"level": "warning", "spent": round(spent, 4), "limit": limit, "pct": round(pct, 1)}

        return {"success": True, **entry, "budget_alert": alert}

    @staticmethod
    def set_budget(store: Dict, limit_usd: float) -> Dict:
        store["budget"]["limit_usd"] = limit_usd
        return {"success": True, "limit_usd": limit_usd, "spent_usd": round(store["budget"]["spent_usd"], 4)}

    @staticmethod
    def get_budget_status(store: Dict) -> Dict:
        b = store["budget"]
        pct = (b["spent_usd"] / b["limit_usd"] * 100) if b["limit_usd"] > 0 else 0
        return {
            "success": True,
            "limit_usd": b["limit_usd"],
            "spent_usd": round(b["spent_usd"], 6),
            "remaining_usd": round(b["limit_usd"] - b["spent_usd"], 6) if b["limit_usd"] > 0 else -1,
            "usage_pct": round(pct, 1),
            "exceeded": b["spent_usd"] >= b["limit_usd"] if b["limit_usd"] > 0 else False,
        }

    @staticmethod
    def get_usage_report(store: Dict, by: str = "model") -> Dict:
        if by == "model":
            data = {}
            for model, stats in store["by_model"].items():
                data[model] = {
                    "calls": stats["calls"],
                    "input_tokens": stats["input_tokens"],
                    "output_tokens": stats["output_tokens"],
                    "total_tokens": stats["input_tokens"] + stats["output_tokens"],
                    "cost": round(stats["cost"], 6),
                    "avg_cost_per_call": round(stats["cost"] / max(stats["calls"], 1), 6),
                }
            return {"success": True, "by": "model", "data": data, "total_calls": len(store["usage"])}
        elif by == "label":
            labels = collections.defaultdict(lambda: {"calls": 0, "cost": 0.0, "tokens": 0})
            for entry in store["usage"]:
                lbl = entry.get("label") or "unlabeled"
                labels[lbl]["calls"] += 1
                labels[lbl]["cost"] += entry["cost"]
                labels[lbl]["tokens"] += entry["input_tokens"] + entry["output_tokens"]
            data = {k: {**v, "cost": round(v["cost"], 6)} for k, v in labels.items()}
            return {"success": True, "by": "label", "data": data, "total_calls": len(store["usage"])}
        else:
            return {"success": True, "data": store["usage"][-50:], "total_calls": len(store["usage"])}

    @staticmethod
    def list_models(store: Dict) -> Dict:
        return {"success": True, "models": TokenBudget.MODEL_PRICING}

    @staticmethod
    def optimize(store: Dict, input_tokens: int, output_tokens: int, models: List[str] = None) -> Dict:
        models = models or list(TokenBudget.MODEL_PRICING.keys())
        results = []
        for m in models:
            cost = TokenBudget.estimate_cost(m, input_tokens, output_tokens)
            results.append({
                "model": cost["model"],
                "total_cost": cost["total_cost"],
                "input_cost": cost["input_cost"],
                "output_cost": cost["output_cost"],
            })
        results.sort(key=lambda x: x["total_cost"])
        cheapest = results[0]
        most_expensive = results[-1]
        savings = most_expensive["total_cost"] - cheapest["total_cost"]
        return {
            "success": True,
            "cheapest": cheapest,
            "most_expensive": most_expensive,
            "potential_savings": round(savings, 6),
            "all": results,
        }

    @staticmethod
    def get_alerts(store: Dict, limit: int = 10) -> Dict:
        return {"success": True, "alerts": store["alerts"][-limit:], "total": len(store["alerts"])}

    @staticmethod
    def get_stats(store: Dict) -> Dict:
        return {
            "success": True,
            **store["stats"],
            "total_calls": len(store["usage"]),
            "total_cost": round(store["budget"]["spent_usd"], 6),
            "models_used": len(store["by_model"]),
        }

    @staticmethod
    def reset(store: Dict) -> Dict:
        old = TokenBudget.get_stats(store)
        store["stats"] = {"logged": 0, "alerts": 0, "errors": 0}
        store["budget"] = {"limit_usd": 0, "spent_usd": 0.0}
        store["usage"] = []
        store["by_model"] = {}
        store["alerts"] = []
        return {"success": True, "reset": old}

"""AB Tester engine — zero dependencies.
A/B test prompts, configs, and strategies. Track outcomes, compute significance.
"""
import json, time, hashlib, math, collections
from typing import Any, Dict, List, Optional, Tuple

class ABTester:
    @staticmethod
    def create_store() -> Dict:
        return {
            "stats": {"experiments": 0, "trials": 0, "completed": 0, "errors": 0},
            "experiments": {},  # exp_id -> {name, variants, results, status, created_at}
            "counter": 0,
        }

    @staticmethod
    def _track(store: Dict, op: str):
        store["stats"][op] = store["stats"].get(op, 0) + 1

    @staticmethod
    def _gen_id() -> str:
        return hashlib.sha256(str(time.time()).encode()).hexdigest()[:10]

    @staticmethod
    def create_experiment(store: Dict, name: str, description: str = "", variants: List[Dict] = None) -> Dict:
        ABTester._track(store, "experiments")
        exp_id = ABTester._gen_id()
        actual_variants = variants if variants else [
            {"id": "A", "label": "control", "config": {}},
            {"id": "B", "label": "treatment", "config": {}},
        ]
        store["experiments"][exp_id] = {
            "id": exp_id,
            "name": name,
            "description": description,
            "variants": actual_variants,
            "results": {v["id"]: {"trials": 0, "successes": 0, "scores": [], "labels": []} for v in actual_variants},
            "status": "active",
            "created_at": time.time(),
            "completed_at": None,
        }
        return {"success": True, "experiment_id": exp_id, "name": name, "variants": len(actual_variants)}

    @staticmethod
    def record_trial(store: Dict, experiment_id: str, variant_id: str, success: bool, score: float = None, label: str = "") -> Dict:
        if experiment_id not in store["experiments"]:
            return {"success": False, "error": "Experiment not found"}
        exp = store["experiments"][experiment_id]
        if exp["status"] != "active":
            return {"success": False, "error": f"Experiment is {exp['status']}"}
        if variant_id not in exp["results"]:
            return {"success": False, "error": f"Variant {variant_id} not found"}

        ABTester._track(store, "trials")
        exp["results"][variant_id]["trials"] += 1
        if success:
            exp["results"][variant_id]["successes"] += 1
        if score is not None:
            exp["results"][variant_id]["scores"].append(score)
        if label:
            exp["results"][variant_id]["labels"].append(label)

        return {"success": True, "experiment_id": experiment_id, "variant_id": variant_id, "total_trials": exp["results"][variant_id]["trials"]}

    @staticmethod
    def get_results(store: Dict, experiment_id: str) -> Dict:
        if experiment_id not in store["experiments"]:
            return {"success": False, "error": "Experiment not found"}
        exp = store["experiments"][experiment_id]
        variant_stats = {}
        for vid, data in exp["results"].items():
            trials = data["trials"]
            successes = data["successes"]
            scores = data["scores"]
            stats = {
                "trials": trials,
                "successes": successes,
                "success_rate": round(successes / max(trials, 1), 4),
                "avg_score": round(sum(scores) / max(len(scores), 1), 4) if scores else None,
                "min_score": min(scores) if scores else None,
                "max_score": max(scores) if scores else None,
                "std_score": round(ABTester._stddev(scores), 4) if len(scores) > 1 else None,
            }
            variant_stats[vid] = stats

        return {
            "success": True,
            "experiment_id": experiment_id,
            "name": exp["name"],
            "status": exp["status"],
            "variants": variant_stats,
            "total_trials": sum(v["trials"] for v in variant_stats.values()),
        }

    @staticmethod
    def _stddev(values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    @staticmethod
    def compute_significance(store: Dict, experiment_id: str) -> Dict:
        if experiment_id not in store["experiments"]:
            return {"success": False, "error": "Experiment not found"}
        exp = store["experiments"][experiment_id]
        vids = list(exp["results"].keys())
        if len(vids) < 2:
            return {"success": False, "error": "Need at least 2 variants"}

        results = []
        for vid in vids:
            data = exp["results"][vid]
            trials = data["trials"]
            successes = data["successes"]
            rate = successes / max(trials, 1)
            # Standard error for proportion
            se = math.sqrt(rate * (1 - rate) / max(trials, 1)) if trials > 0 else 0
            results.append({"variant": vid, "rate": round(rate, 4), "se": round(se, 4), "trials": trials, "successes": successes})

        # Z-test between top two variants
        results.sort(key=lambda r: -r["rate"])
        if len(results) >= 2 and results[0]["se"] > 0 and results[1]["se"] > 0:
            a = results[0]
            b = results[1]
            pooled_se = math.sqrt(a["se"] ** 2 + b["se"] ** 2)
            z_score = (a["rate"] - b["rate"]) / pooled_se if pooled_se > 0 else 0
            p_value = 2 * (1 - ABTester._normal_cdf(abs(z_score)))
            significant = p_value < 0.05
            winner = a["variant"] if significant else None
        else:
            z_score = 0
            p_value = 1.0
            significant = False
            winner = None

        return {
            "success": True,
            "experiment_id": experiment_id,
            "rankings": results,
            "best_variant": results[0]["variant"] if results else None,
            "z_score": round(z_score, 4),
            "p_value": round(p_value, 4),
            "significant": significant,
            "winner": winner,
            "confidence": "high" if p_value < 0.01 else ("medium" if p_value < 0.05 else "low"),
        }

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Approximate normal CDF using error function."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    @staticmethod
    def complete_experiment(store: Dict, experiment_id: str, winner: str = None) -> Dict:
        if experiment_id not in store["experiments"]:
            return {"success": False, "error": "Experiment not found"}
        ABTester._track(store, "completed")
        exp = store["experiments"][experiment_id]
        exp["status"] = "completed"
        exp["completed_at"] = time.time()
        if winner:
            exp["winner"] = winner
        else:
            sig = ABTester.compute_significance(store, experiment_id)
            exp["winner"] = sig.get("winner")
        return {"success": True, "experiment_id": experiment_id, "winner": exp["winner"], "status": "completed"}

    @staticmethod
    def list_experiments(store: Dict, status: str = None) -> Dict:
        exps = []
        for eid, e in store["experiments"].items():
            if status and e["status"] != status:
                continue
            total_trials = sum(v["trials"] for v in e["results"].values())
            exps.append({
                "id": eid,
                "name": e["name"],
                "status": e["status"],
                "variants": len(e["variants"]),
                "total_trials": total_trials,
                "winner": e.get("winner"),
                "created_at": e["created_at"],
            })
        return {"success": True, "experiments": exps, "total": len(exps)}

    @staticmethod
    def delete_experiment(store: Dict, experiment_id: str) -> Dict:
        if experiment_id not in store["experiments"]:
            return {"success": False, "error": "Experiment not found"}
        name = store["experiments"][experiment_id]["name"]
        del store["experiments"][experiment_id]
        return {"success": True, "deleted": experiment_id, "name": name}

    @staticmethod
    def get_stats(store: Dict) -> Dict:
        return {"success": True, **store["stats"], "total_experiments": len(store["experiments"])}

    @staticmethod
    def reset(store: Dict) -> Dict:
        old = ABTester.get_stats(store)
        store["stats"] = {"experiments": 0, "trials": 0, "completed": 0, "errors": 0}
        store["experiments"] = {}
        return {"success": True, "reset": old}

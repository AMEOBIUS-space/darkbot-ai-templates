"""Eval Harness engine — zero dependencies.
Benchmark agent behavior, run regression tests, score outputs,
track quality over time, and generate eval reports.
"""
import json, time, hashlib, collections, statistics
from typing import Any, Dict, List, Optional, Tuple

class EvalHarness:
    @staticmethod
    def create_store() -> Dict:
        return {
            "stats": {"tests_run": 0, "passed": 0, "failed": 0, "errors": 0, "suites_created": 0},
            "suites": {},  # suite_id -> {name, tests, created, results}
            "runs": [],  # list of run results
            "baselines": {},  # suite_id -> baseline score
        }

    @staticmethod
    def _track(store: Dict, op: str, count: int = 1):
        store["stats"][op] = store["stats"].get(op, 0) + count

    @staticmethod
    def _gen_id() -> str:
        return hashlib.sha256(str(time.time()).encode()).hexdigest()[:12]

    @staticmethod
    def create_suite(store: Dict, name: str, description: str = "", tests: List[Dict] = None) -> Dict:
        EvalHarness._track(store, "suites_created")
        suite_id = EvalHarness._gen_id()
        store["suites"][suite_id] = {
            "id": suite_id,
            "name": name,
            "description": description,
            "tests": tests or [],
            "created_at": time.time(),
            "results": [],
        }
        return {"success": True, "suite_id": suite_id, "name": name, "test_count": len(tests or [])}

    @staticmethod
    def add_test(store: Dict, suite_id: str, test_name: str, prompt: str, expected: str = "", check_type: str = "contains", max_score: int = 10) -> Dict:
        if suite_id not in store["suites"]:
            return {"success": False, "error": "Suite not found"}
        test = {
            "id": EvalHarness._gen_id(),
            "name": test_name,
            "prompt": prompt,
            "expected": expected,
            "check_type": check_type,
            "max_score": max_score,
        }
        store["suites"][suite_id]["tests"].append(test)
        return {"success": True, "test_id": test["id"], "suite_id": suite_id}

    @staticmethod
    def evaluate_response(store: Dict, response: str, expected: str, check_type: str = "contains") -> Dict:
        """Evaluate a single response against expected output."""
        EvalHarness._track(store, "tests_run")
        passed = False
        score = 0
        details = {}

        if check_type == "contains":
            passed = expected.lower() in response.lower() if expected else True
            score = 10 if passed else 0
        elif check_type == "exact":
            passed = response.strip() == expected.strip()
            score = 10 if passed else 0
        elif check_type == "regex":
            import re
            passed = bool(re.search(expected, response, re.I)) if expected else True
            score = 10 if passed else 0
        elif check_type == "starts_with":
            passed = response.strip().lower().startswith(expected.strip().lower())
            score = 10 if passed else 0
        elif check_type == "json_valid":
            try:
                json.loads(response)
                passed = True
                score = 10
            except:
                passed = False
                score = 0
        elif check_type == "length":
            try:
                parts = expected.split(":")
                min_len = int(parts[0]) if parts[0] else 0
                max_len = int(parts[1]) if len(parts) > 1 and parts[1] else 999999
                actual = len(response)
                passed = min_len <= actual <= max_len
                score = 10 if passed else max(0, 10 - abs(actual - (min_len + max_len) // 2) // 10)
            except:
                passed = False
                score = 0
        elif check_type == "keyword_count":
            keywords = [k.strip() for k in expected.split(",") if k.strip()]
            found = sum(1 for k in keywords if k.lower() in response.lower())
            passed = found >= len(keywords) // 2 + 1
            score = round(found / max(len(keywords), 1) * 10, 1)
        else:
            passed = True
            score = 10

        if passed:
            EvalHarness._track(store, "passed")
        else:
            EvalHarness._track(store, "failed")

        return {
            "success": True,
            "passed": passed,
            "score": score,
            "max_score": 10,
            "check_type": check_type,
            "response_length": len(response),
            "details": details,
        }

    @staticmethod
    def run_suite(store: Dict, suite_id: str, responses: List[str] = None) -> Dict:
        """Run all tests in a suite. If responses provided, evaluate each."""
        if suite_id not in store["suites"]:
            return {"success": False, "error": "Suite not found"}
        suite = store["suites"][suite_id]
        tests = suite["tests"]

        if responses is None:
            return {"success": True, "suite_id": suite_id, "message": "Provide responses array to evaluate", "test_count": len(tests)}

        results = []
        total_score = 0
        max_score = 0
        passed = 0

        for i, test in enumerate(tests):
            response = responses[i] if i < len(responses) else ""
            r = EvalHarness.evaluate_response(store, response, test.get("expected", ""), test.get("check_type", "contains"))
            results.append({
                "test_id": test["id"],
                "test_name": test["name"],
                "passed": r["passed"],
                "score": r["score"],
                "max_score": test.get("max_score", 10),
            })
            total_score += r["score"]
            max_score += test.get("max_score", 10)
            if r["passed"]:
                passed += 1

        run_result = {
            "run_id": EvalHarness._gen_id(),
            "suite_id": suite_id,
            "timestamp": time.time(),
            "total_tests": len(tests),
            "passed": passed,
            "failed": len(tests) - passed,
            "pass_rate": round(passed / max(len(tests), 1), 4),
            "total_score": total_score,
            "max_score": max_score,
            "score_percentage": round(total_score / max(max_score, 1) * 100, 2),
            "results": results,
        }
        suite["results"].append(run_result)
        store["runs"].append(run_result)

        return {"success": True, **run_result}

    @staticmethod
    def set_baseline(store: Dict, suite_id: str) -> Dict:
        if suite_id not in store["suites"]:
            return {"success": False, "error": "Suite not found"}
        suite = store["suites"][suite_id]
        if not suite["results"]:
            return {"success": False, "error": "No runs yet"}
        last = suite["results"][-1]
        store["baselines"][suite_id] = last["score_percentage"]
        return {"success": True, "suite_id": suite_id, "baseline": last["score_percentage"]}

    @staticmethod
    def check_regression(store: Dict, suite_id: str) -> Dict:
        if suite_id not in store["suites"]:
            return {"success": False, "error": "Suite not found"}
        if suite_id not in store["baselines"]:
            return {"success": False, "error": "No baseline set"}
        suite = store["suites"][suite_id]
        if not suite["results"]:
            return {"success": False, "error": "No runs yet"}
        last = suite["results"][-1]
        baseline = store["baselines"][suite_id]
        current = last["score_percentage"]
        diff = current - baseline
        return {
            "success": True,
            "baseline": baseline,
            "current": current,
            "delta": round(diff, 2),
            "regressed": diff < -5,
            "improved": diff > 5,
            "stable": -5 <= diff <= 5,
        }

    @staticmethod
    def get_report(store: Dict, suite_id: str = None) -> Dict:
        if suite_id:
            if suite_id not in store["suites"]:
                return {"success": False, "error": "Suite not found"}
            suite = store["suites"][suite_id]
            runs = suite["results"]
            if not runs:
                return {"success": True, "suite_id": suite_id, "message": "No runs yet", "test_count": len(suite["tests"])}
            scores = [r["score_percentage"] for r in runs]
            pass_rates = [r["pass_rate"] for r in runs]
            return {
                "success": True,
                "suite_id": suite_id,
                "suite_name": suite["name"],
                "total_runs": len(runs),
                "total_tests": len(suite["tests"]),
                "avg_score": round(statistics.mean(scores), 2),
                "max_score": max(scores),
                "min_score": min(scores),
                "latest_score": scores[-1],
                "avg_pass_rate": round(statistics.mean(pass_rates), 4),
                "trend": "up" if len(scores) > 1 and scores[-1] > scores[-2] else ("down" if len(scores) > 1 and scores[-1] < scores[-2] else "stable"),
                "baseline": store["baselines"].get(suite_id),
            }
        else:
            # Aggregate report
            all_runs = store["runs"]
            if not all_runs:
                return {"success": True, "total_suites": len(store["suites"]), "total_runs": 0, "message": "No runs yet"}
            all_scores = [r["score_percentage"] for r in all_runs]
            return {
                "success": True,
                "total_suites": len(store["suites"]),
                "total_runs": len(all_runs),
                "avg_score": round(statistics.mean(all_scores), 2),
                "total_tests_run": store["stats"]["tests_run"],
                "total_passed": store["stats"]["passed"],
                "total_failed": store["stats"]["failed"],
                "overall_pass_rate": round(store["stats"]["passed"] / max(store["stats"]["tests_run"], 1), 4),
            }

    @staticmethod
    def list_suites(store: Dict) -> Dict:
        suites = []
        for sid, s in store["suites"].items():
            suites.append({
                "id": sid,
                "name": s["name"],
                "test_count": len(s["tests"]),
                "runs": len(s["results"]),
                "created_at": s["created_at"],
            })
        return {"success": True, "suites": suites, "total": len(suites)}

    @staticmethod
    def get_stats(store: Dict) -> Dict:
        return {"success": True, **store["stats"], "total_suites": len(store["suites"]), "total_runs": len(store["runs"])}

    @staticmethod
    def reset(store: Dict) -> Dict:
        old = EvalHarness.get_stats(store)
        store["stats"] = {"tests_run": 0, "passed": 0, "failed": 0, "errors": 0, "suites_created": 0}
        store["suites"] = {}
        store["runs"] = []
        store["baselines"] = {}
        return {"success": True, "reset": old}

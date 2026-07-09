"""Prompt Versioning engine — zero dependencies.
Version control for prompts: save, diff, rollback, branch, compare effectiveness.
"""
import json, time, hashlib, difflib, copy
from typing import Any, Dict, List, Optional, Tuple

class PromptVersioning:
    @staticmethod
    def create_store() -> Dict:
        return {
            "stats": {"saved": 0, "rolled_back": 0, "diffed": 0, "branched": 0, "errors": 0},
            "prompts": {},  # prompt_id -> {name, versions: [{id, text, metadata, created_at, parent}], active_version, branches}
            "counter": 0,
        }

    @staticmethod
    def _track(store: Dict, op: str):
        store["stats"][op] = store["stats"].get(op, 0) + 1

    @staticmethod
    def _gen_id() -> str:
        return hashlib.sha256(str(time.time()).encode()).hexdigest()[:10]

    @staticmethod
    def create_prompt(store: Dict, name: str, text: str, metadata: Dict = None) -> Dict:
        PromptVersioning._track(store, "saved")
        prompt_id = PromptVersioning._gen_id()
        version_id = "v1"
        store["prompts"][prompt_id] = {
            "id": prompt_id,
            "name": name,
            "versions": [{
                "id": version_id,
                "text": text,
                "metadata": metadata or {},
                "created_at": time.time(),
                "parent": None,
            }],
            "active_version": version_id,
            "branches": {},
        }
        return {"success": True, "prompt_id": prompt_id, "version_id": version_id, "name": name}

    @staticmethod
    def save_version(store: Dict, prompt_id: str, text: str, metadata: Dict = None, message: str = "") -> Dict:
        if prompt_id not in store["prompts"]:
            return {"success": False, "error": "Prompt not found"}
        PromptVersioning._track(store, "saved")
        prompt = store["prompts"][prompt_id]
        version_num = len(prompt["versions"]) + 1
        version_id = f"v{version_num}"
        prompt["versions"].append({
            "id": version_id,
            "text": text,
            "metadata": metadata or {},
            "message": message,
            "created_at": time.time(),
            "parent": prompt["active_version"],
        })
        prompt["active_version"] = version_id
        return {"success": True, "prompt_id": prompt_id, "version_id": version_id, "parent": prompt["versions"][-1]["parent"]}

    @staticmethod
    def get_version(store: Dict, prompt_id: str, version_id: str = None) -> Dict:
        if prompt_id not in store["prompts"]:
            return {"success": False, "error": "Prompt not found"}
        prompt = store["prompts"][prompt_id]
        vid = version_id or prompt["active_version"]
        for v in prompt["versions"]:
            if v["id"] == vid:
                return {"success": True, "prompt_id": prompt_id, "version": v, "is_active": vid == prompt["active_version"]}
        return {"success": False, "error": f"Version {vid} not found"}

    @staticmethod
    def get_active(store: Dict, prompt_id: str) -> Dict:
        if prompt_id not in store["prompts"]:
            return {"success": False, "error": "Prompt not found"}
        prompt = store["prompts"][prompt_id]
        return PromptVersioning.get_version(store, prompt_id, prompt["active_version"])

    @staticmethod
    def rollback(store: Dict, prompt_id: str, version_id: str) -> Dict:
        if prompt_id not in store["prompts"]:
            return {"success": False, "error": "Prompt not found"}
        prompt = store["prompts"][prompt_id]
        found = any(v["id"] == version_id for v in prompt["versions"])
        if not found:
            return {"success": False, "error": f"Version {version_id} not found"}
        old_active = prompt["active_version"]
        prompt["active_version"] = version_id
        PromptVersioning._track(store, "rolled_back")
        return {"success": True, "prompt_id": prompt_id, "new_active": version_id, "previous_active": old_active}

    @staticmethod
    def diff(store: Dict, prompt_id: str, version_a: str, version_b: str) -> Dict:
        if prompt_id not in store["prompts"]:
            return {"success": False, "error": "Prompt not found"}
        PromptVersioning._track(store, "diffed")
        prompt = store["prompts"][prompt_id]
        text_a = None
        text_b = None
        for v in prompt["versions"]:
            if v["id"] == version_a: text_a = v["text"]
            if v["id"] == version_b: text_b = v["text"]
        if text_a is None or text_b is None:
            return {"success": False, "error": "Version not found"}

        lines_a = text_a.splitlines(keepends=True)
        lines_b = text_b.splitlines(keepends=True)
        diff = list(difflib.unified_diff(lines_a, lines_b, fromfile=version_a, tofile=version_b))
        diff_text = "".join(diff) if diff else "(no differences)"

        additions = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
        deletions = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))

        return {
            "success": True,
            "prompt_id": prompt_id,
            "version_a": version_a,
            "version_b": version_b,
            "diff": diff_text,
            "additions": additions,
            "deletions": deletions,
            "identical": len(diff) == 0,
        }

    @staticmethod
    def list_versions(store: Dict, prompt_id: str) -> Dict:
        if prompt_id not in store["prompts"]:
            return {"success": False, "error": "Prompt not found"}
        prompt = store["prompts"][prompt_id]
        versions = [{
            "id": v["id"],
            "created_at": v["created_at"],
            "message": v.get("message", ""),
            "parent": v.get("parent"),
            "is_active": v["id"] == prompt["active_version"],
        } for v in prompt["versions"]]
        return {"success": True, "prompt_id": prompt_id, "name": prompt["name"], "versions": versions, "total": len(versions)}

    @staticmethod
    def list_prompts(store: Dict) -> Dict:
        prompts = []
        for pid, p in store["prompts"].items():
            prompts.append({
                "id": pid,
                "name": p["name"],
                "version_count": len(p["versions"]),
                "active_version": p["active_version"],
            })
        return {"success": True, "prompts": prompts, "total": len(prompts)}

    @staticmethod
    def branch(store: Dict, prompt_id: str, branch_name: str, from_version: str = None) -> Dict:
        if prompt_id not in store["prompts"]:
            return {"success": False, "error": "Prompt not found"}
        PromptVersioning._track(store, "branched")
        prompt = store["prompts"][prompt_id]
        base_version = from_version or prompt["active_version"]
        base_text = None
        for v in prompt["versions"]:
            if v["id"] == base_version:
                base_text = v["text"]
                break
        if base_text is None:
            return {"success": False, "error": "Base version not found"}
        prompt["branches"][branch_name] = {
            "name": branch_name,
            "base_version": base_version,
            "created_at": time.time(),
            "text": base_text,
        }
        return {"success": True, "prompt_id": prompt_id, "branch_name": branch_name, "base_version": base_version}

    @staticmethod
    def compare_effectiveness(store: Dict, prompt_id: str, version_a: str, version_b: str,
                               score_a: float, score_b: float) -> Dict:
        result = PromptVersioning.diff(store, prompt_id, version_a, version_b)
        if not result["success"]:
            return result
        delta = score_b - score_a
        improvement_pct = round((delta / max(abs(score_a), 0.001)) * 100, 2) if score_a != 0 else 0
        return {
            **result,
            "score_a": score_a,
            "score_b": score_b,
            "delta": round(delta, 4),
            "improvement_pct": improvement_pct,
            "winner": version_b if score_b > score_a else (version_a if score_a > score_b else "tie"),
        }

    @staticmethod
    def delete_prompt(store: Dict, prompt_id: str) -> Dict:
        if prompt_id not in store["prompts"]:
            return {"success": False, "error": "Prompt not found"}
        name = store["prompts"][prompt_id]["name"]
        del store["prompts"][prompt_id]
        return {"success": True, "deleted": prompt_id, "name": name}

    @staticmethod
    def get_stats(store: Dict) -> Dict:
        return {"success": True, **store["stats"], "total_prompts": len(store["prompts"])}

    @staticmethod
    def reset(store: Dict) -> Dict:
        old = PromptVersioning.get_stats(store)
        store["stats"] = {"saved": 0, "rolled_back": 0, "diffed": 0, "branched": 0, "errors": 0}
        store["prompts"] = {}
        store["counter"] = 0
        return {"success": True, "reset": old}

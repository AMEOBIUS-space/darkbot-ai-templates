"""Skill Router engine — zero dependencies.
Routes tasks to the right skills/tools based on intent classification,
keyword matching, semantic similarity, and usage history.
"""
import re, json, math, time, hashlib, collections
from typing import Any, Dict, List, Optional, Tuple

class SkillRouter:
    @staticmethod
    def create_store() -> Dict:
        return {
            "stats": {"routed": 0, "matched": 0, "fallback": 0, "errors": 0, "learned": 0},
            "skills": {},  # skill_id -> {name, description, keywords, patterns, examples, priority, usage_count, success_count}
            "history": [],  # routing decisions for learning
            "counter": 0,
        }

    @staticmethod
    def _track(store: Dict, op: str, count: int = 1):
        store["stats"][op] = store["stats"].get(op, 0) + count

    @staticmethod
    def _gen_id() -> str:
        store_counter = time.time()
        return hashlib.sha256(str(store_counter).encode()).hexdigest()[:10]

    @staticmethod
    def register_skill(store: Dict, name: str, description: str, keywords: List[str] = None,
                       patterns: List[str] = None, examples: List[str] = None, priority: int = 0) -> Dict:
        SkillRouter._track(store, "learned")
        skill_id = SkillRouter._gen_id()
        store["skills"][skill_id] = {
            "id": skill_id,
            "name": name,
            "description": description,
            "keywords": [k.lower() for k in (keywords or [])],
            "patterns": patterns or [],
            "examples": examples or [],
            "priority": priority,
            "usage_count": 0,
            "success_count": 0,
            "fail_count": 0,
            "created_at": time.time(),
        }
        return {"success": True, "skill_id": skill_id, "name": name}

    @staticmethod
    def remove_skill(store: Dict, skill_id: str) -> Dict:
        if skill_id not in store["skills"]:
            return {"success": False, "error": "Skill not found"}
        name = store["skills"][skill_id]["name"]
        del store["skills"][skill_id]
        return {"success": True, "removed": skill_id, "name": name}

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\b\w+\b", text.lower())

    @staticmethod
    def _cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        if not vec1 or not vec2:
            return 0.0
        common = set(vec1.keys()) & set(vec2.keys())
        dot = sum(vec1[w] * vec2[w] for w in common)
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot / (mag1 * mag2)

    @staticmethod
    def _score_skill(skill: Dict, query: str, query_tokens: List[str], query_vec: Dict[str, float]) -> Tuple[float, Dict]:
        """Score a skill against a query using multiple signals."""
        score = 0.0
        signals = {}

        # 1. Keyword match (strong signal)
        kw_matches = sum(1 for kw in skill["keywords"] if kw in " ".join(query_tokens))
        if kw_matches > 0:
            kw_score = min(kw_matches * 5.0, 15.0)
            score += kw_score
            signals["keyword"] = kw_score

        # 2. Pattern match (very strong signal)
        pattern_hits = 0
        for pattern in skill["patterns"]:
            if re.search(pattern, query, re.I):
                pattern_hits += 1
        if pattern_hits > 0:
            pat_score = pattern_hits * 10.0
            score += pat_score
            signals["pattern"] = pat_score

        # 3. Description TF-IDF similarity
        desc_tokens = SkillRouter._tokenize(skill["description"])
        desc_words = set(desc_tokens + skill["keywords"])
        # Build simple TF vector for description
        desc_vec = {}
        for w in desc_tokens:
            desc_vec[w] = desc_vec.get(w, 0) + 1
        # Add keywords with boost
        for kw in skill["keywords"]:
            desc_vec[kw] = desc_vec.get(kw, 0) + 2

        sim = SkillRouter._cosine_similarity(query_vec, desc_vec)
        if sim > 0:
            sim_score = sim * 8.0
            score += sim_score
            signals["semantic"] = round(sim_score, 2)

        # 4. Example match
        for example in skill["examples"]:
            ex_tokens = set(SkillRouter._tokenize(example))
            overlap = len(ex_tokens & set(query_tokens))
            if overlap > 0:
                ex_score = overlap * 2.0
                score += ex_score
                signals["example"] = signals.get("example", 0) + ex_score

        # 5. Priority boost
        if skill["priority"] > 0:
            score += skill["priority"] * 0.5
            signals["priority"] = skill["priority"] * 0.5

        # 6. Usage history (success rate)
        total = skill["usage_count"]
        if total > 0:
            success_rate = skill["success_count"] / total
            history_boost = success_rate * 3.0
            score += history_boost
            signals["history"] = round(history_boost, 2)

        return score, signals

    @staticmethod
    def route(store: Dict, query: str, top_k: int = 3) -> Dict:
        """Route a query to the best matching skills."""
        SkillRouter._track(store, "routed")
        query_tokens = SkillRouter._tokenize(query)
        query_vec = {}
        for w in query_tokens:
            query_vec[w] = query_vec.get(w, 0) + 1

        scored = []
        for sid, skill in store["skills"].items():
            score, signals = SkillRouter._score_skill(skill, query, query_tokens, query_vec)
            if score > 0:
                scored.append({
                    "skill_id": sid,
                    "name": skill["name"],
                    "description": skill["description"],
                    "score": round(score, 2),
                    "signals": signals,
                })

        scored.sort(key=lambda x: -x["score"])
        top = scored[:top_k]

        if not top:
            SkillRouter._track(store, "fallback")
            return {
                "success": True,
                "matched": False,
                "query": query,
                "message": "No matching skills found",
                "fallback": True,
            }

        SkillRouter._track(store, "matched")
        # Record in history
        entry = {"query": query, "top_skill": top[0]["skill_id"], "timestamp": time.time()}
        store["history"].append(entry)
        if len(store["history"]) > 500:
            store["history"] = store["history"][-250:]

        return {
            "success": True,
            "matched": True,
            "query": query,
            "results": top,
            "best_match": top[0]["name"],
            "best_score": top[0]["score"],
        }

    @staticmethod
    def record_outcome(store: Dict, skill_id: str, success: bool) -> Dict:
        """Record whether a routing decision was successful (for learning)."""
        if skill_id not in store["skills"]:
            return {"success": False, "error": "Skill not found"}
        skill = store["skills"][skill_id]
        skill["usage_count"] += 1
        if success:
            skill["success_count"] += 1
        else:
            skill["fail_count"] += 1
        return {"success": True, "skill_id": skill_id, "usage_count": skill["usage_count"], "success_rate": round(skill["success_count"] / skill["usage_count"], 2)}

    @staticmethod
    def list_skills(store: Dict) -> Dict:
        skills = []
        for sid, s in store["skills"].items():
            rate = round(s["success_count"] / s["usage_count"], 2) if s["usage_count"] > 0 else None
            skills.append({
                "id": sid,
                "name": s["name"],
                "description": s["description"][:80],
                "priority": s["priority"],
                "keywords_count": len(s["keywords"]),
                "usage_count": s["usage_count"],
                "success_rate": rate,
            })
        skills.sort(key=lambda x: -x["priority"])
        return {"success": True, "skills": skills, "total": len(skills)}

    @staticmethod
    def update_skill(store: Dict, skill_id: str, name: str = None, description: str = None,
                     keywords: List[str] = None, patterns: List[str] = None, priority: int = None) -> Dict:
        if skill_id not in store["skills"]:
            return {"success": False, "error": "Skill not found"}
        skill = store["skills"][skill_id]
        if name is not None: skill["name"] = name
        if description is not None: skill["description"] = description
        if keywords is not None: skill["keywords"] = [k.lower() for k in keywords]
        if patterns is not None: skill["patterns"] = patterns
        if priority is not None: skill["priority"] = priority
        return {"success": True, "skill_id": skill_id, "updated_fields": [k for k in ["name","description","keywords","patterns","priority"] if locals().get(k) is not None]}

    @staticmethod
    def get_routing_history(store: Dict, limit: int = 20) -> Dict:
        return {"success": True, "history": store["history"][-limit:], "total": len(store["history"])}

    @staticmethod
    def get_stats(store: Dict) -> Dict:
        return {"success": True, **store["stats"], "total_skills": len(store["skills"])}

    @staticmethod
    def reset(store: Dict) -> Dict:
        old = SkillRouter.get_stats(store)
        store["stats"] = {"routed": 0, "matched": 0, "fallback": 0, "errors": 0, "learned": 0}
        store["skills"] = {}
        store["history"] = []
        return {"success": True, "reset": old}

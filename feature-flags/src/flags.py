"""Feature Flag Manager — toggles, percentage rollouts, A/B testing, environment targeting."""
import json
import hashlib
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum


class FlagType(Enum):
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    VARIANT = "variant"
    KILL_SWITCH = "kill_switch"


@dataclass
class FeatureFlag:
    key: str
    flag_type: FlagType
    enabled: bool = True
    percentage: float = 100.0  # 0-100
    variants: List[str] = field(default_factory=list)
    default_variant: str = ""
    environments: List[str] = field(default_factory=lambda: ["production", "staging", "development"])
    target_users: Set[str] = field(default_factory=set)
    excluded_users: Set[str] = field(default_factory=set)
    metadata: Dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    description: str = ""


class FeatureFlagManager:
    """Manage feature flags with targeting, rollouts, and A/B testing."""

    def __init__(self, current_environment: str = "production"):
        self.environment = current_environment
        self.flags: Dict[str, FeatureFlag] = {}
        self._overrides: Dict[str, Dict[str, Any]] = {}  # user_id -> {flag_key -> value}

    def create(self, key: str, flag_type: FlagType = FlagType.BOOLEAN,
               description: str = "", **kwargs) -> FeatureFlag:
        """Create a new feature flag."""
        now = datetime.now().isoformat()
        flag = FeatureFlag(
            key=key,
            flag_type=flag_type,
            description=description,
            created_at=now,
            updated_at=now,
            **kwargs,
        )
        self.flags[key] = flag
        return flag

    def is_enabled(self, key: str, user_id: str = None) -> bool:
        """Check if a boolean flag is enabled for a user."""
        # Check override first
        if user_id and key in self._overrides.get(user_id, {}):
            return self._overrides[user_id][key]

        flag = self.flags.get(key)
        if not flag or not flag.enabled:
            return False

        if self.environment not in flag.environments:
            return False

        if user_id:
            if user_id in flag.excluded_users:
                return False
            if flag.target_users:
                if user_id in flag.target_users:
                    return True
                return False

        if flag.flag_type == FlagType.KILL_SWITCH:
            return flag.enabled

        if flag.flag_type == FlagType.PERCENTAGE:
            return self._hash_percentage(key, user_id or "anonymous") < flag.percentage

        if flag.flag_type == FlagType.BOOLEAN:
            return flag.percentage >= 100.0 or self._hash_percentage(key, user_id or "anonymous") < flag.percentage

        return flag.enabled

    def get_variant(self, key: str, user_id: str = None) -> str:
        """Get the A/B test variant for a user."""
        if user_id and key in self._overrides.get(user_id, {}):
            return self._overrides[user_id][key]

        flag = self.flags.get(key)
        if not flag or not flag.enabled:
            return flag.default_variant if flag else ""

        if self.environment not in flag.environments:
            return flag.default_variant

        if not flag.variants:
            return flag.default_variant

        if user_id and user_id in flag.excluded_users:
            return flag.default_variant

        # Hash-based variant assignment for consistent distribution
        hash_val = self._hash_percentage(key, user_id or "anonymous")
        variant_index = int(hash_val / 100.0 * len(flag.variants))
        variant_index = min(variant_index, len(flag.variants) - 1)
        return flag.variants[variant_index]

    def get_percentage(self, key: str, user_id: str = None) -> float:
        """Get the rollout percentage for a user (0-100)."""
        flag = self.flags.get(key)
        if not flag or not flag.enabled:
            return 0.0
        if self.environment not in flag.environments:
            return 0.0
        user_hash = self._hash_percentage(key, user_id or "anonymous")
        return flag.percentage if user_hash < flag.percentage else 0.0

    @staticmethod
    def _hash_percentage(key: str, user_id: str) -> float:
        """Deterministic hash to percentage (0-100). Same user always gets same result."""
        combined = f"{key}:{user_id}"
        hash_val = hashlib.md5(combined.encode()).hexdigest()
        return int(hash_val[:8], 16) % 10000 / 100.0

    def set_override(self, user_id: str, flag_key: str, value: Any):
        """Set a per-user override for a flag."""
        if user_id not in self._overrides:
            self._overrides[user_id] = {}
        self._overrides[user_id][flag_key] = value

    def clear_override(self, user_id: str, flag_key: str = None):
        """Clear user overrides."""
        if flag_key:
            self._overrides.get(user_id, {}).pop(flag_key, None)
        else:
            self._overrides.pop(user_id, None)

    def toggle(self, key: str, enabled: bool = None) -> bool:
        """Toggle a flag on/off. Returns new state."""
        flag = self.flags.get(key)
        if flag:
            flag.enabled = not flag.enabled if enabled is None else enabled
            flag.updated_at = datetime.now().isoformat()
            return flag.enabled
        return False

    def set_percentage(self, key: str, percentage: float):
        """Update rollout percentage."""
        if key in self.flags:
            self.flags[key].percentage = max(0.0, min(100.0, percentage))
            self.flags[key].updated_at = datetime.now().isoformat()

    def add_target_user(self, key: str, user_id: str):
        """Add a targeted user to a flag."""
        if key in self.flags:
            self.flags[key].target_users.add(user_id)

    def add_excluded_user(self, key: str, user_id: str):
        """Exclude a user from a flag."""
        if key in self.flags:
            self.flags[key].excluded_users.add(user_id)

    def list_flags(self) -> List[Dict]:
        """List all flags with their current state."""
        return [
            {
                "key": f.key,
                "type": f.flag_type.value,
                "enabled": f.enabled,
                "percentage": f.percentage,
                "variants": f.variants,
                "environments": f.environments,
                "target_users": list(f.target_users),
                "description": f.description,
            }
            for f in self.flags.values()
        ]

    def export(self) -> str:
        """Export all flags as JSON."""
        data = {}
        for key, flag in self.flags.items():
            d = asdict(flag)
            d["flag_type"] = flag.flag_type.value
            d["target_users"] = list(flag.target_users)
            d["excluded_users"] = list(flag.excluded_users)
            data[key] = d
        return json.dumps(data, indent=2)

    def import_flags(self, json_str: str):
        """Import flags from JSON."""
        data = json.loads(json_str)
        for key, d in data.items():
            flag = FeatureFlag(
                key=key,
                flag_type=FlagType(d.get("flag_type", "boolean")),
                enabled=d.get("enabled", True),
                percentage=d.get("percentage", 100.0),
                variants=d.get("variants", []),
                default_variant=d.get("default_variant", ""),
                environments=d.get("environments", ["production"]),
                target_users=set(d.get("target_users", [])),
                excluded_users=set(d.get("excluded_users", [])),
                metadata=d.get("metadata", {}),
                created_at=d.get("created_at", ""),
                updated_at=d.get("updated_at", ""),
                description=d.get("description", ""),
            )
            self.flags[key] = flag

    def stats(self) -> Dict:
        return {
            "total_flags": len(self.flags),
            "enabled": sum(1 for f in self.flags.values() if f.enabled),
            "disabled": sum(1 for f in self.flags.values() if not f.enabled),
            "by_type": {t.value: sum(1 for f in self.flags.values() if f.flag_type == t) for t in FlagType},
            "overrides": sum(len(v) for v in self._overrides.values()),
        }

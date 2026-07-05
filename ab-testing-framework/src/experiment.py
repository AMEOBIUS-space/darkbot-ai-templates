"""AB Testing Framework — experiment tracking, variant assignment, statistical significance."""
import math
import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum


class ExperimentStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


@dataclass
class Variant:
    name: str
    weight: float = 50.0  # traffic percentage
    conversions: int = 0
    visitors: int = 0
    revenue: float = 0.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class Experiment:
    id: str
    name: str
    description: str = ""
    status: ExperimentStatus = ExperimentStatus.DRAFT
    variants: Dict[str, Variant] = field(default_factory=dict)
    control_variant: str = "control"
    started_at: str = ""
    ended_at: str = ""
    target_metric: str = "conversion_rate"
    min_sample_size: int = 100
    significance_level: float = 0.05


class ABTestingFramework:
    """Run and analyze A/B test experiments."""

    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self._assignments: Dict[str, str] = {}  # user_id -> variant_name

    def create_experiment(self, exp_id: str, name: str, description: str = "",
                          variants: List[str] = None, control: str = "control") -> Experiment:
        """Create a new experiment."""
        exp = Experiment(id=exp_id, name=name, description=description, control_variant=control)
        variant_names = variants or ["control", "treatment"]
        total = len(variant_names)
        for vname in variant_names:
            exp.variants[vname] = Variant(name=vname, weight=100.0 / total)
        self.experiments[exp_id] = exp
        return exp

    def start(self, exp_id: str) -> bool:
        exp = self.experiments.get(exp_id)
        if exp and exp.status == ExperimentStatus.DRAFT:
            exp.status = ExperimentStatus.RUNNING
            exp.started_at = datetime.now().isoformat()
            return True
        return False

    def stop(self, exp_id: str) -> bool:
        exp = self.experiments.get(exp_id)
        if exp:
            exp.status = ExperimentStatus.STOPPED
            exp.ended_at = datetime.now().isoformat()
            return True
        return False

    def complete(self, exp_id: str) -> bool:
        exp = self.experiments.get(exp_id)
        if exp:
            exp.status = ExperimentStatus.COMPLETED
            exp.ended_at = datetime.now().isoformat()
            return True
        return False

    def assign_variant(self, exp_id: str, user_id: str) -> Optional[str]:
        """Deterministically assign a user to a variant."""
        exp = self.experiments.get(exp_id)
        if not exp or exp.status != ExperimentStatus.RUNNING:
            return None

        assignment_key = f"{exp_id}:{user_id}"
        if assignment_key in self._assignments:
            return self._assignments[assignment_key]

        # Hash-based assignment for consistency
        hash_val = int(hashlib.md5(assignment_key.encode()).hexdigest()[:8], 16)
        cumulative = 0.0
        assigned = None
        for vname, variant in exp.variants.items():
            cumulative += variant.weight
            if hash_val % 10000 / 100.0 < cumulative:
                assigned = vname
                break
        if not assigned:
            assigned = list(exp.variants.keys())[-1]

        self._assignments[assignment_key] = assigned
        exp.variants[assigned].visitors += 1
        return assigned

    def track_conversion(self, exp_id: str, user_id: str, revenue: float = 0.0) -> bool:
        """Track a conversion for a user."""
        exp = self.experiments.get(exp_id)
        if not exp:
            return False
        assignment_key = f"{exp_id}:{user_id}"
        variant_name = self._assignments.get(assignment_key)
        if not variant_name:
            return False
        variant = exp.variants.get(variant_name)
        if variant:
            variant.conversions += 1
            variant.revenue += revenue
            return True
        return False

    def get_variant(self, exp_id: str, user_id: str) -> Optional[str]:
        """Get the variant assigned to a user (without incrementing visitors)."""
        return self._assignments.get(f"{exp_id}:{user_id}")

    def conversion_rate(self, exp_id: str, variant_name: str) -> float:
        """Calculate conversion rate for a variant."""
        exp = self.experiments.get(exp_id)
        if not exp:
            return 0.0
        variant = exp.variants.get(variant_name)
        if not variant or variant.visitors == 0:
            return 0.0
        return variant.conversions / variant.visitors * 100

    def z_score(self, exp_id: str) -> Optional[float]:
        """Calculate z-score between control and best performing variant."""
        exp = self.experiments.get(exp_id)
        if not exp:
            return None
        control = exp.variants.get(exp.control_variant)
        if not control or control.visitors == 0:
            return None

        best_variant = max(exp.variants.values(), key=lambda v: self.conversion_rate(exp_id, v.name))
        if best_variant.name == exp.control_variant or best_variant.visitors == 0:
            return 0.0

        p1 = control.conversions / control.visitors
        p2 = best_variant.conversions / best_variant.visitors
        n1, n2 = control.visitors, best_variant.visitors

        pooled_p = (control.conversions + best_variant.conversions) / (n1 + n2)
        se = math.sqrt(pooled_p * (1 - pooled_p) * (1/n1 + 1/n2))

        if se == 0:
            return 0.0
        return (p2 - p1) / se

    def is_significant(self, exp_id: str) -> bool:
        """Check if results are statistically significant (p < 0.05, two-tailed)."""
        z = self.z_score(exp_id)
        if z is None:
            return False
        return abs(z) > 1.96  # 95% confidence, two-tailed

    def results(self, exp_id: str) -> Dict:
        """Get experiment results summary."""
        exp = self.experiments.get(exp_id)
        if not exp:
            return {}
        z = self.z_score(exp_id)
        return {
            "experiment": exp.name,
            "status": exp.status.value,
            "variants": {
                v.name: {
                    "visitors": v.visitors,
                    "conversions": v.conversions,
                    "conversion_rate": f"{self.conversion_rate(exp_id, v.name):.2f}%",
                    "revenue": v.revenue,
                }
                for v in exp.variants.values()
            },
            "z_score": round(z, 4) if z is not None else None,
            "is_significant": self.is_significant(exp_id),
            "total_visitors": sum(v.visitors for v in exp.variants.values()),
            "total_conversions": sum(v.conversions for v in exp.variants.values()),
        }

    def set_weights(self, exp_id: str, weights: Dict[str, float]):
        """Update variant traffic weights."""
        exp = self.experiments.get(exp_id)
        if exp:
            for vname, weight in weights.items():
                if vname in exp.variants:
                    exp.variants[vname].weight = weight

    def stats(self) -> Dict:
        return {
            "total_experiments": len(self.experiments),
            "running": sum(1 for e in self.experiments.values() if e.status == ExperimentStatus.RUNNING),
            "completed": sum(1 for e in self.experiments.values() if e.status == ExperimentStatus.COMPLETED),
        }

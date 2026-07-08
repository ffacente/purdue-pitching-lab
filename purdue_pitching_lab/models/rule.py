"""Rule models for the player development engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Operator = Literal[">", ">=", "<", "<=", "=="]
Status = Literal["red", "yellow", "green"]


@dataclass(frozen=True)
class Rule:
    """Represents a recommendation rule evaluated against a metric."""

    metric: str
    operator: Operator
    threshold: float
    priority: int
    recommendation: str
    status: Status


DEFAULT_RULES = [
    Rule(
        metric="ops",
        operator=">=",
        threshold=0.9,
        priority=1,
        recommendation=(
            "Opposing hitters are averaging an alarming {value:.3f} OPS against "
            "your {pitch_type}. Adjust design shape or restrict deployment zones."
        ),
        status="red",
    ),
    Rule(
        metric="whiff_pct",
        operator=">=",
        threshold=0.32,
        priority=2,
        recommendation=(
            "Your {pitch_type} holds an elite {value:.1%} Whiff Rate, but is thrown "
            "under 15% of the time in {count_group}. Elevate its usage to expand "
            "strikeout efficiency."
        ),
        status="yellow",
    ),
    Rule(
        metric="baa",
        operator="<=",
        threshold=0.18,
        priority=3,
        recommendation=(
            "Your {pitch_type} completely stymies {split_label}, holding them to a "
            "pristine {value:.3f} BAA. Maintain as your anchor tool."
        ),
        status="green",
    ),
]
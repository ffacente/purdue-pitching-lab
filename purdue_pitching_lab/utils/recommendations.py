"""Recommendation engines for development and arsenal optimization."""

from __future__ import annotations

import operator

import pandas as pd

from models.rule import DEFAULT_RULES, Rule
from utils.metrics import summarize_by_group


EXCLUDED_SPECIAL_PITCH_TYPES = {"other", "undefined"}


def _exclude_special_pitch_types(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Remove non-actionable pitch labels from optimization workflows."""

    if dataframe.empty or "pitch_type" not in dataframe.columns:
        return dataframe
    return dataframe.loc[
        ~dataframe["pitch_type"].astype(str).str.strip().str.lower().isin(EXCLUDED_SPECIAL_PITCH_TYPES)
    ].copy()

OPERATORS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
}


def evaluate_rules(
    summary: pd.DataFrame,
    split_label: str = "hitters",
    count_group: str = "the current count state",
) -> list[dict[str, str]]:
    """Evaluate the default rulebook against per-pitch summaries."""

    cards: list[dict[str, str]] = []
    if summary.empty:
        return cards

    for _, row in summary.iterrows():
        for rule in sorted(DEFAULT_RULES, key=lambda value: value.priority):
            metric_value = float(row.get(rule.metric, 0.0))
            if rule.metric == "whiff_pct" and row.get("usage_pct", 1.0) >= 0.15:
                continue
            if OPERATORS[rule.operator](metric_value, rule.threshold):
                cards.append(
                    {
                        "status": rule.status,
                        "title": row.get("pitch_type", "Pitch Development"),
                        "body": rule.recommendation.format(
                            value=metric_value,
                            pitch_type=row.get("pitch_type", "pitch"),
                            split_label=split_label,
                            count_group=count_group,
                        ),
                    }
                )
                break
    return cards


def arsenal_optimization_summary(dataframe: pd.DataFrame) -> dict[str, str]:
    """Compute coach-facing arsenal optimization answers."""

    dataframe = _exclude_special_pitch_types(dataframe)
    if dataframe.empty:
        return {}

    pitch_summary = summarize_by_group(dataframe, ("pitch_type",))
    lhh_summary = summarize_by_group(dataframe.loc[dataframe["batter_side"] == "Left"], ("pitch_type",))
    rhh_summary = summarize_by_group(dataframe.loc[dataframe["batter_side"] == "Right"], ("pitch_type",))
    ahead_summary = summarize_by_group(dataframe.loc[dataframe["count_group"] == "Ahead"], ("pitch_type",))
    zero_zero_summary = summarize_by_group(dataframe.loc[dataframe["count_group"] == "0-0"], ("pitch_type",))

    def best_row(summary: pd.DataFrame, metric: str, ascending: bool) -> pd.Series | None:
        if summary.empty or metric not in summary.columns:
            return None
        return summary.sort_values(metric, ascending=ascending).iloc[0]

    answers = {
        "Best pitch vs LHH": _describe_row(best_row(lhh_summary, "baa", True), "lowest BAA vs left-handed hitters"),
        "Best pitch vs RHH": _describe_row(best_row(rhh_summary, "baa", True), "lowest BAA vs right-handed hitters"),
        "Best 2-Strike weapon": _describe_row(best_row(ahead_summary, "whiff_pct", False), "best whiff profile when ahead"),
        "Best early-count strike-getter": _describe_row(best_row(zero_zero_summary, "ops", True), "strongest 0-0 results"),
        "Most underutilized asset": _describe_row(best_row(pitch_summary.loc[pitch_summary["usage_pct"] < 0.15], "whiff_pct", False), "elite whiff rate with low usage"),
        "Most overused pitch": _describe_row(best_row(pitch_summary, "usage_pct", False), "largest usage share"),
        "Most damaged pitch type": _describe_row(best_row(pitch_summary, "ops", False), "highest OPS allowed"),
    }
    return answers


def _describe_row(row: pd.Series | None, rationale: str) -> str:
    if row is None or row.empty:
        return "No qualifying sample."
    return f"{row['pitch_type']} ({rationale}; sample {int(row['sample_size'])})"
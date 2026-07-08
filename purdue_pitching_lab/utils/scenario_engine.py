"""Bullpen scenario scoring and ranking engine."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.filters import FilterState, apply_filters
from utils.metrics import summarize_by_group


def _min_max_scale(series: pd.Series, invert: bool = False) -> pd.Series:
    values = series.fillna(0.0).astype(float)
    minimum = values.min()
    maximum = values.max()
    if minimum == maximum:
        scaled = pd.Series([0.5] * len(values), index=values.index)
    else:
        scaled = (values - minimum) / (maximum - minimum)
    return 1 - scaled if invert else scaled


@st.cache_data(show_spinner=False)
def build_scenario_leaderboard(dataframe: pd.DataFrame, filters: FilterState) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rank pitchers for a specific scenario using the weighted success score."""

    filtered = apply_filters(dataframe, filters)
    summary = summarize_by_group(filtered, ("pitcher",))
    if summary.empty:
        empty = pd.DataFrame(columns=["pitcher", "scenario_score", "tag", "sample_size"])
        return empty, empty

    sampled = summary.loc[summary["sample_size"] >= 5].copy()
    unsampled = summary.loc[summary["sample_size"] < 5].copy()
    if sampled.empty:
        unsampled["tag"] = "Insufficient sample"
        unsampled["scenario_score"] = 0.0
        return sampled, unsampled

    sampled["ops_component"] = _min_max_scale(sampled["ops"], invert=True)
    sampled["whiff_component"] = _min_max_scale(sampled["whiff_pct"])
    sampled["hard_hit_component"] = _min_max_scale(sampled["hard_hit_pct"], invert=True)
    sampled["ground_ball_component"] = _min_max_scale(sampled["ground_ball_pct"])
    sampled["scenario_score"] = 100 * (
        (0.40 * sampled["ops_component"])
        + (0.30 * sampled["whiff_component"])
        + (0.20 * sampled["hard_hit_component"])
        + (0.10 * sampled["ground_ball_component"])
    )
    sampled["tag"] = sampled.apply(_tag_pitcher, axis=1)
    unsampled["tag"] = "Insufficient sample"
    unsampled["scenario_score"] = 0.0
    return (
        sampled.sort_values("scenario_score", ascending=False).reset_index(drop=True),
        unsampled.sort_values("sample_size", ascending=False).reset_index(drop=True),
    )


def _tag_pitcher(row: pd.Series) -> str:
    components = {
        "groundball profile": row["ground_ball_component"],
        "whiff profile": row["whiff_component"],
        "run prevention": row["ops_component"],
        "contact suppression": row["hard_hit_component"],
    }
    best_trait = max(components, key=components.get)
    return f"Highest structural {best_trait} in this scenario"
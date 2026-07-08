"""Metric calculations and cached aggregations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
import streamlit as st

from utils.helpers import log_timing


@dataclass(frozen=True)
class MetricSpec:
    """Metadata for a registered metric."""

    label: str
    description: str
    kind: str


METRIC_REGISTRY = {
    "baa": MetricSpec("BAA", "Batting Average Against", "avg"),
    "obp": MetricSpec("OBP", "On Base Percentage", "avg"),
    "slg": MetricSpec("SLG", "Slugging Percentage", "avg"),
    "ops": MetricSpec("OPS", "On-Base Plus Slugging", "avg"),
    "whiff_pct": MetricSpec("Whiff %", "Swinging strikes divided by total swings", "pct"),
    "hard_hit_pct": MetricSpec("Hard-Hit %", "Balls in play hit 95+ mph", "pct"),
    "ground_ball_pct": MetricSpec("Ground Ball %", "Ground balls divided by total balls in play", "pct"),
    "line_drive_pct": MetricSpec("Line Drive %", "Line drives divided by total balls in play", "pct"),
    "fly_ball_pct": MetricSpec("Fly Ball %", "Fly balls divided by total balls in play", "pct"),
}


def _safe_divide(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def _lower(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.lower()


def _terminal_pitches(dataframe: pd.DataFrame) -> pd.DataFrame:
    if "is_terminal_pitch" not in dataframe.columns:
        return dataframe
    return dataframe.loc[dataframe["is_terminal_pitch"]].copy()


def _event_counts(dataframe: pd.DataFrame) -> dict[str, float]:
    terminal = _terminal_pitches(dataframe)
    play_result = _lower(terminal.get("play_result", pd.Series(index=terminal.index, dtype=str)))
    pitch_call = _lower(terminal.get("pitch_call", pd.Series(index=terminal.index, dtype=str)))
    kor_bb = _lower(terminal.get("kor_bb", pd.Series(index=terminal.index, dtype=str)))
    hit_type = _lower(dataframe.get("batted_ball_type", pd.Series(index=dataframe.index, dtype=str)))

    hits = play_result.isin(["single", "double", "triple", "homerun", "home run", "home_run"]).sum()
    walks = kor_bb.eq("walk").sum()
    hbp = pitch_call.eq("hitbypitch").sum()
    sacrifice_flies = ((play_result.str.contains("sacrifice")) & (hit_type.reindex(terminal.index).str.contains("fly|pop"))).sum()
    at_bats = len(terminal) - walks - hbp - sacrifice_flies
    total_bases = (
        play_result.eq("single").sum()
        + (play_result.eq("double").sum() * 2)
        + (play_result.eq("triple").sum() * 3)
        + (play_result.isin(["homerun", "home run", "home_run"]).sum() * 4)
    )

    pitch_call_all = _lower(dataframe.get("pitch_call", pd.Series(index=dataframe.index, dtype=str)))
    swing_mask = pitch_call_all.str.contains("swing|foul|inplay")
    whiff_mask = pitch_call_all.eq("strikeswinging")
    in_play_mask = pitch_call_all.str.contains("inplay") | hit_type.str.contains("ground|line|fly|pop")
    exit_velocity = pd.to_numeric(dataframe.get("exit_velocity", pd.Series(index=dataframe.index, dtype=float)), errors="coerce")
    hard_hit_mask = in_play_mask & exit_velocity.ge(95)

    return {
        "hits": float(hits),
        "walks": float(walks),
        "hbp": float(hbp),
        "sacrifice_flies": float(sacrifice_flies),
        "at_bats": float(max(at_bats, 0)),
        "total_bases": float(total_bases),
        "swings": float(swing_mask.sum()),
        "whiffs": float(whiff_mask.sum()),
        "balls_in_play": float(in_play_mask.sum()),
        "hard_hit": float(hard_hit_mask.sum()),
        "ground_balls": float(hit_type.str.contains("ground").sum()),
        "line_drives": float(hit_type.str.contains("line").sum()),
        "fly_balls": float(hit_type.str.contains("fly|pop").sum()),
        "plate_appearances": float(len(terminal)),
    }


def calculate_metrics(dataframe: pd.DataFrame) -> dict[str, float]:
    """Calculate the core required metrics for a filtered dataframe."""

    counts = _event_counts(dataframe)
    baa = _safe_divide(counts["hits"], counts["at_bats"])
    obp = _safe_divide(
        counts["hits"] + counts["walks"] + counts["hbp"],
        counts["at_bats"] + counts["walks"] + counts["hbp"] + counts["sacrifice_flies"],
    )
    slg = _safe_divide(counts["total_bases"], counts["at_bats"])
    ops = obp + slg
    whiff_pct = _safe_divide(counts["whiffs"], counts["swings"])
    hard_hit_pct = _safe_divide(counts["hard_hit"], counts["balls_in_play"])
    ground_ball_pct = _safe_divide(counts["ground_balls"], counts["balls_in_play"])
    line_drive_pct = _safe_divide(counts["line_drives"], counts["balls_in_play"])
    fly_ball_pct = _safe_divide(counts["fly_balls"], counts["balls_in_play"])
    return {
        **counts,
        "baa": baa,
        "obp": obp,
        "slg": slg,
        "ops": ops,
        "whiff_pct": whiff_pct,
        "hard_hit_pct": hard_hit_pct,
        "ground_ball_pct": ground_ball_pct,
        "line_drive_pct": line_drive_pct,
        "fly_ball_pct": fly_ball_pct,
    }


@st.cache_data(show_spinner=False)
def summarize_by_group(dataframe: pd.DataFrame, group_columns: tuple[str, ...]) -> pd.DataFrame:
    """Aggregate metrics for each group in the dataframe."""

    with log_timing("summarize_by_group", group_columns=group_columns):
        if dataframe.empty:
            return pd.DataFrame(columns=[*group_columns, *METRIC_REGISTRY.keys(), "sample_size"])

        rows: list[dict[str, float | str]] = []
        for group_key, frame in dataframe.groupby(list(group_columns), dropna=False):
            key_values = group_key if isinstance(group_key, tuple) else (group_key,)
            record = dict(zip(group_columns, key_values, strict=True))
            metrics = calculate_metrics(frame)
            record.update(metrics)
            record["sample_size"] = len(frame)
            if "pitch_type" in group_columns and "pitch_type" in dataframe.columns:
                record["usage_pct"] = len(frame) / max(len(dataframe), 1)
            rows.append(record)

        summary = pd.DataFrame(rows)
        return summary.sort_values("sample_size", ascending=False).reset_index(drop=True)


def leaderboard_metric(dataframe: pd.DataFrame, group_column: str, metric_name: str) -> pd.DataFrame:
    """Return a sorted leaderboard for a single metric."""

    summary = summarize_by_group(dataframe, (group_column,))
    ascending = metric_name in {"ops", "baa", "obp", "slg", "hard_hit_pct"}
    if metric_name not in summary.columns:
        return pd.DataFrame(columns=[group_column, metric_name, "sample_size"])
    return summary[[group_column, metric_name, "sample_size"]].sort_values(metric_name, ascending=ascending)


def metric_columns() -> list[str]:
    """Return the registered metric column names."""

    return list(METRIC_REGISTRY.keys())
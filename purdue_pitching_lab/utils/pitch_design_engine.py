"""Pitch design analysis and clustering utilities."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from models.thresholds import PITCH_CLUSTER_THRESHOLDS, PROGRAM_BENCHMARKS
from utils.metrics import summarize_by_group


EXCLUDED_SPECIAL_PITCH_TYPES = {"other", "undefined"}


def _exclude_special_pitch_types(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Remove non-actionable pitch labels from design workflows."""

    if dataframe.empty or "pitch_type" not in dataframe.columns:
        return dataframe
    return dataframe.loc[
        ~dataframe["pitch_type"].astype(str).str.strip().str.lower().isin(EXCLUDED_SPECIAL_PITCH_TYPES)
    ].copy()


def classify_pitch_cluster(row: pd.Series) -> str:
    """Assign a movement-based pitch cluster label."""

    velocity = float(row.get("velocity", 0.0))
    ivb = float(row.get("induced_vertical_break", 0.0))
    hb = float(row.get("horizontal_break", 0.0))
    pitch_type = str(row.get("pitch_type", ""))

    if "change" in pitch_type.lower() and ivb >= 12:
        return "Vertical Changeup"
    if hb >= 12 and ivb <= 12:
        return "Sinker"
    if velocity >= 92 and ivb >= 14:
        return "Power Fastball"
    if velocity >= 88 and ivb >= 17:
        return "Ride Fastball"
    if hb >= 12:
        return "Running Fastball"
    if hb <= -14 and ivb <= 2:
        return "Sweeper"
    if -8 <= hb <= -2 and ivb <= 1:
        return "Gyro Slider"
    if velocity >= 84 and hb <= -8 and ivb <= 2:
        return "Power Slider"
    if hb <= -8 and ivb <= -5:
        return "Slurve"
    return pitch_type or "Unknown"


@st.cache_data(show_spinner=False)
def build_pitch_design_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Aggregate pitch design summaries by pitcher and pitch type."""

    dataframe = _exclude_special_pitch_types(dataframe)
    required = {"pitcher", "pitch_type", "velocity", "induced_vertical_break", "horizontal_break"}
    if dataframe.empty or not required.issubset(dataframe.columns):
        return pd.DataFrame()
    summary = dataframe.groupby(["pitcher", "pitch_type"], dropna=False).agg(
        velocity=("velocity", "mean"),
        max_velocity=("velocity", "max"),
        spin_rate=("spin_rate", "mean"),
        induced_vertical_break=("induced_vertical_break", "mean"),
        horizontal_break=("horizontal_break", "mean"),
        sample_size=("pitch_type", "size"),
    ).reset_index()
    summary["cluster"] = summary.apply(classify_pitch_cluster, axis=1)
    return summary


def compare_to_staff(summary: pd.DataFrame, pitcher_name: str) -> pd.DataFrame:
    """Compare a pitcher's pitch shapes against staff averages and program targets."""

    if summary.empty:
        return pd.DataFrame()
    pitcher_rows = summary.loc[summary["pitcher"] == pitcher_name].copy()
    staff_rows = summary.loc[summary["pitcher"] != pitcher_name].copy()
    if pitcher_rows.empty:
        return pd.DataFrame()

    staff_means = staff_rows.groupby("pitch_type").agg(
        staff_velocity=("velocity", "mean"),
        staff_ivb=("induced_vertical_break", "mean"),
        staff_hb=("horizontal_break", "mean"),
        staff_spin=("spin_rate", "mean"),
    )
    comparison = pitcher_rows.merge(staff_means, on="pitch_type", how="left")
    comparison["benchmark_velocity"] = comparison["pitch_type"].map(lambda value: PROGRAM_BENCHMARKS.get(value, PROGRAM_BENCHMARKS.get("Fastball")).velocity)
    comparison["benchmark_ivb"] = comparison["pitch_type"].map(lambda value: PROGRAM_BENCHMARKS.get(value, PROGRAM_BENCHMARKS.get("Fastball")).induced_vertical_break)
    comparison["benchmark_hb"] = comparison["pitch_type"].map(lambda value: PROGRAM_BENCHMARKS.get(value, PROGRAM_BENCHMARKS.get("Fastball")).horizontal_break)
    comparison["benchmark_spin"] = comparison["pitch_type"].map(lambda value: PROGRAM_BENCHMARKS.get(value, PROGRAM_BENCHMARKS.get("Fastball")).spin_rate)
    return comparison


def build_pitch_design_notes(comparison: pd.DataFrame) -> list[str]:
    """Generate coach-facing pitch design notes."""

    scored_notes: list[tuple[float, str]] = []
    if comparison.empty:
        return ["No pitch design sample is available for the selected pitcher."]

    for _, row in comparison.iterrows():
        separation = row["max_velocity"] - row["velocity"]
        velocity_gap = row["benchmark_velocity"] - row["velocity"]
        movement_gap = abs(row["horizontal_break"] - row["benchmark_hb"])
        separation_gap = 1.0 - separation

        if velocity_gap > 1.0:
            scored_notes.append(
                (
                    float(velocity_gap),
                    f"{row['pitch_type']}: velocity trails the Division I benchmark; pursue intent or force-production gains.",
                )
            )
        if movement_gap > 4:
            scored_notes.append(
                (
                    float(movement_gap),
                    f"{row['pitch_type']}: movement shape drifts from Division I geometry, creating alignment inefficiency.",
                )
            )
        if separation_gap > 0:
            scored_notes.append(
                (
                    float(separation_gap),
                    f"{row['pitch_type']}: max velocity ceiling is compressed, suggesting limited explosive margin.",
                )
            )

    if not scored_notes:
        return ["Current pitch shapes align cleanly with Division I benchmark expectations."]

    top_notes: list[str] = []
    seen: set[str] = set()
    for _, note in sorted(scored_notes, key=lambda item: item[0], reverse=True):
        if note in seen:
            continue
        seen.add(note)
        top_notes.append(note)
        if len(top_notes) == 3:
            break
    return top_notes
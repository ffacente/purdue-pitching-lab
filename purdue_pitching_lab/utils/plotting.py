"""Plotly chart factories for the Purdue Pitching Lab."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import PURDUE_COLORS


EXCLUDED_PITCH_TYPES = {"", "unknown", "other", "undefined"}


def _filter_actionable_pitch_types(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty or "pitch_type" not in dataframe.columns:
        return dataframe
    return dataframe.loc[
        ~dataframe["pitch_type"].fillna("").astype(str).str.strip().str.lower().isin(EXCLUDED_PITCH_TYPES)
    ].copy()


def usage_treemap(dataframe: pd.DataFrame) -> go.Figure | None:
    """Build a pitch usage treemap."""

    if dataframe.empty or "pitch_type" not in dataframe.columns:
        return None
    dataframe = _filter_actionable_pitch_types(dataframe)
    if dataframe.empty:
        return None
    usage = dataframe["pitch_type"].value_counts().reset_index()
    usage.columns = ["pitch_type", "count"]
    usage["usage_pct"] = usage["count"] / usage["count"].sum()
    figure = px.treemap(
        usage,
        path=["pitch_type"],
        values="count",
        color="usage_pct",
        color_continuous_scale=[[0, "#E2E8F0"], [1, PURDUE_COLORS["gold"]]],
    )
    figure.update_traces(
        texttemplate="%{label}<br>%{percentRoot:.1%}",
        hovertemplate="Pitch: %{label}<br>Count: %{value}<br>Usage: %{percentRoot:.1%}<extra></extra>",
    )
    figure.update_layout(margin=dict(t=20, l=10, r=10, b=10))
    return figure


def movement_scatter(dataframe: pd.DataFrame) -> go.Figure | None:
    """Build the HB vs IVB movement plot."""

    required = {"horizontal_break", "induced_vertical_break", "pitch_type"}
    if dataframe.empty or not required.issubset(dataframe.columns):
        return None
    dataframe = _filter_actionable_pitch_types(dataframe)
    if dataframe.empty:
        return None
    figure = px.scatter(
        dataframe,
        x="horizontal_break",
        y="induced_vertical_break",
        color="pitch_type",
        hover_data=[col for col in ["velocity", "spin_rate"] if col in dataframe.columns],
        opacity=0.7,
    )
    figure.add_hline(y=0, line_dash="dash", line_color=PURDUE_COLORS["slate"])
    figure.add_vline(x=0, line_dash="dash", line_color=PURDUE_COLORS["slate"])
    figure.update_layout(xaxis_title="Horizontal Break", yaxis_title="Induced Vertical Break")
    return figure


def distribution_histogram(dataframe: pd.DataFrame, column: str, title: str) -> go.Figure | None:
    """Build a histogram for a numeric column."""

    if dataframe.empty or column not in dataframe.columns:
        return None
    histogram_df = dataframe.dropna(subset=[column])
    if "pitch_type" in histogram_df.columns:
        histogram_df = _filter_actionable_pitch_types(histogram_df)
    if histogram_df.empty:
        return None
    figure = px.histogram(
        histogram_df,
        x=column,
        color="pitch_type" if "pitch_type" in dataframe.columns else None,
        barmode="overlay",
        opacity=0.75,
        marginal="box",
        title=title,
    )
    figure.update_layout(margin=dict(t=50, l=10, r=10, b=10))
    return figure


def leaderboard_bar(dataframe: pd.DataFrame, x: str, y: str, title: str) -> go.Figure | None:
    """Build a horizontal leaderboard chart."""

    if dataframe.empty or x not in dataframe.columns or y not in dataframe.columns:
        return None
    figure = px.bar(
        dataframe,
        x=x,
        y=y,
        orientation="h",
        title=title,
        color=x,
        color_continuous_scale=[[0, PURDUE_COLORS["gold"]], [1, PURDUE_COLORS["black"]]],
    )
    figure.update_layout(showlegend=False, margin=dict(t=50, l=10, r=10, b=10))
    return figure


def velocity_boxplot(dataframe: pd.DataFrame) -> go.Figure | None:
    """Build a roster-wide velocity boxplot."""

    if dataframe.empty or not {"pitcher", "velocity"}.issubset(dataframe.columns):
        return None
    return px.box(dataframe, x="pitcher", y="velocity", color="pitcher", points=False, title="Roster Velocity Spread")
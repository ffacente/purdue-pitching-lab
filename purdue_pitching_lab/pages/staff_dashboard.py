"""Staff dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.data_loader import filter_target_pitchers
from utils.metrics import leaderboard_metric, summarize_by_group
from utils.plotting import leaderboard_bar, usage_treemap, velocity_boxplot


def render() -> None:
    """Render the staff dashboard."""

    bundle = st.session_state["dataset_bundle"]
    roster_df = filter_target_pitchers(bundle.dataframe)
    st.title("Staff Dashboard & Team Analytics")

    chart_columns = st.columns(2)
    pitch_distribution = usage_treemap(roster_df)
    if pitch_distribution:
        chart_columns[0].plotly_chart(pitch_distribution, use_container_width=True)
    else:
        chart_columns[0].info("Team pitch distribution is unavailable because pitch type data is missing.")

    velocity_figure = velocity_boxplot(roster_df)
    if velocity_figure:
        chart_columns[1].plotly_chart(velocity_figure, use_container_width=True)
    else:
        chart_columns[1].info("Roster velocity spread is unavailable because velocity data is missing.")

    leaderboard_columns = st.columns(3)
    _render_leaderboard(leaderboard_columns[0], roster_df, "whiff_pct", "Whiff % Leaders")
    _render_leaderboard(leaderboard_columns[1], roster_df, "ops", "Low OPS Leaders")
    _render_leaderboard(leaderboard_columns[2], roster_df, "hard_hit_pct", "Hard-Hit Avoidance")

    st.subheader("Pitch-Shape Leaderboards")
    pitch_shape_board = _pitch_shape_leaderboards(roster_df)
    st.dataframe(pitch_shape_board, use_container_width=True, hide_index=True)

    st.subheader("Open Player Profile")
    for pitcher_name in sorted(roster_df["pitcher"].dropna().unique())[:12]:
        if st.button(f"Open {pitcher_name}", key=f"staff_{pitcher_name}"):
            st.session_state["selected_pitcher"] = pitcher_name
            st.session_state["pending_nav_page"] = "player_profile"
            st.rerun()


def _render_leaderboard(container: st.delta_generator.DeltaGenerator, dataframe: pd.DataFrame, metric_name: str, title: str) -> None:
    leaderboard = leaderboard_metric(dataframe, "pitcher", metric_name).head(10)
    figure = leaderboard_bar(leaderboard, metric_name, "pitcher", title)
    if figure:
        container.plotly_chart(figure, use_container_width=True)
    else:
        container.info(f"{title} is unavailable for the current dataset.")


def _pitch_shape_leaderboards(dataframe: pd.DataFrame) -> pd.DataFrame:
    required = {"pitcher", "pitch_type", "induced_vertical_break", "horizontal_break", "velocity"}
    if not required.issubset(dataframe.columns):
        return pd.DataFrame()

    summary = dataframe.groupby(["pitcher", "pitch_type"], dropna=False).agg(
        ivb=("induced_vertical_break", "mean"),
        hb=("horizontal_break", "mean"),
        velocity=("velocity", "mean"),
    ).reset_index()
    fastball = summary.loc[summary["pitch_type"].str.contains("fast", case=False, na=False)]
    slider = summary.loc[summary["pitch_type"].str.contains("slider", case=False, na=False)]
    changeup = summary.loc[summary["pitch_type"].str.contains("change", case=False, na=False)]
    changeup = changeup.assign(velo_separation=changeup["velocity"].map(lambda value: summary["velocity"].max() - value))
    boards = [
        fastball.nlargest(5, "ivb").assign(metric="Fastball IVB Ride"),
        slider.nsmallest(5, "hb").assign(metric="Slider Break"),
        changeup.nlargest(5, "velo_separation").assign(metric="Changeup Velo Separation"),
    ]
    return pd.concat(boards, ignore_index=True)[["metric", "pitcher", "pitch_type", "ivb", "hb", "velocity"]]
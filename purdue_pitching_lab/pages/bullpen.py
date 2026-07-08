"""Bullpen live scenario matcher page."""

from __future__ import annotations

import streamlit as st

from utils.data_loader import filter_target_pitchers
from utils.filters import FilterState, get_filter_options
from utils.page_bootstrap import bootstrap_page
from utils.scenario_engine import build_scenario_leaderboard


def render() -> None:
    """Render the bullpen scenario matcher page."""

    bundle = st.session_state["dataset_bundle"]
    roster_df = filter_target_pitchers(bundle.dataframe)
    options = get_filter_options(roster_df)

    st.title("Bullpen Live Scenario Matcher")
    st.caption("Score formula: 0.40 x inverted OPS + 0.30 x Whiff % + 0.20 x inverted Hard-Hit % + 0.10 x Ground Ball %")

    with st.sidebar:
        st.subheader("Bullpen Scenario")
        batter_side = st.selectbox("Facing", options=["", *options.get("batter_side", [])], index=0)
        outs = st.selectbox("Outs", options=["", *options.get("outs", [])], index=0)
        count_group = st.selectbox("Count Group", options=["", *options.get("count_group", [])], index=0)

    filters = FilterState(
        batter_sides=(batter_side,) if batter_side else (),
        outs=(int(outs),) if outs else (),
        count_groups=(count_group,) if count_group else (),
    )
    ranked, unsampled = build_scenario_leaderboard(roster_df, filters)

    if ranked.empty and unsampled.empty:
        st.info("No pitchers matched the selected scenario.")
        return

    st.subheader("Ranked Recommendations")
    for index, row in ranked.iterrows():
        st.write(f"#{index + 1}: {row['pitcher']} — {row['tag']} (Score: {row['scenario_score']:.1f})")
    if not ranked.empty:
        st.dataframe(ranked[["pitcher", "scenario_score", "ops", "whiff_pct", "hard_hit_pct", "ground_ball_pct", "sample_size", "tag"]], use_container_width=True, hide_index=True)

    if not unsampled.empty:
        st.subheader("Insufficient Sample")
        st.dataframe(unsampled[["pitcher", "sample_size", "tag"]], use_container_width=True, hide_index=True)


if __name__ == "__main__":
    bootstrap_page("bullpen")
    render()
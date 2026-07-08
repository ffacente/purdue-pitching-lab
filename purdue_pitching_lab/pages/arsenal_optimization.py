"""Arsenal optimization page."""

from __future__ import annotations

import streamlit as st

from utils.data_loader import filter_target_pitchers
from utils.metrics import summarize_by_group
from utils.page_bootstrap import bootstrap_page
from utils.recommendations import arsenal_optimization_summary


def render() -> None:
    """Render the arsenal optimization page."""

    bundle = st.session_state["dataset_bundle"]
    pitcher_name = st.session_state.get("selected_pitcher")
    if not pitcher_name:
        st.info("Select a pitcher to compute arsenal optimization outputs.")
        return

    roster_df = filter_target_pitchers(bundle.dataframe)
    pitcher_df = roster_df.loc[roster_df["pitcher"] == pitcher_name].copy()
    st.title("Arsenal Optimization Engine")
    st.caption(f"Algorithmic pitch-usage answers for {pitcher_name}")

    if pitcher_df.empty:
        st.warning("The selected pitcher is not in the current Purdue-only dataset slice.")
        return

    answers = arsenal_optimization_summary(pitcher_df)
    for label, value in answers.items():
        st.markdown(f"**{label}:** {value}")

    actionable_pitch_df = pitcher_df.loc[
        ~pitcher_df["pitch_type"].astype(str).str.strip().str.lower().isin({"other", "undefined"})
    ].copy()
    summary = summarize_by_group(actionable_pitch_df, ("pitch_type",))
    if not summary.empty:
        st.subheader("Pitch Matrix")
        st.dataframe(summary, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    bootstrap_page("arsenal_optimization")
    render()
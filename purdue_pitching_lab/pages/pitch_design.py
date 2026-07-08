"""Pitch design page."""

from __future__ import annotations

import streamlit as st

from utils.data_loader import filter_target_pitchers
from utils.helpers import dataframe_to_excel_bytes, export_filename
from utils.page_bootstrap import bootstrap_page
from utils.pitch_design_engine import build_pitch_design_notes, build_pitch_design_table, compare_to_staff


def render() -> None:
    """Render the pitch design lab page."""

    bundle = st.session_state["dataset_bundle"]
    pitcher_name = st.session_state.get("selected_pitcher")
    if not pitcher_name:
        st.info("Select a pitcher to evaluate pitch design profiles.")
        return

    st.title("Pitch Design Lab & Cluster Classification")
    if "Level" in bundle.dataframe.columns:
        d1_dataframe = bundle.dataframe.loc[
            bundle.dataframe["Level"].astype(str).str.strip().eq("D1")
        ].copy()
    else:
        d1_dataframe = bundle.dataframe.copy()
    summary = build_pitch_design_table(d1_dataframe)
    comparison = compare_to_staff(summary, pitcher_name)

    if comparison.empty:
        st.info("Pitch design comparisons are unavailable for the selected pitcher.")
        return

    st.caption("Benchmarks compare the selected pitcher against all Division I pitchers in the dataset.")

    st.dataframe(comparison, use_container_width=True, hide_index=True)
    st.download_button(
        "Download Pitch Design Workbook",
        data=dataframe_to_excel_bytes(comparison),
        file_name=export_filename("pitch_design", "xlsx"),
        use_container_width=True,
    )

    st.subheader("Coaching Notes")
    for note in build_pitch_design_notes(comparison):
        st.write(f"- {note}")


if __name__ == "__main__":
    bootstrap_page("pitch_design")
    render()
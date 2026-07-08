"""Automated player development engine page."""

from __future__ import annotations

import streamlit as st

from utils.data_loader import filter_target_pitchers
from utils.helpers import build_pdf_report, export_filename
from utils.metrics import summarize_by_group
from utils.page_bootstrap import bootstrap_page
from utils.recommendations import evaluate_rules


def _exclude_undefined_pitch_types(dataframe):
    """Remove Undefined pitches from development outputs."""

    if dataframe.empty or "pitch_type" not in dataframe.columns:
        return dataframe
    return dataframe.loc[
        dataframe["pitch_type"].astype(str).str.strip().str.lower().ne("undefined")
    ].copy()


def render() -> None:
    """Render the development engine page."""

    bundle = st.session_state["dataset_bundle"]
    pitcher_name = st.session_state.get("selected_pitcher")
    if not pitcher_name:
        st.info("Select a pitcher from the home page or player profile to unlock development recommendations.")
        return

    roster_df = filter_target_pitchers(bundle.dataframe)
    pitcher_df = roster_df.loc[roster_df["pitcher"] == pitcher_name].copy()
    st.title("Automated Player Development Engine")
    st.caption(f"Rule-based development guidance for {pitcher_name}")

    if pitcher_df.empty:
        st.warning("The selected pitcher is not in the current Purdue-only dataset slice.")
        return

    development_df = _exclude_undefined_pitch_types(pitcher_df)
    summary = summarize_by_group(development_df, ("pitch_type",))
    cards = evaluate_rules(summary)
    if not cards:
        st.info("No recommendation cards were triggered by the current sample.")
    for card in cards:
        st.markdown(
            f'<div class="status-card status-{card["status"]}"><strong>{card["title"]}</strong><br>{card["body"]}</div>',
            unsafe_allow_html=True,
        )

    st.subheader("Underlying pitch summary")
    st.dataframe(summary, use_container_width=True, hide_index=True)

    report_sections = [
        ("Current Performance Snapshot", f"{pitcher_name} generated {len(cards)} active development cards."),
        ("Development Recommendations", "\n".join(card["body"] for card in cards) or "No triggered recommendations."),
    ]
    st.download_button(
        "Download PDF Report",
        data=build_pdf_report(f"{pitcher_name} Development Report", report_sections),
        file_name=export_filename("development_report", "pdf"),
        use_container_width=True,
    )


if __name__ == "__main__":
    bootstrap_page("development")
    render()
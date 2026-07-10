"""Home page for the Purdue Pitching Lab."""

from __future__ import annotations

import streamlit as st

from utils.data_loader import dataset_health, filter_target_pitchers
from utils.page_bootstrap import bootstrap_page


def render() -> None:
    """Render the home page."""

    bundle = st.session_state["dataset_bundle"]
    dataframe = filter_target_pitchers(bundle.dataframe)
    health = dataset_health(bundle)

    st.markdown("# Purdue Pitching Lab 🚂")
    st.caption("Analytical and player development hub for Purdue pitching operations.")

    metric_columns = st.columns(3)
    metric_columns[0].metric("Pitches Loaded", f"{health['rows']:,}")
    metric_columns[1].metric("Pitchers Indexed", f"{health['pitchers']:,}")
    metric_columns[2].metric("Pitch Types Indexed", f"{health['pitch_types']:,}")

    pitcher_options = sorted(dataframe["pitcher"].dropna().unique()) if "pitcher" in dataframe.columns else []
    if not pitcher_options:
        st.warning(
            "No Purdue pitchers were found in the loaded dataset. "
            "Update the dataset team labels or add a Purdue roster mapping before using the selector."
        )
        return

    widget_key = "home_selected_pitcher"
    default_pitcher = st.session_state.get("selected_pitcher")
    if default_pitcher not in pitcher_options:
        default_pitcher = pitcher_options[0]

    if st.session_state.get(widget_key) not in pitcher_options:
        st.session_state[widget_key] = default_pitcher

    selected_pitcher = st.selectbox(
        "Select a pitcher",
        options=pitcher_options,
        key=widget_key,
    )
    st.session_state["selected_pitcher"] = selected_pitcher

    button_columns = st.columns(2)
    if button_columns[0].button("Go to Player Profile", use_container_width=True):
        st.session_state["pending_nav_page"] = "player_profile"
        st.rerun()
    if button_columns[1].button("🚨 Open Bullpen Live Scenario Matcher", use_container_width=True):
        st.session_state["pending_nav_page"] = "bullpen"
        st.rerun()


if __name__ == "__main__":
    bootstrap_page("home")
    render()
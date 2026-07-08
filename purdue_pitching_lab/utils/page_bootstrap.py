"""Helpers for running page modules directly in Streamlit."""

from __future__ import annotations

import streamlit as st

from config import APP_ICON, APP_TITLE
from utils.data_loader import load_dataset
from utils.helpers import configure_logging, inject_theme


def bootstrap_page(active_page: str) -> None:
    """Initialize shared app context when a page file is run directly."""

    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    configure_logging()
    inject_theme()
    st.session_state.setdefault("active_page", active_page)
    st.session_state.setdefault("nav_page", active_page)
    st.session_state.setdefault("selected_pitcher", None)
    st.session_state.setdefault("favorite_pitchers", [])
    st.session_state.setdefault("recent_pitchers", [])
    st.session_state["dataset_bundle"] = load_dataset()
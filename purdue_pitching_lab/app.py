"""Streamlit entry point for the Purdue Pitching Lab."""

from __future__ import annotations

import importlib

import streamlit as st
from loguru import logger

from config import APP_ICON, APP_TITLE, PAGE_REGISTRY
from utils.data_loader import dataset_health, filter_target_pitchers, load_dataset
from utils.helpers import configure_logging, inject_theme


def _initialize_state() -> None:
    valid_pages = [page_key for page_key, _ in PAGE_REGISTRY]
    st.session_state.setdefault("active_page", "home")
    if st.session_state["active_page"] not in valid_pages:
        st.session_state["active_page"] = "home"
    st.session_state.setdefault("nav_page", st.session_state["active_page"])
    if st.session_state["nav_page"] not in valid_pages:
        st.session_state["nav_page"] = st.session_state["active_page"]
    st.session_state.setdefault("pending_nav_page", None)
    st.session_state.setdefault("selected_pitcher", None)
    st.session_state.setdefault("favorite_pitchers", [])
    st.session_state.setdefault("recent_pitchers", [])


def _render_sidebar(health: dict[str, object]) -> None:
    st.sidebar.title("Navigation")
    page_label_map = {page_key: label for page_key, label in PAGE_REGISTRY}
    options = [page_key for page_key, _ in PAGE_REGISTRY]

    pending_page = st.session_state.get("pending_nav_page")
    if pending_page in options:
        st.session_state["nav_page"] = pending_page
        st.session_state["active_page"] = pending_page
        st.session_state["pending_nav_page"] = None

    selected_page = st.sidebar.radio(
        "Open module",
        options=options,
        format_func=lambda key: page_label_map[key],
        key="nav_page",
    )
    if selected_page != st.session_state["active_page"]:
        st.session_state["active_page"] = selected_page

    st.sidebar.caption(f"Rows loaded: {health['rows']:,}")
    st.sidebar.caption(f"Pitchers: {health['pitchers']:,}")
    if health["notes"]:
        st.sidebar.info("\n".join(health["notes"]))


def _render_page() -> None:
    module = importlib.import_module(f"pages.{st.session_state['active_page']}")
    module.render()


def main() -> None:
    """Run the Streamlit application."""

    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    configure_logging()
    inject_theme()
    _initialize_state()

    try:
        bundle = load_dataset()
        st.session_state["dataset_bundle"] = bundle
        st.session_state["roster_df"] = filter_target_pitchers(bundle.dataframe)
        health = dataset_health(bundle)
        _render_sidebar(health)
        _render_page()
    except Exception as exc:  # pragma: no cover - UI guardrail
        logger.exception("app_runtime_error error={}", exc)
        st.error(
            "The application hit an unexpected issue while loading this module. "
            "The error has been logged to logs/app.log."
        )


if __name__ == "__main__":
    main()
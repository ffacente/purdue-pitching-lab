"""Streamlit entry point for the Purdue Pitching Lab."""

from __future__ import annotations

import importlib
import os
from urllib.parse import urlparse

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from loguru import logger

from config import APP_ICON, APP_TITLE, DATA_PATH, PAGE_REGISTRY, SAMPLE_DATA_PATH
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


def _resolve_dataset_source() -> tuple[str | None, str | None]:
    """Return dataset source and a short UI status message."""

    try:
        remote_url = str(st.secrets.get("FULL_DATASET_URL", "")).strip()
    except StreamlitSecretNotFoundError:
        remote_url = ""
    if not remote_url:
        remote_url = os.getenv("FULL_DATASET_URL", "").strip()

    if remote_url:
        parsed = urlparse(remote_url)
        if parsed.scheme in {"http", "https", "s3", "gs", "abfs"}:
            return remote_url, "Using full dataset from remote storage."
        logger.warning("invalid_dataset_url scheme={} value={}", parsed.scheme, remote_url)

    if DATA_PATH.exists():
        return str(DATA_PATH), None

    if SAMPLE_DATA_PATH.exists():
        return str(SAMPLE_DATA_PATH), "Full dataset not found; running with sample dataset for cloud compatibility."

    return None, None


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
        dataset_source, dataset_message = _resolve_dataset_source()
        if dataset_source is None:
            st.error(
                "Dataset file is missing at "
                f"{DATA_PATH}. "
                "This often happens on Streamlit Cloud when large parquet files are excluded from Git. "
                "Set FULL_DATASET_URL in Streamlit Cloud Secrets for the full dataset, "
                "or commit a smaller sample dataset. "
                f"Expected fallback path: {SAMPLE_DATA_PATH}."
            )
            st.stop()

        if dataset_message:
            st.warning(dataset_message)

        try:
            bundle = load_dataset(path=dataset_source)
        except Exception as dataset_exc:
            logger.exception("dataset_load_failed source={} error={}", dataset_source, dataset_exc)
            can_fallback = dataset_source != str(SAMPLE_DATA_PATH) and SAMPLE_DATA_PATH.exists()
            if can_fallback:
                error_text = str(dataset_exc).strip().replace("\n", " ")
                if not error_text:
                    error_text = dataset_exc.__class__.__name__
                if len(error_text) > 220:
                    error_text = f"{error_text[:217]}..."
                st.warning(
                    "Full dataset could not be loaded from remote storage. "
                    f"Falling back to sample dataset. Reason: {error_text}"
                )
                bundle = load_dataset(path=str(SAMPLE_DATA_PATH))
            else:
                raise

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
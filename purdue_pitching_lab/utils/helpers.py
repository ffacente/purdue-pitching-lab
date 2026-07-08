"""Shared helper utilities for logging, formatting, and exports."""

from __future__ import annotations

import io
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from loguru import logger

from config import EXPORT_FILE_PREFIX, LOG_DIR, LOG_PATH, PURDUE_COLORS


def configure_logging() -> None:
    """Configure the application logger once per process."""

    if getattr(configure_logging, "_configured", False):
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    Path(LOG_PATH).touch(exist_ok=True)
    logger.remove()
    logger.add(LOG_PATH, rotation="5 MB", retention=5, enqueue=True, backtrace=False)
    logger.add(lambda message: print(message, end=""), level="INFO")
    configure_logging._configured = True


@contextmanager
def log_timing(event_name: str, **context: Any) -> Iterator[None]:
    """Log the execution time for a block of work."""

    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        logger.info("event={} elapsed_ms={:.2f} context={}", event_name, elapsed, context)


def show_small_sample_warning(sample_size: int) -> None:
    """Render the standard small-sample message."""

    if sample_size < 5:
        st.warning(
            "📊 Not enough data recorded in this specific scenario to draw a reliable conclusion."
        )


def format_metric(value: float | None, kind: str = "number") -> str:
    """Format a metric value for display."""

    if value is None or pd.isna(value):
        return "N/A"
    if kind == "pct":
        return f"{value:.1%}"
    if kind == "avg":
        return f"{value:.3f}"
    if kind == "mph":
        return f"{value:.1f} mph"
    if kind == "rpm":
        return f"{value:,.0f} rpm"
    return f"{value:,.2f}"


def dataframe_to_excel_bytes(dataframe: pd.DataFrame) -> bytes:
    """Convert a dataframe to an Excel workbook in memory."""

    export_frame = dataframe.copy()
    for column in export_frame.columns:
        series = export_frame[column]
        if isinstance(series.dtype, pd.DatetimeTZDtype):
            export_frame[column] = series.dt.tz_localize(None)
            continue

        if pd.api.types.is_object_dtype(series):
            has_tz_values = series.map(
                lambda value: isinstance(value, pd.Timestamp) and value.tz is not None
            ).any()
            if has_tz_values:
                export_frame[column] = series.map(
                    lambda value: value.tz_localize(None)
                    if isinstance(value, pd.Timestamp) and value.tz is not None
                    else value
                )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        export_frame.to_excel(writer, index=False, sheet_name="Data")
    return output.getvalue()


def plotly_figure_to_png_bytes(figure: go.Figure) -> bytes | None:
    """Convert a Plotly figure to PNG bytes if kaleido is available."""

    try:
        return figure.to_image(format="png", scale=2)
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.warning("plot_export_failed error={}", exc)
        return None


def build_pdf_report(title: str, sections: list[tuple[str, str]]) -> bytes:
    """Generate a simple PDF report from text sections."""

    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 12, title, ln=True)
    pdf.set_draw_color(207, 185, 145)
    pdf.line(10, 22, 200, 22)

    for heading, body in sections:
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(0, 0, 0)
        pdf.set_x(10)
        pdf.multi_cell(190, 8, str(heading))
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(60, 60, 60)
        pdf.set_x(10)
        pdf.multi_cell(190, 6, str(body))

    return bytes(pdf.output(dest="S"))


def inject_theme() -> None:
    """Apply Purdue-themed styling to the Streamlit app."""

    colors = PURDUE_COLORS
    st.markdown(
        f"""
        <style>
            :root {{
                --gold: {colors['gold']};
                --black: {colors['black']};
                --slate: {colors['slate']};
                --slate-light: {colors['slate_light']};
                --white: {colors['white']};
            }}
            .block-container {{padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1320px;}}
            [data-testid="stSidebar"] {{position: sticky; top: 0;}}
            .metric-card {{background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%); border: 1px solid #e2e8f0; border-left: 6px solid var(--gold); border-radius: 16px; padding: 1rem; box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);}}
            .status-card {{border-radius: 16px; padding: 1rem; color: white; margin-bottom: 0.75rem;}}
            .status-red {{background: linear-gradient(135deg, #991b1b, #dc2626);}}
            .status-yellow {{background: linear-gradient(135deg, #a16207, #f59e0b);}}
            .status-green {{background: linear-gradient(135deg, #166534, #16a34a);}}
            .recent-player-grid {{display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 1rem;}}
            .recent-player-card {{background: linear-gradient(135deg, #111827 0%, #1f2937 100%); color: #f8fafc; border: 1px solid rgba(207,185,145,0.45); border-radius: 14px; padding: 0.9rem 1rem; font-weight: 700; letter-spacing: 0.02em; box-shadow: 0 10px 24px rgba(15, 23, 42, 0.18);}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def export_filename(stem: str, suffix: str) -> str:
    """Return a standard export file name."""

    return f"{EXPORT_FILE_PREFIX}_{stem}.{suffix}"
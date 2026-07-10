"""Pitcher performance profile page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.data_loader import filter_target_pitchers
from utils.filters import FilterState, apply_filters, get_filter_options
from utils.helpers import dataframe_to_excel_bytes, export_filename, format_metric, plotly_figure_to_png_bytes, show_small_sample_warning
from utils.metrics import METRIC_REGISTRY, calculate_metrics, summarize_by_group
from utils.page_bootstrap import bootstrap_page
from utils.plotting import movement_scatter, usage_treemap


def render() -> None:
    """Render the pitcher profile page."""

    bundle = st.session_state["dataset_bundle"]
    dataframe = filter_target_pitchers(bundle.dataframe)
    pitcher_options = sorted(dataframe["pitcher"].dropna().unique())
    if not pitcher_options:
        st.warning("No Purdue pitchers are available for the player profile page.")
        return

    selected_pitcher = _select_pitcher(pitcher_options)
    pitcher_df = dataframe.loc[dataframe["pitcher"] == selected_pitcher].copy()
    filters = _build_profile_filters(pitcher_df)
    filtered = apply_filters(pitcher_df, filters)

    st.title("Pitcher Performance Profile")
    st.caption(f"Detailed performance model for {selected_pitcher}")
    show_small_sample_warning(len(filtered))

    metrics = calculate_metrics(filtered)
    _render_metric_cards(metrics)

    export_columns = st.columns(3)
    export_columns[0].download_button(
        "Download CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name=export_filename("player_profile_filtered", "csv"),
        use_container_width=True,
    )
    export_columns[1].download_button(
        "Download Excel",
        data=dataframe_to_excel_bytes(filtered),
        file_name=export_filename("player_profile_filtered", "xlsx"),
        use_container_width=True,
    )

    arsenal_tab, performance_tab = st.tabs(["Arsenal Overview", "Performance Output"])
    with arsenal_tab:
        _render_arsenal_tab(filtered)
    with performance_tab:
        _render_performance_tab(filtered)


def _select_pitcher(pitcher_options: list[str]) -> str:
    widget_key = "player_profile_selected_pitcher"
    default_pitcher = st.session_state.get("selected_pitcher")
    if default_pitcher not in pitcher_options:
        default_pitcher = pitcher_options[0]

    if st.session_state.get(widget_key) not in pitcher_options:
        st.session_state[widget_key] = default_pitcher

    selected_pitcher = st.selectbox(
        "Pitcher",
        options=pitcher_options,
        key=widget_key,
    )
    st.session_state["selected_pitcher"] = selected_pitcher
    return selected_pitcher


def _build_profile_filters(pitcher_df: pd.DataFrame) -> FilterState:
    options = get_filter_options(pitcher_df)
    with st.sidebar:
        st.subheader("Profile Filters")
        batter_sides = st.multiselect("Batter Side", options.get("batter_side", []), default=[])
        outs = st.multiselect("Outs", options.get("outs", []), default=[])
        count_groups = st.multiselect("Count Group", options.get("count_group", []), default=[])
        pitch_types = st.multiselect("Pitch Type", options.get("pitch_type", []), default=[])
    return FilterState(
        batter_sides=tuple(batter_sides),
        outs=tuple(int(value) for value in outs),
        count_groups=tuple(count_groups),
        pitch_types=tuple(pitch_types),
    )


def _render_metric_cards(metrics: dict[str, float]) -> None:
    columns = st.columns(5)
    metric_order = ["baa", "obp", "slg", "ops", "whiff_pct"]
    for column, metric_name in zip(columns, metric_order, strict=True):
        spec = METRIC_REGISTRY[metric_name]
        column.metric(spec.label, format_metric(metrics.get(metric_name), spec.kind), help=spec.description)


def _render_arsenal_tab(filtered: pd.DataFrame) -> None:
    usage_figure = usage_treemap(filtered)
    movement_figure = movement_scatter(filtered)

    chart_columns = st.columns(2)
    if usage_figure:
        chart_columns[0].plotly_chart(usage_figure, use_container_width=True)
        png_bytes = plotly_figure_to_png_bytes(usage_figure)
        if png_bytes:
            chart_columns[0].download_button(
                "Export Usage PNG",
                data=png_bytes,
                file_name=export_filename("usage_treemap", "png"),
            )
    else:
        chart_columns[0].info("Pitch usage treemap is unavailable because pitch type data is missing.")

    if movement_figure:
        chart_columns[1].plotly_chart(movement_figure, use_container_width=True)
    else:
        chart_columns[1].info("Movement scatter is unavailable because break metrics are missing.")


def _render_performance_tab(filtered: pd.DataFrame) -> None:
    summary = summarize_by_group(filtered, ("pitch_type",))
    if summary.empty:
        st.info("No pitch-level performance sample is available for the selected filter combination.")
        return
    display_columns = [
        "pitch_type",
        "sample_size",
        "usage_pct",
        "baa",
        "obp",
        "slg",
        "ops",
        "whiff_pct",
        "hard_hit_pct",
        "ground_ball_pct",
        "line_drive_pct",
        "fly_ball_pct",
    ]
    available = [column for column in display_columns if column in summary.columns]
    st.dataframe(summary[available], use_container_width=True, hide_index=True)


if __name__ == "__main__":
    bootstrap_page("player_profile")
    render()
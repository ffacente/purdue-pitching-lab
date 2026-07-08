"""Filtering utilities for pitcher and scenario views."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st
from loguru import logger

from utils.helpers import log_timing


@dataclass(frozen=True)
class FilterState:
    """Represents active filters for a page."""

    pitcher: str | None = None
    batter_sides: tuple[str, ...] = ()
    outs: tuple[int, ...] = ()
    game_states: tuple[str, ...] = ()
    count_groups: tuple[str, ...] = ()
    pitch_types: tuple[str, ...] = ()


@st.cache_data(show_spinner=False)
def apply_filters(dataframe: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
    """Apply cached filters to a dataframe."""

    with log_timing("apply_filters", filters=filters.__dict__):
        filtered = dataframe.copy()
        if filters.pitcher and "pitcher" in filtered.columns:
            filtered = filtered.loc[filtered["pitcher"] == filters.pitcher]
        if filters.batter_sides and "batter_side" in filtered.columns:
            filtered = filtered.loc[filtered["batter_side"].isin(filters.batter_sides)]
        if filters.outs and "outs" in filtered.columns:
            filtered = filtered.loc[filtered["outs"].isin(filters.outs)]
        if filters.game_states and "game_state" in filtered.columns:
            filtered = filtered.loc[filtered["game_state"].isin(filters.game_states)]
        if filters.count_groups and "count_group" in filtered.columns:
            filtered = filtered.loc[filtered["count_group"].isin(filters.count_groups)]
        if filters.pitch_types and "pitch_type" in filtered.columns:
            filtered = filtered.loc[filtered["pitch_type"].isin(filters.pitch_types)]
        logger.info("filters_applied rows={} filters={}", len(filtered), filters)
        return filtered


def get_filter_options(dataframe: pd.DataFrame) -> dict[str, list[str]]:
    """Return filter options present in the dataset."""

    options: dict[str, list[str]] = {}
    for column in ["batter_side", "game_state", "count_group", "pitch_type"]:
        if column in dataframe.columns:
            values = sorted(
                value
                for value in dataframe[column].dropna().astype(str).unique()
                if value and value.lower() != "unknown"
            )
            options[column] = values
    if "outs" in dataframe.columns:
        options["outs"] = [str(int(value)) for value in sorted(dataframe["outs"].dropna().unique())]
    return options
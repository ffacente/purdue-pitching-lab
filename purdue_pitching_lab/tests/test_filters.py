"""Tests for filtering logic."""

from __future__ import annotations

import pandas as pd

from utils.filters import FilterState, apply_filters


def test_apply_filters_respects_multiple_fields() -> None:
    dataframe = pd.DataFrame(
        {
            "pitcher": ["A", "A", "B"],
            "batter_side": ["Left", "Right", "Left"],
            "outs": [0, 1, 0],
            "game_state": ["Bases Empty", "RISP", "Bases Empty"],
            "count_group": ["0-0", "Ahead", "0-0"],
            "pitch_type": ["Fastball", "Slider", "Fastball"],
        }
    )
    filters = FilterState(
        pitcher="A",
        batter_sides=("Left",),
        outs=(0,),
        game_states=("Bases Empty",),
        count_groups=("0-0",),
        pitch_types=("Fastball",),
    )

    result = apply_filters(dataframe, filters)

    assert len(result) == 1
    assert result.iloc[0]["pitcher"] == "A"
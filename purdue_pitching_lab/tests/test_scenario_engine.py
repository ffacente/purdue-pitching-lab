"""Tests for the bullpen scenario engine."""

from __future__ import annotations

import pandas as pd

from utils.filters import FilterState
from utils.scenario_engine import build_scenario_leaderboard


def test_scenario_engine_ranks_pitchers_and_separates_unsampled() -> None:
    dataframe = pd.DataFrame(
        {
            "pitcher": ["A"] * 6 + ["B"] * 6 + ["C"] * 4,
            "batter_side": ["Right"] * 16,
            "outs": [2] * 16,
            "game_state": ["Bases Empty"] * 16,
            "count_group": ["Ahead"] * 16,
            "is_terminal_pitch": [True] * 16,
            "play_result": ["Out", "Out", "Single", "Out", "Out", "Out", "Single", "Double", "Single", "Out", "Out", "Out", "Out", "Out", "Out", "Out"],
            "pitch_call": ["StrikeSwinging", "InPlay", "InPlay", "StrikeSwinging", "InPlay", "InPlay", "InPlay", "InPlay", "InPlay", "StrikeSwinging", "InPlay", "InPlay", "InPlay", "InPlay", "InPlay", "InPlay"],
            "kor_bb": ["Strikeout", "InPlay", "InPlay", "Strikeout", "InPlay", "InPlay", "InPlay", "InPlay", "InPlay", "Strikeout", "InPlay", "InPlay", "InPlay", "InPlay", "InPlay", "InPlay"],
            "batted_ball_type": ["", "GroundBall", "LineDrive", "", "GroundBall", "GroundBall", "FlyBall", "FlyBall", "LineDrive", "", "GroundBall", "GroundBall", "GroundBall", "GroundBall", "GroundBall", "GroundBall"],
            "exit_velocity": [None, 88, 99, None, 87, 85, 97, 102, 96, None, 82, 84, 80, 81, 79, 78],
        }
    )

    ranked, unsampled = build_scenario_leaderboard(dataframe, FilterState())

    assert list(ranked["pitcher"]) == ["A", "B"]
    assert list(unsampled["pitcher"]) == ["C"]
    assert ranked.iloc[0]["scenario_score"] > ranked.iloc[1]["scenario_score"]
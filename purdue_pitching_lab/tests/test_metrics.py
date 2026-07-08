"""Tests for metric calculations."""

from __future__ import annotations

import pytest
import pandas as pd

from utils.metrics import calculate_metrics


def test_calculate_metrics_matches_required_formulas() -> None:
    dataframe = pd.DataFrame(
        {
            "is_terminal_pitch": [True, True, True, True],
            "play_result": ["Single", "Double", "Out", "Sacrifice"],
            "pitch_call": ["InPlay", "InPlay", "StrikeSwinging", "InPlay"],
            "kor_bb": ["InPlay", "InPlay", "Strikeout", "InPlay"],
            "batted_ball_type": ["GroundBall", "FlyBall", "", "FlyBall"],
            "exit_velocity": [96.0, 88.0, None, 85.0],
        }
    )

    metrics = calculate_metrics(dataframe)

    assert metrics["baa"] == pytest.approx(2 / 3)
    assert metrics["obp"] == pytest.approx(2 / 4)
    assert metrics["slg"] == pytest.approx(3 / 3)
    assert metrics["ops"] == pytest.approx((2 / 4) + (3 / 3))
    assert metrics["whiff_pct"] == pytest.approx(1 / 4)
    assert metrics["hard_hit_pct"] == pytest.approx(1 / 3)
    assert metrics["ground_ball_pct"] == pytest.approx(1 / 3)
    assert metrics["line_drive_pct"] == pytest.approx(0.0)
    assert metrics["fly_ball_pct"] == pytest.approx(2 / 3)


def test_small_sample_metric_calculation_stays_safe() -> None:
    dataframe = pd.DataFrame(
        {
            "is_terminal_pitch": [True],
            "play_result": ["Out"],
            "pitch_call": ["StrikeCalled"],
            "kor_bb": ["."],
            "batted_ball_type": [""],
            "exit_velocity": [None],
        }
    )

    metrics = calculate_metrics(dataframe)

    assert metrics["whiff_pct"] == 0.0
    assert metrics["hard_hit_pct"] == 0.0
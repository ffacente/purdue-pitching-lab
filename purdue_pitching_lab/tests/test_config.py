"""Tests for configuration constants."""

from config import COUNT_GROUPS, MIN_SAMPLE_SIZE, TARGET_TEAM


def test_target_team_is_purdue() -> None:
    assert TARGET_TEAM == "Purdue"


def test_min_sample_size_threshold() -> None:
    assert MIN_SAMPLE_SIZE == 5


def test_full_count_group_defined() -> None:
    assert COUNT_GROUPS["Full Count"] == [(3, 2)]
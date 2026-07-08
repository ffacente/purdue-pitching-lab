"""Data loading, schema discovery, and normalization utilities."""

from __future__ import annotations

from dataclasses import dataclass
import io
import os
import re
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

import pandas as pd
import streamlit as st
from loguru import logger

from config import (
    COUNT_GROUPS,
    DATA_PATH,
    EXCLUDED_PITCHERS_NEXT_YEAR,
    TARGET_TEAM,
    TARGET_TEAM_ALIASES,
    TRANSFER_PLAYER_ALIASES,
    TRANSFER_PLAYER_SCHOOLS,
)
from utils.helpers import log_timing

ALIAS_MAP = {
    "pitch_type": ["tagged_pitch_type", "pitch_type", "auto_pitch_type", "PitchType"],
    "pitcher": ["pitcher", "PitcherName", "Pitcher Name", "Player"],
    "velocity": ["release_speed", "pitch_speed", "velocity", "rel_speed", "RelSpeed"],
    "spin_rate": ["spin_rate", "release_spin_rate", "spin", "SpinRate"],
    "team": ["pitcher_team", "team", "school", "program", "PitcherTeam"],
    "horizontal_break": ["horizontal_break", "horz_break", "HorzBreak"],
    "induced_vertical_break": ["induced_vertical_break", "InducedVertBreak", "vert_break", "ivb"],
    "batted_ball_type": ["tagged_hit_type", "hit_type", "BattedBallType", "TaggedHitType"],
    "batter_side": ["batter_side", "BatterSide"],
    "outs": ["outs", "Outs"],
    "balls": ["balls", "Balls"],
    "strikes": ["strikes", "Strikes"],
    "pitch_call": ["pitch_call", "PitchCall"],
    "play_result": ["play_result", "PlayResult"],
    "kor_bb": ["korbb", "KorBB"],
    "exit_velocity": ["exit_velocity", "exit_speed", "ExitSpeed"],
    "date": ["date", "Date"],
    "batter": ["batter", "Batter"],
    "inning": ["inning", "Inning"],
    "top_bottom": ["top_bottom", "Top/Bottom"],
    "pa_of_inning": ["pa_of_inning", "PAofInning"],
    "pitch_of_pa": ["pitch_of_pa", "PitchofPA"],
    "game_id": ["game_uid", "GameUID", "GameID"],
    "runner_on_first": ["1B", "RunnerOnFirst", "RunnerOn1B", "FirstBaseRunner"],
    "runner_on_second": ["2B", "RunnerOnSecond", "RunnerOn2B", "SecondBaseRunner"],
    "runner_on_third": ["3B", "RunnerOnThird", "RunnerOn3B", "ThirdBaseRunner"],
}


@dataclass(frozen=True)
class DatasetBundle:
    """Normalized dataset payload shared across pages."""

    dataframe: pd.DataFrame
    column_map: dict[str, str]
    missing_aliases: list[str]
    notes: list[str]


def _normalize_token(value: str) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def _find_alias(columns: list[str], aliases: list[str]) -> str | None:
    lookup = {_normalize_token(column): column for column in columns}
    for alias in aliases:
        match = lookup.get(_normalize_token(alias))
        if match:
            return match
    return None


def discover_column_map(columns: list[str]) -> tuple[dict[str, str], list[str]]:
    """Discover the source-to-standard column map."""

    mapping: dict[str, str] = {}
    missing: list[str] = []
    for standard_name, aliases in ALIAS_MAP.items():
        found = _find_alias(columns, aliases)
        if found:
            mapping[standard_name] = found
        else:
            missing.append(standard_name)
    return mapping, missing


def _clean_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _coalesce_pitch_type(dataframe: pd.DataFrame) -> pd.Series:
    tagged = dataframe.get("TaggedPitchType")
    auto = dataframe.get("AutoPitchType")
    if tagged is None and auto is None:
        return pd.Series(["Unknown"] * len(dataframe), index=dataframe.index)
    if tagged is None:
        return _clean_text(auto).replace("", "Unknown")
    tagged_clean = _clean_text(tagged)
    if auto is None:
        return tagged_clean.replace("", "Unknown")
    auto_clean = _clean_text(auto)
    return tagged_clean.where(tagged_clean.ne(""), auto_clean).replace("", "Unknown")


def _canonical_pitch_type(series: pd.Series) -> pd.Series:
    """Normalize pitch labels to canonical program groupings."""

    normalized = series.fillna("Unknown").astype(str).str.strip()
    token = normalized.str.lower().str.replace(r"[^a-z0-9]+", "", regex=True)

    # Collapse non-actionable labels that should not appear as separate pitch types.
    special_mask = token.str.contains("other|undefined|unknown")
    normalized = normalized.mask(special_mask, "Unknown")

    # Collapse all four-seam/fastball variants into a single Fastball label.
    fastball_mask = token.str.contains("fourseam|4seam|fourseamfastball|fastball")
    normalized = normalized.mask(fastball_mask, "Fastball")

    return normalized.replace("", "Unknown")


def _normalize_count_group(dataframe: pd.DataFrame) -> pd.Series:
    reverse_lookup = {
        count: label for label, counts in COUNT_GROUPS.items() for count in counts
    }
    balls = dataframe["balls"].fillna(0).astype(int)
    strikes = dataframe["strikes"].fillna(0).astype(int)
    values = [reverse_lookup.get((ball, strike), "Other") for ball, strike in zip(balls, strikes, strict=False)]
    return pd.Series(values, index=dataframe.index)


def _normalize_game_state(dataframe: pd.DataFrame) -> pd.Series:
    runner_columns = {"runner_on_first", "runner_on_second", "runner_on_third"}
    if runner_columns.issubset(dataframe.columns):
        first = dataframe["runner_on_first"].notna()
        second = dataframe["runner_on_second"].notna()
        third = dataframe["runner_on_third"].notna()
        risp = second | third
        on_base = first | second | third
        return pd.Series(
            pd.Series("Bases Empty", index=dataframe.index)
            .mask(on_base, "Men on Base")
            .mask(risp, "RISP"),
            index=dataframe.index,
        )
    return pd.Series("", index=dataframe.index)


def _build_pa_identifier(dataframe: pd.DataFrame) -> pd.Series:
    pieces = [
        dataframe.get("game_id", pd.Series("", index=dataframe.index)).astype(str),
        dataframe.get("inning", pd.Series("", index=dataframe.index)).astype(str),
        dataframe.get("top_bottom", pd.Series("", index=dataframe.index)).astype(str),
        dataframe.get("pa_of_inning", pd.Series("", index=dataframe.index)).astype(str),
        dataframe.get("pitcher", pd.Series("", index=dataframe.index)).astype(str),
        dataframe.get("batter", pd.Series("", index=dataframe.index)).astype(str),
    ]
    return pieces[0].str.cat(pieces[1:], sep="|")


def _build_notes(dataframe: pd.DataFrame) -> list[str]:
    notes: list[str] = []
    teams = dataframe["team"].dropna().astype(str).str.strip().str.lower()
    target_aliases = {alias.strip().lower() for alias in TARGET_TEAM_ALIASES}
    if not teams.isin(target_aliases).any():
        notes.append(
            "No Purdue team label match was found in the dataset, so the Purdue-only roster is currently empty."
        )

    pitchers = dataframe["pitcher"].dropna().astype(str)
    for player_name, school in TRANSFER_PLAYER_SCHOOLS.items():
        aliases = TRANSFER_PLAYER_ALIASES.get(player_name, [player_name])
        pattern = "|".join(re.escape(alias) for alias in aliases)
        if not pitchers.str.contains(pattern, case=False, na=False, regex=True).any():
            notes.append(f"Transfer note: {player_name} ({school}) has no available stats in this file.")
    return notes


def _transfer_pitcher_mask(dataframe: pd.DataFrame) -> pd.Series:
    if "pitcher" not in dataframe.columns:
        return pd.Series(False, index=dataframe.index)
    pitcher_series = dataframe["pitcher"].fillna("").astype(str)
    mask = pd.Series(False, index=dataframe.index)
    for aliases in TRANSFER_PLAYER_ALIASES.values():
        pattern = "|".join(re.escape(alias) for alias in aliases)
        mask = mask | pitcher_series.str.contains(pattern, case=False, na=False, regex=True)
    return mask


def _build_excluded_pitcher_aliases() -> set[str]:
    aliases: set[str] = set()
    for raw_name in EXCLUDED_PITCHERS_NEXT_YEAR:
        clean_name = raw_name.strip()
        if not clean_name:
            continue
        aliases.add(clean_name.lower())
        parts = clean_name.split()
        if len(parts) >= 2:
            first = parts[0]
            last = " ".join(parts[1:])
            aliases.add(f"{last}, {first}".lower())
    return aliases


def _standardize_dataframe(dataframe: pd.DataFrame, column_map: dict[str, str]) -> pd.DataFrame:
    normalized = dataframe.copy()
    rename_map = {source: standard for standard, source in column_map.items()}
    normalized = normalized.rename(columns=rename_map)
    normalized["pitch_type"] = _canonical_pitch_type(_coalesce_pitch_type(dataframe))

    numeric_columns = [
        "velocity",
        "spin_rate",
        "horizontal_break",
        "induced_vertical_break",
        "exit_velocity",
        "balls",
        "strikes",
        "outs",
        "pitch_of_pa",
    ]
    for column in numeric_columns:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    text_columns = ["pitcher", "team", "batter_side", "pitch_call", "play_result", "kor_bb", "batted_ball_type"]
    for column in text_columns:
        if column in normalized.columns:
            normalized[column] = _clean_text(normalized[column])

    if {"balls", "strikes"}.issubset(normalized.columns):
        normalized["count"] = normalized["balls"].fillna(0).astype(int).astype(str).str.cat(
            normalized["strikes"].fillna(0).astype(int).astype(str), sep="-"
        )
        normalized["count_group"] = _normalize_count_group(normalized)
    else:
        normalized["count"] = "Unknown"
        normalized["count_group"] = "Unknown"

    if "batter_side" in normalized.columns:
        normalized["batter_side"] = normalized["batter_side"].replace({"left": "Left"})
    else:
        normalized["batter_side"] = "Unknown"

    normalized["game_state"] = _normalize_game_state(normalized)
    normalized["pa_id"] = _build_pa_identifier(normalized)
    normalized["is_terminal_pitch"] = (
        normalized.groupby("pa_id")["pitch_of_pa"].transform("max") == normalized["pitch_of_pa"]
        if "pitch_of_pa" in normalized.columns
        else True
    )
    return normalized


@st.cache_data(show_spinner=False)
def load_dataset(path: str = str(DATA_PATH)) -> DatasetBundle:
    """Load, normalize, and cache the source Parquet dataset."""

    with log_timing("load_dataset", path=path):
        parsed_path = urlparse(path)
        if parsed_path.scheme in {"http", "https"}:
            with urlopen(path, timeout=120) as response:  # nosec B310 - controlled by app config
                dataframe = pd.read_parquet(io.BytesIO(response.read()))
        else:
            dataframe = pd.read_parquet(path)

        duplicate_rows = int(dataframe.duplicated().sum())
        if duplicate_rows:
            dataframe = dataframe.drop_duplicates().copy()
            logger.info("dropped_exact_duplicates rows_removed={} rows_remaining={}", duplicate_rows, len(dataframe))

        column_map, missing = discover_column_map(list(dataframe.columns))
        logger.info("dataset_loaded rows={} cols={} mapped={} missing={}", len(dataframe), len(dataframe.columns), column_map, missing)
        normalized = _standardize_dataframe(dataframe, column_map)

        target_only = os.getenv("TARGET_ONLY_DATA", "true").strip().lower() in {"1", "true", "yes", "y"}
        if target_only:
            before_rows = len(normalized)
            normalized = filter_target_pitchers(normalized)
            logger.info(
                "target_dataset_pruned enabled={} rows_before={} rows_after={}",
                target_only,
                before_rows,
                len(normalized),
            )

        notes = _build_notes(normalized)
        return DatasetBundle(
            dataframe=normalized,
            column_map=column_map,
            missing_aliases=missing,
            notes=notes,
        )


def filter_target_pitchers(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return only the Purdue pitcher slice."""

    excluded_aliases = _build_excluded_pitcher_aliases()

    if "team" not in dataframe.columns:
        transfer_mask = _transfer_pitcher_mask(dataframe)
        filtered = dataframe.loc[transfer_mask].copy()
        if "pitcher" in filtered.columns and excluded_aliases:
            filtered = filtered.loc[
                ~filtered["pitcher"].fillna("").astype(str).str.strip().str.lower().isin(excluded_aliases)
            ].copy()
        return filtered

    target_aliases = {alias.strip().lower() for alias in TARGET_TEAM_ALIASES}
    team_mask = dataframe["team"].astype(str).str.strip().str.lower().isin(target_aliases)
    transfer_mask = _transfer_pitcher_mask(dataframe)
    filtered = dataframe.loc[team_mask | transfer_mask].copy()
    if "pitcher" in filtered.columns and excluded_aliases:
        filtered = filtered.loc[
            ~filtered["pitcher"].fillna("").astype(str).str.strip().str.lower().isin(excluded_aliases)
        ].copy()
    return filtered


def dataset_health(bundle: DatasetBundle) -> dict[str, Any]:
    """Summarize dataset state for the UI."""

    dataframe = bundle.dataframe
    pitcher_count = dataframe["pitcher"].nunique() if "pitcher" in dataframe.columns else 0
    pitch_types = dataframe["pitch_type"].nunique() if "pitch_type" in dataframe.columns else 0
    return {
        "rows": len(dataframe),
        "pitchers": pitcher_count,
        "pitch_types": pitch_types,
        "missing_aliases": bundle.missing_aliases,
        "notes": bundle.notes,
    }
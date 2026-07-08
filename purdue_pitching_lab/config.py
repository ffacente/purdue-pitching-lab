"""Application configuration for the Purdue Pitching Lab."""

from __future__ import annotations

from pathlib import Path

APP_TITLE = "Purdue Pitching Lab"
APP_ICON = "🚂"
TARGET_TEAM = "Purdue"
TARGET_TEAM_ALIASES = ["Purdue", "PUR_BOI"]
MIN_SAMPLE_SIZE = 5

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_PATH = DATA_DIR / "combined_data.parquet"
ASSETS_DIR = BASE_DIR / "assets"
LOG_DIR = BASE_DIR / "logs"
LOG_PATH = LOG_DIR / "app.log"

PURDUE_COLORS = {
    "gold": "#CFB991",
    "black": "#000000",
    "slate": "#475569",
    "slate_light": "#E2E8F0",
    "white": "#FFFFFF",
    "success": "#15803D",
    "warning": "#B45309",
    "danger": "#B91C1C",
}

PAGE_REGISTRY = [
    ("home", "Purdue Pitching Lab"),
    ("player_profile", "Pitcher Performance Profile"),
    ("development", "Player Development Engine"),
    ("pitch_design", "Pitch Design Lab"),
    ("arsenal_optimization", "Arsenal Optimization"),
    ("bullpen", "Bullpen Scenario Matcher"),
]

TRANSFER_PLAYER_SCHOOLS = {
    "Max Tramontana": "App St",
    "Walker Brodt": "Winthrop",
    "Cam Allen": "Wright State",
    "Nolan Roycraft": "Rice",
}

TRANSFER_PLAYER_ALIASES = {
    "Max Tramontana": ["Max Tramontana", "Tramontana, Max"],
    "Walker Brodt": ["Walker Brodt", "Brodt, Walker"],
    "Cam Allen": ["Cam Allen", "Cameron Allen", "Allen, Cameron"],
    "Nolan Roycraft": ["Nolan Roycraft", "Roycraft, Nolan"],
}

TRANSFER_TEAM_CODE_MAP = {
    "App St": ["APP", "APP_ST", "APPALACHIAN", "APP STATE", "APP_MOU"],
    "Winthrop": ["WIN", "WINTHROP", "WIN_EAG"],
    "Wright State": ["WRI", "WRIGHT", "WRIGHT STATE", "WRI_RAI", "WRI_EAG"],
    "Rice": ["RIC", "RICE", "RIC_OWL"],
}

COUNT_GROUPS = {
    "0-0": [(0, 0)],
    "Ahead": [(0, 1), (0, 2), (1, 2)],
    "Even": [(1, 1), (2, 2)],
    "Behind": [(1, 0), (2, 0), (3, 0), (2, 1), (3, 1)],
    "Full Count": [(3, 2)],
}

GAME_STATE_OPTIONS = ["Bases Empty", "Men on Base", "RISP"]

EXPORT_FILE_PREFIX = "purdue_pitching_lab"
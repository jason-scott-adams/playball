from __future__ import annotations

from datetime import date
from io import StringIO
from typing import Dict, List

import pandas as pd
import requests
import streamlit as st


SAVANT_CSV_URL = "https://baseballsavant.mlb.com/statcast_search/csv"


def _season_start() -> str:
    return f"{date.today().year}-03-01"


def _today() -> str:
    return date.today().isoformat()


def _base_params(player_type: str, min_pas: int, sort_col: str, sort_order: str) -> Dict[str, str]:
    return {
        "all": "true",
        "hfGT": "R|",
        "hfSea": f"{date.today().year}|",
        "player_type": player_type,
        "game_date_gt": _season_start(),
        "game_date_lt": _today(),
        "group_by": "name",
        "sort_col": sort_col,
        "sort_order": sort_order,
        "min_pitches": "0",
        "min_results": "0",
        "min_pas": str(min_pas),
        "chk_stats_pa": "on",
        "chk_stats_woba": "on",
        "chk_stats_xwoba": "on",
        "chk_stats_xba": "on",
        "chk_stats_xslg": "on",
        "chk_stats_exit_velocity": "on",
        "chk_stats_launch_angle": "on",
    }


def _pitch_type_params(pitcher_id: int) -> Dict[str, str]:
    params = _base_params("pitcher", 0, "pitches", "desc")
    params.update(
        {
            "group_by": "pitch-type",
            "pitchers_lookup[]": str(pitcher_id),
            "min_pitches": "0",
            "chk_stats_velocity": "on",
        }
    )
    return params


def _batter_pitch_type_params(batter_id: int) -> Dict[str, str]:
    params = _base_params("batter", 0, "pitches", "desc")
    params.update(
        {
            "group_by": "pitch-type",
            "batters_lookup[]": str(batter_id),
            "min_pitches": "0",
            "chk_stats_velocity": "on",
        }
    )
    return params


def _read_savant_csv(params: Dict[str, str]) -> pd.DataFrame:
    frame = _read_savant_csv_raw(params)
    if frame.empty:
        return frame
    return _shape_frame(frame)


def _read_savant_csv_raw(params: Dict[str, str]) -> pd.DataFrame:
    response = requests.get(SAVANT_CSV_URL, params=params, timeout=30)
    response.raise_for_status()
    text = response.text.lstrip("\ufeff")
    return pd.read_csv(StringIO(text))


def _shape_frame(frame: pd.DataFrame) -> pd.DataFrame:
    numeric_cols: List[str] = [
        "player_id",
        "pa",
        "pitches",
        "woba",
        "xwoba",
        "xba",
        "xslg",
        "slg",
        "obp",
        "launch_speed",
        "launch_angle",
        "hardhit_percent",
        "barrels_per_bbe_percent",
        "barrels_per_pa_percent",
        "k_percent",
        "bb_percent",
        "swing_miss_percent",
        "whiffs",
        "swings",
    ]
    for col in numeric_cols:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")

    frame["name"] = frame["player_name"].apply(_display_name)
    frame["luck_gap"] = frame["woba"] - frame["xwoba"]
    frame["whiff_percent"] = (frame["whiffs"] / frame["swings"] * 100).where(frame.get("swings", 0) > 0)
    keep = [
        "player_id",
        "name",
        "pa",
        "pitches",
        "woba",
        "xwoba",
        "luck_gap",
        "xba",
        "xslg",
        "obp",
        "slg",
        "launch_speed",
        "launch_angle",
        "hardhit_percent",
        "barrels_per_bbe_percent",
        "barrels_per_pa_percent",
        "k_percent",
        "bb_percent",
        "swing_miss_percent",
        "whiff_percent",
    ]
    return frame[[col for col in keep if col in frame.columns]]


def _shape_arsenal(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    numeric_cols = [
        "pitches",
        "total_pitches",
        "pitch_percent",
        "velocity",
        "spin_rate",
        "whiffs",
        "swings",
        "woba",
        "xwoba",
        "xba",
        "xslg",
        "launch_speed",
        "launch_angle",
        "hardhit_percent",
        "barrels_per_bbe_percent",
        "api_break_z_induced",
        "api_break_x_arm",
    ]
    for col in numeric_cols:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")

    frame["pitch_name"] = frame["pitch_type"].map(PITCH_NAMES).fillna(frame["pitch_type"])
    frame["whiff_percent"] = (frame["whiffs"] / frame["swings"] * 100).where(frame["swings"] > 0)
    keep = [
        "pitch_type",
        "pitch_name",
        "pitches",
        "pitch_percent",
        "velocity",
        "spin_rate",
        "whiff_percent",
        "woba",
        "xwoba",
        "xba",
        "xslg",
        "launch_speed",
        "launch_angle",
        "hardhit_percent",
        "barrels_per_bbe_percent",
        "api_break_z_induced",
        "api_break_x_arm",
    ]
    return frame[[col for col in keep if col in frame.columns]].sort_values("pitches", ascending=False)


def _display_name(raw: str) -> str:
    if not isinstance(raw, str) or "," not in raw:
        return raw
    last, first = [part.strip() for part in raw.split(",", 1)]
    return f"{first} {last}".strip()


PITCH_NAMES = {
    "FF": "Four-Seam",
    "SI": "Sinker",
    "FC": "Cutter",
    "SL": "Slider",
    "ST": "Sweeper",
    "CU": "Curveball",
    "KC": "Knuckle Curve",
    "CS": "Slow Curve",
    "CH": "Changeup",
    "FS": "Splitter",
    "FO": "Forkball",
    "KN": "Knuckleball",
    "SV": "Slurve",
}


@st.cache_data(ttl=15 * 60)
def get_savant_batters(min_pas: int = 25) -> pd.DataFrame:
    return _read_savant_csv(_base_params("batter", min_pas, "xwoba", "desc"))


@st.cache_data(ttl=15 * 60)
def get_savant_pitchers(min_pas: int = 25) -> pd.DataFrame:
    return _read_savant_csv(_base_params("pitcher", min_pas, "xwoba", "asc"))


@st.cache_data(ttl=15 * 60)
def get_pitcher_arsenal(pitcher_id: int) -> pd.DataFrame:
    return _shape_arsenal(_read_savant_csv_raw(_pitch_type_params(pitcher_id)))


@st.cache_data(ttl=15 * 60)
def get_batter_pitch_profile(batter_id: int) -> pd.DataFrame:
    return _shape_arsenal(_read_savant_csv_raw(_batter_pitch_type_params(batter_id)))


def get_player_expected_row(player_id: int, role: str) -> pd.Series | None:
    frame = get_savant_pitchers(10) if role == "Pitcher" else get_savant_batters(10)
    if frame.empty:
        return None
    rows = frame[frame["player_id"] == player_id]
    if rows.empty:
        return None
    return rows.iloc[0]


def format_savant_table(frame: pd.DataFrame, lower_is_better: bool = False) -> pd.DataFrame:
    if frame.empty:
        return frame
    out = frame.copy()
    percent_cols = ["pitch_percent", "hardhit_percent", "barrels_per_bbe_percent", "barrels_per_pa_percent", "k_percent", "bb_percent", "swing_miss_percent", "whiff_percent"]
    rate_cols = ["woba", "xwoba", "luck_gap", "xba", "xslg", "obp", "slg"]
    for col in rate_cols:
        if col in out.columns:
            out[col] = out[col].map(lambda value: "" if pd.isna(value) else f"{value:.3f}".replace("0.", ".").replace("-0.", "-."))
    for col in percent_cols:
        if col in out.columns:
            out[col] = out[col].map(lambda value: "" if pd.isna(value) else f"{value:.1f}%")
    for col in ["launch_speed", "launch_angle", "velocity", "api_break_z_induced", "api_break_x_arm"]:
        if col in out.columns:
            out[col] = out[col].map(lambda value: "" if pd.isna(value) else f"{value:.1f}")
    if "spin_rate" in out.columns:
        out["spin_rate"] = out["spin_rate"].map(lambda value: "" if pd.isna(value) else f"{value:.0f}")
    return out

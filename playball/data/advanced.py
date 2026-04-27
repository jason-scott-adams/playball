"""Advanced/computed season stats from MLB Stats API.

Fills the FIP, K-BB%, BB%, K%, ISO gap that FanGraphs would normally cover.
We do this locally because FanGraphs is now Cloudflare-protected — pybaseball
returns 403 against the FanGraphs URLs, verified 2026-04-26.

This module fetches per-player season totals from MLB Stats API and applies
the formulas in `playball/lib/stats.py`.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

import requests
import streamlit as st

from playball.lib.stats import (
    compute_bb_pct,
    compute_fip,
    compute_iso,
    compute_k_pct,
    compute_kbb_pct,
    fip_constant_for,
    parse_innings_pitched,
)

BASE_URL = "https://statsapi.mlb.com/api/v1"
USER_AGENT = "playball/0.2 (+https://github.com/jason-scott-adams/playball)"
REQUEST_TIMEOUT = 20


def _try_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fetch_player_stats(player_id: int, group: str, season: int) -> Optional[Dict[str, Any]]:
    url = f"{BASE_URL}/people/{player_id}/stats"
    params = {"stats": "season", "group": group, "season": season}
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    payload = response.json()
    for stat_block in payload.get("stats", []):
        for split in stat_block.get("splits", []):
            row = split.get("stat")
            if row:
                return row
    return None


@st.cache_data(ttl=15 * 60)
def fetch_pitcher_advanced(player_id: int, season: Optional[int] = None) -> Optional[Dict[str, Any]]:
    season = season or date.today().year
    row = _fetch_player_stats(player_id, "pitching", season)
    if not row:
        return None
    ip_decimal = parse_innings_pitched(row.get("inningsPitched"))
    fip = compute_fip(
        hr=row.get("homeRuns"),
        bb=row.get("baseOnBalls"),
        hbp=row.get("hitByPitch"),
        k=row.get("strikeOuts"),
        ip=ip_decimal,
        season=season,
    )
    tbf = row.get("battersFaced")
    k_pct = compute_k_pct(row.get("strikeOuts"), tbf)
    bb_pct = compute_bb_pct(row.get("baseOnBalls"), tbf)
    return {
        "player_id": player_id,
        "season": season,
        "innings_pitched": row.get("inningsPitched"),
        "batters_faced": tbf,
        "era": _try_float(row.get("era")),
        "whip": _try_float(row.get("whip")),
        "fip": fip,
        "fip_constant": fip_constant_for(season),
        "k_pct": k_pct,
        "bb_pct": bb_pct,
        "kbb_pct": compute_kbb_pct(row.get("strikeOuts"), row.get("baseOnBalls"), tbf),
        "home_runs": row.get("homeRuns"),
        "strikeouts": row.get("strikeOuts"),
        "walks": row.get("baseOnBalls"),
        "hbp": row.get("hitByPitch"),
    }


@st.cache_data(ttl=15 * 60)
def fetch_hitter_advanced(player_id: int, season: Optional[int] = None) -> Optional[Dict[str, Any]]:
    season = season or date.today().year
    row = _fetch_player_stats(player_id, "hitting", season)
    if not row:
        return None
    pa = row.get("plateAppearances")
    avg = _try_float(row.get("avg"))
    slg = _try_float(row.get("slg"))
    obp = _try_float(row.get("obp"))
    return {
        "player_id": player_id,
        "season": season,
        "plate_appearances": pa,
        "at_bats": row.get("atBats"),
        "home_runs": row.get("homeRuns"),
        "avg": avg,
        "obp": obp,
        "slg": slg,
        "ops": _try_float(row.get("ops")),
        "iso": compute_iso(slg, avg),
        "k_pct": compute_k_pct(row.get("strikeOuts"), pa),
        "bb_pct": compute_bb_pct(row.get("baseOnBalls"), pa),
        "kbb_pct": compute_kbb_pct(row.get("strikeOuts"), row.get("baseOnBalls"), pa),
    }

"""Live smoke test for every external data path Playball depends on.

Run before pulling latest into the laptop you'll use during games:

    python -m scripts.smoke_test

Exits non-zero on any failure. Designed to fail loud rather than degrade
silently when MLB Stats API, Baseball Savant, or our computed-stats path
breaks shape.
"""

from __future__ import annotations

import sys
import traceback
from datetime import date

USER_AGENT = "playball/0.2-smoketest"


def _ok(name: str, detail: str = "") -> None:
    print(f"  PASS  {name}{(' — ' + detail) if detail else ''}")


def _fail(name: str, exc: BaseException) -> None:
    print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")


def check_mlb_stats_api() -> bool:
    import requests
    try:
        r = requests.get(
            "https://statsapi.mlb.com/api/v1/teams/118/roster",
            params={"rosterType": "active", "season": date.today().year},
            timeout=20,
            headers={"User-Agent": USER_AGENT},
        )
        r.raise_for_status()
        roster = r.json().get("roster", [])
        assert len(roster) > 10, f"Royals roster came back empty (len={len(roster)})"
        sample = roster[0]
        for key in ("person", "position", "jerseyNumber"):
            assert key in sample, f"Missing expected key '{key}' in roster row"
        _ok("MLB Stats API roster", f"{len(roster)} players")
        return True
    except Exception as exc:
        _fail("MLB Stats API roster", exc)
        return False


def check_mlb_player_stats() -> bool:
    """Hits the per-player season stats endpoint that powers fetch_pitcher_advanced."""
    import requests
    try:
        # Cole Ragans 2025 — known to have rows
        r = requests.get(
            "https://statsapi.mlb.com/api/v1/people/666142/stats",
            params={"stats": "season", "group": "pitching", "season": 2025},
            timeout=20,
            headers={"User-Agent": USER_AGENT},
        )
        r.raise_for_status()
        payload = r.json()
        rows = []
        for block in payload.get("stats", []):
            rows.extend(block.get("splits", []))
        assert rows, "No pitching stats returned for sample player"
        st_row = rows[0]["stat"]
        for key in ("homeRuns", "baseOnBalls", "hitByPitch", "strikeOuts", "inningsPitched", "battersFaced"):
            assert key in st_row, f"FIP input '{key}' missing — formula will break"
        _ok("MLB Stats API per-player pitching", "all FIP inputs present")
        return True
    except Exception as exc:
        _fail("MLB Stats API per-player pitching", exc)
        return False


def check_baseball_savant() -> bool:
    """Hits the Savant CSV endpoint and confirms the columns Playball depends on."""
    import requests
    from io import StringIO
    import pandas as pd
    try:
        r = requests.get(
            "https://baseballsavant.mlb.com/statcast_search/csv",
            params={
                "all": "true",
                "hfGT": "R|",
                "hfSea": f"{date.today().year}|",
                "player_type": "batter",
                "group_by": "name",
                "min_pas": "25",
                "chk_stats_pa": "on",
                "chk_stats_woba": "on",
                "chk_stats_xwoba": "on",
            },
            timeout=30,
            headers={"User-Agent": USER_AGENT},
        )
        r.raise_for_status()
        text = r.text.lstrip("﻿")
        df = pd.read_csv(StringIO(text))
        # Early in season this can be empty — that's fine; we're verifying shape
        for col in ("player_name", "player_id", "woba", "xwoba"):
            assert col in df.columns, f"Savant CSV missing expected column '{col}' — shape drifted"
        _ok("Baseball Savant CSV", f"{len(df)} rows, columns intact")
        return True
    except Exception as exc:
        _fail("Baseball Savant CSV", exc)
        return False


def check_stats_module() -> bool:
    try:
        from playball.lib.stats import (
            compute_fip,
            compute_kbb_pct,
            compute_iso,
            parse_innings_pitched,
        )
        # Real Ragans 2025: HR=7, BB=20, HBP=2, K=98, IP="61.2"
        fip = compute_fip(hr=7, bb=20, hbp=2, k=98, ip=parse_innings_pitched("61.2"), season=2025)
        assert 2.4 <= fip <= 2.55, f"FIP fixture broke: {fip}"
        assert abs(compute_kbb_pct(100, 20, 400) - 20.0) < 0.001
        assert abs(compute_iso(".501", ".295") - 0.206) < 0.001
        _ok("Stats module (FIP, K-BB%, ISO formulas)")
        return True
    except Exception as exc:
        _fail("Stats module", exc)
        return False


def check_advanced_fetcher() -> bool:
    """Live fetch through the actual module Playball uses."""
    try:
        # Streamlit cache decorator is a passthrough when streamlit isn't running, but
        # importing it pulls streamlit; that's fine in dev.
        from playball.data.advanced import fetch_pitcher_advanced
        adv = fetch_pitcher_advanced(666142, season=2025)
        assert adv is not None, "fetch_pitcher_advanced returned None for Ragans 2025"
        for key in ("fip", "kbb_pct", "k_pct", "bb_pct", "era", "whip"):
            assert key in adv, f"Advanced row missing '{key}'"
        assert adv["fip"] is not None, "FIP came out None despite full season inputs"
        _ok("fetch_pitcher_advanced live path", f"FIP={adv['fip']:.2f}")
        return True
    except Exception as exc:
        _fail("fetch_pitcher_advanced", exc)
        return False


def check_watchlist_load() -> bool:
    try:
        from playball.data.watchlist import ensure_watchlist
        df = ensure_watchlist()
        assert len(df) > 0, "Watchlist is empty after ensure_watchlist()"
        for col in ("name", "player_id", "role", "org", "tags", "why", "notes", "created_at"):
            assert col in df.columns, f"Watchlist missing column '{col}'"
        _ok("Watchlist load", f"{len(df)} rows")
        return True
    except Exception as exc:
        _fail("Watchlist load", exc)
        return False


def main() -> int:
    print("Playball smoke test")
    print("===================")
    checks = [
        check_mlb_stats_api,
        check_mlb_player_stats,
        check_baseball_savant,
        check_stats_module,
        check_advanced_fetcher,
        check_watchlist_load,
    ]
    results = []
    for check in checks:
        try:
            results.append(check())
        except Exception:
            traceback.print_exc()
            results.append(False)
    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} checks passed.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st


BASE_URL = "https://statsapi.mlb.com/api/v1"
LIVE_URL = "https://statsapi.mlb.com/api/v1.1"
TEAM_ID_ROYALS = 118
USER_AGENT = "playball/0.2 (+https://github.com/jason-scott-adams/playball)"
DIVISION_NAMES = {
    200: "AL West",
    201: "AL East",
    202: "AL Central",
    203: "NL West",
    204: "NL East",
    205: "NL Central",
}


class MlbDataError(RuntimeError):
    pass


def _get_json(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    response = requests.get(url, params=params, timeout=20, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=60)
def get_royals_game(day: date) -> Optional[Dict[str, Any]]:
    data = _get_json(
        f"{BASE_URL}/schedule",
        {
            "sportId": 1,
            "teamId": TEAM_ID_ROYALS,
            "date": day.isoformat(),
            "hydrate": "probablePitcher(note),team,linescore",
        },
    )
    dates = data.get("dates", [])
    if not dates:
        return None
    games = dates[0].get("games", [])
    return games[0] if games else None


@st.cache_data(ttl=45)
def get_live_feed(game_pk: int) -> Dict[str, Any]:
    return _get_json(f"{LIVE_URL}/game/{game_pk}/feed/live")


@st.cache_data(ttl=60 * 60)
def get_active_roster(team_id: int = TEAM_ID_ROYALS, season: Optional[int] = None) -> pd.DataFrame:
    season = season or date.today().year
    data = _get_json(f"{BASE_URL}/teams/{team_id}/roster", {"rosterType": "active", "season": season})
    rows: List[Dict[str, Any]] = []
    for item in data.get("roster", []):
        person = item.get("person", {})
        position = item.get("position", {})
        rows.append(
            {
                "player_id": person.get("id"),
                "name": person.get("fullName"),
                "number": item.get("jerseyNumber", ""),
                "position": position.get("abbreviation"),
                "role": position.get("type"),
                "status": item.get("status", {}).get("description"),
            }
        )
    return pd.DataFrame(rows).sort_values(["role", "position", "name"], na_position="last")


@st.cache_data(ttl=10 * 60)
def get_leaders(stat_group: str, categories: List[str], limit: int = 10, season: Optional[int] = None) -> Dict[str, pd.DataFrame]:
    season = season or date.today().year
    data = _get_json(
        f"{BASE_URL}/stats/leaders",
        {
            "leaderCategories": ",".join(categories),
            "season": season,
            "sportId": 1,
            "leaderGameTypes": "R",
            "statGroup": stat_group,
            "limit": limit,
        },
    )
    out: Dict[str, pd.DataFrame] = {}
    for block in data.get("leagueLeaders", []):
        rows = []
        for leader in block.get("leaders", []):
            rows.append(
                {
                    "rank": leader.get("rank"),
                    "player": leader.get("person", {}).get("fullName"),
                    "team": leader.get("team", {}).get("name"),
                    "value": leader.get("value"),
                }
            )
        out[block.get("leaderCategory", "leaders")] = pd.DataFrame(rows)
    return out


@st.cache_data(ttl=10 * 60)
def get_standings(season: Optional[int] = None) -> pd.DataFrame:
    data = _get_json(
        f"{BASE_URL}/standings",
        {
            "leagueId": "103,104",
            "season": season or date.today().year,
            "standingsTypes": "regularSeason",
            "hydrate": "team",
        },
    )
    rows: List[Dict[str, Any]] = []
    for record in data.get("records", []):
        division = record.get("division", {}).get("id")
        for item in record.get("teamRecords", []):
            team = item.get("team", {})
            league_record = item.get("leagueRecord", {})
            rows.append(
                {
                    "division": DIVISION_NAMES.get(division, str(division)),
                    "rank": int(item.get("divisionRank", 0) or 0),
                    "team": team.get("name"),
                    "abbr": team.get("abbreviation"),
                    "wins": league_record.get("wins"),
                    "losses": league_record.get("losses"),
                    "pct": league_record.get("pct"),
                    "gb": item.get("divisionGamesBack") or item.get("gamesBack"),
                    "wc_gb": item.get("wildCardGamesBack"),
                    "streak": item.get("streak", {}).get("streakCode", ""),
                    "last_10": _split_record(item, "lastTen"),
                    "team_id": team.get("id"),
                }
            )
    return pd.DataFrame(rows).sort_values(["division", "rank"])


def _split_record(item: Dict[str, Any], split_type: str) -> str:
    for split in item.get("records", {}).get("splitRecords", []):
        if split.get("type") == split_type:
            return f"{split.get('wins')}-{split.get('losses')}"
    return ""


@st.cache_data(ttl=10 * 60)
def get_royals_schedule(start_date: date, end_date: date) -> pd.DataFrame:
    data = _get_json(
        f"{BASE_URL}/schedule",
        {
            "sportId": 1,
            "teamId": TEAM_ID_ROYALS,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "hydrate": "probablePitcher,team,linescore,venue",
        },
    )
    rows: List[Dict[str, Any]] = []
    for date_block in data.get("dates", []):
        for game in date_block.get("games", []):
            teams = game.get("teams", {})
            home = teams.get("home", {})
            away = teams.get("away", {})
            is_home = home.get("team", {}).get("id") == TEAM_ID_ROYALS
            royals_side = home if is_home else away
            opp_side = away if is_home else home
            rows.append(
                {
                    "date": game.get("officialDate"),
                    "matchup": f"{'vs' if is_home else '@'} {opp_side.get('team', {}).get('name')}",
                    "status": game.get("status", {}).get("detailedState"),
                    "score": _schedule_score(royals_side, opp_side, game),
                    "royals_starter": royals_side.get("probablePitcher", {}).get("fullName", "TBD"),
                    "opp_starter": opp_side.get("probablePitcher", {}).get("fullName", "TBD"),
                    "venue": game.get("venue", {}).get("name"),
                    "game_pk": game.get("gamePk"),
                }
            )
    return pd.DataFrame(rows)


def _schedule_score(royals_side: Dict[str, Any], opp_side: Dict[str, Any], game: Dict[str, Any]) -> str:
    state = game.get("status", {}).get("abstractGameState")
    if state in {"Preview", "Pre-Game"}:
        return ""
    royals_score = royals_side.get("score")
    opp_score = opp_side.get("score")
    if royals_score is None or opp_score is None:
        return ""
    marker = "W" if royals_side.get("isWinner") else "L" if state == "Final" else ""
    return f"{marker} {royals_score}-{opp_score}".strip()


def summarize_game(game: Dict[str, Any]) -> Dict[str, Any]:
    teams = game.get("teams", {})
    home = teams.get("home", {})
    away = teams.get("away", {})
    linescore = game.get("linescore", {})
    return {
        "game_pk": game.get("gamePk"),
        "state": game.get("status", {}).get("detailedState"),
        "reason": game.get("status", {}).get("reason"),
        "venue": game.get("venue", {}).get("name"),
        "home_name": home.get("team", {}).get("name"),
        "away_name": away.get("team", {}).get("name"),
        "home_score": home.get("score", 0),
        "away_score": away.get("score", 0),
        "home_record": home.get("leagueRecord", {}).get("pct"),
        "away_record": away.get("leagueRecord", {}).get("pct"),
        "home_probable": home.get("probablePitcher", {}).get("fullName", "TBD"),
        "away_probable": away.get("probablePitcher", {}).get("fullName", "TBD"),
        "inning": linescore.get("currentInningOrdinal", ""),
        "half": linescore.get("inningHalf", ""),
        "is_top": linescore.get("isTopInning"),
    }


def recent_plays(feed: Dict[str, Any], limit: int = 8) -> pd.DataFrame:
    rows = []
    for play in feed.get("liveData", {}).get("plays", {}).get("allPlays", [])[-limit:]:
        about = play.get("about", {})
        matchup = play.get("matchup", {})
        result = play.get("result", {})
        rows.append(
            {
                "inning": f"{about.get('halfInning', '')} {about.get('inning', '')}".strip(),
                "batter": matchup.get("batter", {}).get("fullName", ""),
                "pitcher": matchup.get("pitcher", {}).get("fullName", ""),
                "event": result.get("event", ""),
                "description": result.get("description", ""),
            }
        )
    return pd.DataFrame(rows)


def current_matchup(feed: Dict[str, Any]) -> Dict[str, Any]:
    plays = feed.get("liveData", {}).get("plays", {})
    current = plays.get("currentPlay") or {}
    matchup = current.get("matchup", {})
    count = current.get("count", {})
    about = current.get("about", {})
    result = current.get("result", {})
    return {
        "batter_id": matchup.get("batter", {}).get("id"),
        "batter": matchup.get("batter", {}).get("fullName", "Unknown"),
        "pitcher_id": matchup.get("pitcher", {}).get("id"),
        "pitcher": matchup.get("pitcher", {}).get("fullName", "Unknown"),
        "balls": count.get("balls", 0),
        "strikes": count.get("strikes", 0),
        "outs": count.get("outs", 0),
        "inning": about.get("inning"),
        "half": about.get("halfInning"),
        "event": result.get("event", ""),
        "description": result.get("description", ""),
    }


def live_scorebug_state(feed: Dict[str, Any]) -> Dict[str, Any]:
    linescore = feed.get("liveData", {}).get("linescore", {})
    offense = linescore.get("offense", {}) or {}
    defense = linescore.get("defense", {}) or {}
    return {
        "inning": linescore.get("currentInningOrdinal", ""),
        "half": linescore.get("inningHalf", ""),
        "balls": int(linescore.get("balls") or 0),
        "strikes": int(linescore.get("strikes") or 0),
        "outs": int(linescore.get("outs") or 0),
        "first": offense.get("first", {}).get("fullName", ""),
        "second": offense.get("second", {}).get("fullName", ""),
        "third": offense.get("third", {}).get("fullName", ""),
        "batter": offense.get("batter", {}).get("fullName", ""),
        "on_deck": offense.get("onDeck", {}).get("fullName", ""),
        "in_hole": offense.get("inHole", {}).get("fullName", ""),
        "pitcher": defense.get("pitcher", {}).get("fullName", ""),
        "batting_team": offense.get("team", {}).get("name", ""),
        "fielding_team": defense.get("team", {}).get("name", ""),
    }


def watch_note(summary: Dict[str, Any], matchup: Optional[Dict[str, Any]] = None) -> str:
    state = summary.get("state") or "Scheduled"
    if summary.get("reason"):
        return f"{state}: {summary['reason']}. Keep the live feed open; lineup and bullpen context still matter."
    if state in {"Final", "Game Over"}:
        return "Final. This is postgame mode: scan the swing events, bullpen usage, and who changed the game."
    if state in {"Scheduled", "Pre-Game", "Warmup"}:
        return "Pregame mode: compare probable starters, then watch the first trip through each lineup."
    if matchup:
        outs = matchup.get("outs", 0)
        count = f"{matchup.get('balls', 0)}-{matchup.get('strikes', 0)}"
        return f"Live: {matchup.get('batter')} vs. {matchup.get('pitcher')}, {count} count, {outs} out(s). This is the plate appearance to frame."
    return "Live mode: watch for leverage, bullpen decisions, and hard contact rather than only the box score."

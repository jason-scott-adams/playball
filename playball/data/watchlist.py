from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


WATCHLIST_PATH = Path(__file__).resolve().parents[2] / "data" / "watchlist.csv"

WATCHLIST_COLUMNS = ["name", "player_id", "role", "org", "tags", "why", "notes", "created_at"]

SEED_WATCHLIST: List[Dict[str, object]] = [
    {
        "name": "Bobby Witt Jr.",
        "player_id": 677951,
        "role": "Infielder",
        "org": "Royals",
        "tags": "Royals;MVP watch;core",
        "why": "Franchise star. Track whether expected contact says another MVP-level jump is coming.",
        "notes": "",
    },
    {
        "name": "Cole Ragans",
        "player_id": 666142,
        "role": "Pitcher",
        "org": "Royals",
        "tags": "Royals;ace;arsenal",
        "why": "Modern ace profile with bat-missing stuff. Watch fastball/changeup shape and command.",
        "notes": "",
    },
    {
        "name": "Vinnie Pasquantino",
        "player_id": 686469,
        "role": "Infielder",
        "org": "Royals",
        "tags": "Royals;OBP;contact quality",
        "why": "Good player for learning how OBP and contact quality can beat traditional RBI/AVG reads.",
        "notes": "",
    },
    {
        "name": "Jac Caglianone",
        "player_id": 695506,
        "role": "Outfielder",
        "org": "Royals",
        "tags": "Royals;prospect;power",
        "why": "Loud power. Watch swing decisions and damage on contact.",
        "notes": "",
    },
    {
        "name": "Carter Jensen",
        "player_id": 695600,
        "role": "Catcher",
        "org": "Royals",
        "tags": "Royals;prospect;catcher",
        "why": "Catcher offense changes roster math fast.",
        "notes": "",
    },
    {
        "name": "Yordan Alvarez",
        "player_id": 670541,
        "role": "Outfielder",
        "org": "Astros",
        "tags": "star;power;xwOBA",
        "why": "One of the cleanest modern examples of elite contact quality and damage.",
        "notes": "",
    },
    {
        "name": "Aaron Judge",
        "player_id": 592450,
        "role": "Outfielder",
        "org": "Yankees",
        "tags": "star;power;MVP watch",
        "why": "The baseline for current superstar offensive force.",
        "notes": "",
    },
    {
        "name": "Paul Skenes",
        "player_id": 694973,
        "role": "Pitcher",
        "org": "Pirates",
        "tags": "star;ace;arsenal",
        "why": "The modern power ace template.",
        "notes": "",
    },
    {
        "name": "Elly De La Cruz",
        "player_id": 682829,
        "role": "Infielder",
        "org": "Reds",
        "tags": "star;speed;power",
        "why": "Chaos player in the best way: speed, power, strikeouts, highlights.",
        "notes": "",
    },
    {
        "name": "James Wood",
        "player_id": 695578,
        "role": "Outfielder",
        "org": "Nationals",
        "tags": "young star;power;watch",
        "why": "Young impact bat with the kind of physical tools worth tracking early.",
        "notes": "",
    },
    {
        "name": "Konnor Griffin",
        "player_id": "",
        "role": "Prospect",
        "org": "Pirates",
        "tags": "prospect;top 100",
        "why": "Top prospect name to keep in the mental map.",
        "notes": "",
    },
    {
        "name": "Kevin McGonigle",
        "player_id": "",
        "role": "Prospect",
        "org": "Tigers",
        "tags": "prospect;AL Central",
        "why": "AL Central prospect threat with elite hit-tool buzz.",
        "notes": "",
    },
]


def ensure_watchlist() -> pd.DataFrame:
    WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not WATCHLIST_PATH.exists():
        frame = pd.DataFrame(SEED_WATCHLIST)
        frame["created_at"] = date.today().isoformat()
        frame.to_csv(WATCHLIST_PATH, index=False)
    return load_watchlist()


def load_watchlist() -> pd.DataFrame:
    if not WATCHLIST_PATH.exists():
        return ensure_watchlist()
    frame = pd.read_csv(WATCHLIST_PATH, dtype=str).fillna("")
    for col in WATCHLIST_COLUMNS:
        if col not in frame.columns:
            frame[col] = ""
    return frame[WATCHLIST_COLUMNS]


def save_watchlist(frame: pd.DataFrame) -> None:
    WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean = frame.copy().fillna("")
    for col in WATCHLIST_COLUMNS:
        if col not in clean.columns:
            clean[col] = ""
    clean = clean[WATCHLIST_COLUMNS].drop_duplicates(subset=["name"], keep="last")
    clean.to_csv(WATCHLIST_PATH, index=False)


def add_watch_player(name: str, player_id: Optional[str], role: str, org: str, tags: str, why: str, notes: str = "") -> None:
    frame = ensure_watchlist()
    player_id = str(player_id or "").strip()
    row = {
        "name": name.strip(),
        "player_id": player_id,
        "role": role.strip(),
        "org": org.strip(),
        "tags": tags.strip(),
        "why": why.strip(),
        "notes": notes.strip(),
        "created_at": date.today().isoformat(),
    }
    frame = frame[frame["name"].str.lower() != row["name"].lower()]
    save_watchlist(pd.concat([frame, pd.DataFrame([row])], ignore_index=True))


def remove_watch_player(name: str) -> None:
    frame = ensure_watchlist()
    save_watchlist(frame[frame["name"] != name])


def update_watch_notes(name: str, notes: str) -> None:
    frame = ensure_watchlist()
    frame.loc[frame["name"] == name, "notes"] = notes
    save_watchlist(frame)

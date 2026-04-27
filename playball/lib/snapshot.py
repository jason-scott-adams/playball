from __future__ import annotations

import pandas as pd

from playball.data.savant import get_player_expected_row


def _rate(value) -> str:
    if pd.isna(value):
        return ""
    return f"{value:.3f}".replace("0.", ".").replace("-0.", "-.")


def _snapshot_text(role: str, gap) -> str:
    if pd.isna(gap):
        return "Watch volume"
    if role == "Pitcher":
        if gap > 0.045:
            return "Results worse than expected"
        if gap < -0.045:
            return "Results better than expected"
        return "Aligned"
    if gap < -0.045:
        return "Due better"
    if gap > 0.045:
        return "Outrunning contact"
    return "Aligned"


def expected_snapshot(frame: pd.DataFrame) -> pd.DataFrame:
    """Map a watchlist DataFrame to a current-Statcast snapshot per player."""
    rows = []
    for item in frame.to_dict("records"):
        player_id = str(item.get("player_id", "")).strip()
        if not player_id.isdigit():
            continue
        role = item.get("role", "")
        try:
            expected = get_player_expected_row(int(player_id), role)
        except Exception:
            expected = None
        if expected is None:
            rows.append({
                "name": item["name"],
                "org": item["org"],
                "tags": item["tags"],
                "woba": "",
                "xwoba": "",
                "luck_gap": "",
                "snapshot": "No current row",
            })
            continue
        gap = expected.get("luck_gap")
        rows.append({
            "name": item["name"],
            "org": item["org"],
            "tags": item["tags"],
            "woba": _rate(expected.get("woba")),
            "xwoba": _rate(expected.get("xwoba")),
            "luck_gap": _rate(gap),
            "snapshot": _snapshot_text(role, gap),
        })
    return pd.DataFrame(rows)

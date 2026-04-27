from __future__ import annotations

from typing import Any


def pct_record(text: Any) -> str:
    if text in (None, ""):
        return "-"
    return str(text)


def clean_value(text: Any) -> str:
    if text in (None, ""):
        return "-"
    return str(text)

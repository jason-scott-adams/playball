from __future__ import annotations

import warnings
from typing import Optional, Union

# FanGraphs-published yearly FIP constant: league_ERA - league_raw_FIP.
# Update at season end. 2026 placeholder uses 2025's value until season has volume.
FIP_CONSTANTS: dict[int, float] = {
    2021: 3.17,
    2022: 3.10,
    2023: 3.13,
    2024: 3.13,
    2025: 3.10,
    2026: 3.10,  # placeholder; refresh once 2026 has FanGraphs volume
}

DEFAULT_FIP_CONSTANT = 3.10

Number = Union[int, float, str, None]


def _to_float(value: Number) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def parse_innings_pitched(ip: Number) -> float:
    """MLB API returns IP like "61.2" meaning 61 and 2/3 innings, not 61.2 decimal."""
    if ip is None or ip == "":
        return 0.0
    if isinstance(ip, (int, float)):
        # Treat as already-decimal innings (caller's responsibility).
        return float(ip)
    text = str(ip).strip()
    if "." not in text:
        return _to_float(text) or 0.0
    whole, _, frac = text.partition(".")
    whole_val = _to_float(whole) or 0.0
    if frac in ("0", "00", ""):
        return whole_val
    if frac == "1":
        return whole_val + 1 / 3
    if frac == "2":
        return whole_val + 2 / 3
    # Anything else is malformed for baseball IP notation. Warn loudly and treat
    # as whole innings — never silently coerce to decimal (FIP would be wrong).
    warnings.warn(
        f"parse_innings_pitched: unexpected fractional component {frac!r} in {text!r}; treating as whole innings",
        RuntimeWarning,
        stacklevel=2,
    )
    return whole_val


def compute_innings_outs(ip_decimal: float) -> int:
    return int(round(ip_decimal * 3))


def fip_constant_for(season: int) -> float:
    return FIP_CONSTANTS.get(season, DEFAULT_FIP_CONSTANT)


def compute_fip(*, hr: Number, bb: Number, hbp: Number, k: Number, ip: float, season: int) -> Optional[float]:
    """Canonical FIP: ((13*HR + 3*(BB+HBP) - 2*K) / IP) + season_constant."""
    ip_val = _to_float(ip)
    if ip_val is None or ip_val <= 0:
        return None
    hr_val = _to_float(hr) or 0.0
    bb_val = _to_float(bb) or 0.0
    hbp_val = _to_float(hbp) or 0.0
    k_val = _to_float(k) or 0.0
    raw = (13 * hr_val + 3 * (bb_val + hbp_val) - 2 * k_val) / ip_val
    return raw + fip_constant_for(season)


def compute_k_pct(k: Number, tbf: Number) -> Optional[float]:
    tbf_val = _to_float(tbf)
    if not tbf_val:
        return None
    k_val = _to_float(k) or 0.0
    return (k_val / tbf_val) * 100.0


def compute_bb_pct(bb: Number, tbf: Number) -> Optional[float]:
    tbf_val = _to_float(tbf)
    if not tbf_val:
        return None
    bb_val = _to_float(bb) or 0.0
    return (bb_val / tbf_val) * 100.0


def compute_kbb_pct(k: Number, bb: Number, tbf: Number) -> Optional[float]:
    k_pct = compute_k_pct(k, tbf)
    bb_pct = compute_bb_pct(bb, tbf)
    if k_pct is None or bb_pct is None:
        return None
    return k_pct - bb_pct


def compute_iso(slg: Number, avg: Number) -> Optional[float]:
    slg_val = _to_float(slg)
    avg_val = _to_float(avg)
    if slg_val is None or avg_val is None:
        return None
    return slg_val - avg_val

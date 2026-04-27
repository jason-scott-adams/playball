from __future__ import annotations

import math

import pytest

from playball.lib.stats import (
    DEFAULT_FIP_CONSTANT,
    FIP_CONSTANTS,
    compute_bb_pct,
    compute_fip,
    compute_innings_outs,
    compute_iso,
    compute_k_pct,
    compute_kbb_pct,
    parse_innings_pitched,
)


def _approx(a: float, b: float, tol: float = 0.05) -> bool:
    return abs(a - b) <= tol


class TestFIP:
    def test_cole_ragans_2025_partial_season(self):
        # Real values pulled from MLB API for Ragans 2025:
        # HR=7, BB=20, HBP=2, K=98, IP=61.2 (61.667 outs/3)
        ip = parse_innings_pitched("61.2")
        fip = compute_fip(hr=7, bb=20, hbp=2, k=98, ip=ip, season=2025)
        # Manually: (13*7 + 3*22 - 2*98)/61.667 + 3.10
        # = (91 + 66 - 196)/61.667 + 3.10 = (-39)/61.667 + 3.10 = -0.6324 + 3.10 = 2.47
        assert _approx(fip, 2.47, tol=0.05)

    def test_zero_innings_returns_none(self):
        assert compute_fip(hr=0, bb=0, hbp=0, k=0, ip=0.0, season=2025) is None

    def test_uses_default_constant_for_unknown_season(self):
        # Future season falls back to DEFAULT_FIP_CONSTANT
        ip = parse_innings_pitched("100.0")
        fip = compute_fip(hr=10, bb=30, hbp=2, k=100, ip=ip, season=2099)
        # (13*10 + 3*32 - 2*100)/100 + DEFAULT = (130+96-200)/100 + DEFAULT = 0.26 + DEFAULT
        expected = 0.26 + DEFAULT_FIP_CONSTANT
        assert _approx(fip, expected, tol=0.01)

    def test_known_seasons_have_constants(self):
        assert 2024 in FIP_CONSTANTS
        assert 2025 in FIP_CONSTANTS


class TestInningsParsing:
    def test_clean_whole(self):
        assert parse_innings_pitched("100.0") == 100.0
        assert parse_innings_pitched(100) == 100.0

    def test_baseball_thirds(self):
        # IP "61.2" means 61 and 2/3 innings, not 61.2 decimal
        assert _approx(parse_innings_pitched("61.2"), 61 + 2 / 3, tol=0.001)
        assert _approx(parse_innings_pitched("0.1"), 1 / 3, tol=0.001)
        assert _approx(parse_innings_pitched("0.2"), 2 / 3, tol=0.001)

    def test_none_or_blank(self):
        assert parse_innings_pitched(None) == 0.0
        assert parse_innings_pitched("") == 0.0

    def test_malformed_fraction_warns_and_returns_whole(self):
        import warnings

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            value = parse_innings_pitched("61.3")
            assert value == 61.0
            assert any(issubclass(w.category, RuntimeWarning) for w in caught)


class TestRates:
    def test_kbb_pct_basic(self):
        # K=100, BB=20, TBF=400 → K%=25, BB%=5, K-BB%=20
        assert _approx(compute_k_pct(100, 400), 25.0)
        assert _approx(compute_bb_pct(20, 400), 5.0)
        assert _approx(compute_kbb_pct(100, 20, 400), 20.0)

    def test_kbb_pct_zero_tbf(self):
        assert compute_k_pct(0, 0) is None
        assert compute_bb_pct(0, 0) is None
        assert compute_kbb_pct(0, 0, 0) is None

    def test_iso_basic(self):
        # SLG .500, AVG .250 → ISO .250
        assert _approx(compute_iso(0.500, 0.250), 0.250, tol=0.001)

    def test_iso_handles_strings(self):
        # MLB API returns SLG/AVG as strings like ".501"
        assert _approx(compute_iso(".501", ".295"), 0.206, tol=0.001)

    def test_iso_none_inputs(self):
        assert compute_iso(None, 0.250) is None
        assert compute_iso(0.500, None) is None


class TestInningsOuts:
    def test_outs_round_trip(self):
        assert compute_innings_outs(61 + 2 / 3) == 185
        assert compute_innings_outs(0.0) == 0

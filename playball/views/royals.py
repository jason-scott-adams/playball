from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from playball.data.advanced import fetch_hitter_advanced, fetch_pitcher_advanced
from playball.data.savant import format_savant_table, get_savant_batters, get_savant_pitchers


TRACKING_NOTES = {
    "Bobby Witt Jr.": "Franchise star. Watch power/speed plus chase rate; he can dominate without needing batting average luck.",
    "Cole Ragans": "Modern ace profile. Track strikeouts, walks, and whether the fastball/changeup combo is missing bats.",
    "Vinnie Pasquantino": "OBP and contact-quality player. Surface average can undersell him if the walks and hard contact are there.",
    "Maikel Garcia": "Useful test case for old-school vs modern value: defense, speed, contact, and OBP all matter.",
    "Carter Jensen": "Prospect-to-big-league bridge. Watch catcher offense, patience, and whether power is arriving.",
    "Jac Caglianone": "Loud tools profile. Focus on swing decisions and damage on contact more than one-week slumps.",
}


def render_royals(roster: pd.DataFrame) -> None:
    st.subheader("Royals Pulse")
    st.markdown(
        "Roster plus expected-stat context. This is where surface performance starts getting interrogated."
    )

    if roster.empty:
        st.info("Roster data is unavailable.")
        return

    hitters = roster[roster["role"] != "Pitcher"].copy()
    pitchers = roster[roster["role"] == "Pitcher"].copy()

    c1, c2, c3 = st.columns(3)
    c1.metric("Active Players", len(roster))
    c2.metric("Position Players", len(hitters))
    c3.metric("Pitchers", len(pitchers))

    names = roster["name"].dropna().tolist()
    selected = st.selectbox(
        "Spotlight player",
        names,
        index=names.index("Bobby Witt Jr.") if "Bobby Witt Jr." in names else 0,
        key="royals_pulse_player",
    )
    st.markdown(
        f"<div class='watch-note'>{html.escape(TRACKING_NOTES.get(selected, 'Add a note here once this player shows a trend worth tracking.'))}</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        st.markdown("#### Position Players")
        st.dataframe(hitters[["number", "name", "position", "status"]], width="stretch", hide_index=True)
    with right:
        st.markdown("#### Pitchers")
        st.dataframe(pitchers[["number", "name", "position", "status"]], width="stretch", hide_index=True)

    st.markdown("#### Royals Expected Stats")
    batters = get_savant_batters(10)
    pitchers_adv = get_savant_pitchers(10)
    hitter_ids = set(hitters["player_id"].dropna().astype(int))
    pitcher_ids = set(pitchers["player_id"].dropna().astype(int))
    royals_batters = batters[batters["player_id"].isin(hitter_ids)].sort_values("xwoba", ascending=False)
    royals_pitchers = pitchers_adv[pitchers_adv["player_id"].isin(pitcher_ids)].sort_values("xwoba", ascending=True)

    adv_left, adv_right = st.columns(2)
    with adv_left:
        st.markdown("##### Hitters")
        if royals_batters.empty:
            st.caption("No Royals hitter rows met the minimum yet.")
        else:
            st.dataframe(
                format_savant_table(royals_batters)[["name", "pa", "woba", "xwoba", "luck_gap", "xba", "xslg", "hardhit_percent"]],
                width="stretch",
                hide_index=True,
            )
    with adv_right:
        st.markdown("##### Pitchers")
        if royals_pitchers.empty:
            st.caption("No Royals pitcher rows met the minimum yet.")
        else:
            st.dataframe(
                format_savant_table(royals_pitchers)[["name", "pa", "woba", "xwoba", "luck_gap", "xba", "xslg", "hardhit_percent"]],
                width="stretch",
                hide_index=True,
            )

    st.markdown("#### Royals Modern Stats (computed from MLB Stats API)")
    st.caption(
        "FIP, K-BB%, OBP and ISO computed locally. wRC+, WAR, Stuff+ would require FanGraphs, "
        "which is currently Cloudflare-protected and not exposed via a free API — see README for status."
    )
    hit_table, pit_table, hit_fail, pit_fail = _build_modern_tables(hitters, pitchers)
    n_hitters = int((hitters["player_id"].notna()).sum()) if "player_id" in hitters.columns else 0
    n_pitchers = int((pitchers["player_id"].notna()).sum()) if "player_id" in pitchers.columns else 0
    h_col, p_col = st.columns(2)
    with h_col:
        st.markdown("##### Hitter Box")
        if hit_table.empty:
            if hit_fail and hit_fail == n_hitters and n_hitters > 0:
                st.warning("MLB Stats API unavailable — every hitter request failed.")
            else:
                st.caption("No hitter season totals yet.")
        else:
            st.dataframe(hit_table, width="stretch", hide_index=True)
            if hit_fail:
                st.caption(f"{hit_fail} hitter request(s) failed; showing the rest.")
    with p_col:
        st.markdown("##### Pitcher Box")
        if pit_table.empty:
            if pit_fail and pit_fail == n_pitchers and n_pitchers > 0:
                st.warning("MLB Stats API unavailable — every pitcher request failed.")
            else:
                st.caption("No pitcher season totals yet.")
        else:
            st.dataframe(pit_table, width="stretch", hide_index=True)
            if pit_fail:
                st.caption(f"{pit_fail} pitcher request(s) failed; showing the rest.")


def _fmt_rate(value) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return f"{value:.3f}".replace("0.", ".").replace("-0.", "-.")


def _fmt_pct(value) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return f"{value:.1f}%"


def _fmt_two(value) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return f"{value:.2f}"


def _fmt_int(value) -> str:
    if value is None or value == "":
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return str(value)


def _build_modern_tables(
    hitters: pd.DataFrame, pitchers: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, int, int]:
    """Returns (hitters_df, pitchers_df, hitter_failures, pitcher_failures)."""
    hit_rows = []
    hitter_failures = 0
    for _, r in hitters.iterrows():
        pid = r.get("player_id")
        if pd.isna(pid):
            continue
        try:
            adv = fetch_hitter_advanced(int(pid))
        except Exception:
            adv = None
            hitter_failures += 1
        if not adv:
            continue
        # Keep numeric sort key separate from the displayed value so sort never
        # sees mixed int/str. Display layer formats from the raw numeric column.
        hit_rows.append({
            "name": r.get("name"),
            "_pa_num": pd.to_numeric(adv.get("plate_appearances"), errors="coerce"),
            "PA": _fmt_int(adv.get("plate_appearances")),
            "AVG": _fmt_rate(adv.get("avg")),
            "OBP": _fmt_rate(adv.get("obp")),
            "SLG": _fmt_rate(adv.get("slg")),
            "ISO": _fmt_rate(adv.get("iso")),
            "BB%": _fmt_pct(adv.get("bb_pct")),
            "K%": _fmt_pct(adv.get("k_pct")),
            "HR": _fmt_int(adv.get("home_runs")),
        })
    pit_rows = []
    pitcher_failures = 0
    for _, r in pitchers.iterrows():
        pid = r.get("player_id")
        if pd.isna(pid):
            continue
        try:
            adv = fetch_pitcher_advanced(int(pid))
        except Exception:
            adv = None
            pitcher_failures += 1
        if not adv:
            continue
        ip_raw = adv.get("innings_pitched")
        pit_rows.append({
            "name": r.get("name"),
            "_ip_num": _ip_to_decimal(ip_raw),
            "IP": ip_raw if ip_raw not in (None, "") else "",
            "ERA": _fmt_two(adv.get("era")),
            "FIP": _fmt_two(adv.get("fip")),
            "WHIP": _fmt_two(adv.get("whip")),
            "K%": _fmt_pct(adv.get("k_pct")),
            "BB%": _fmt_pct(adv.get("bb_pct")),
            "K-BB%": _fmt_pct(adv.get("kbb_pct")),
        })
    hit_df = pd.DataFrame(hit_rows)
    pit_df = pd.DataFrame(pit_rows)
    if not hit_df.empty:
        hit_df = hit_df.sort_values("_pa_num", ascending=False, na_position="last").drop(columns=["_pa_num"])
    if not pit_df.empty:
        pit_df = pit_df.sort_values("_ip_num", ascending=False, na_position="last").drop(columns=["_ip_num"])
    return hit_df, pit_df, hitter_failures, pitcher_failures


def _ip_to_decimal(ip_raw) -> float:
    """Local copy: converts MLB IP notation (61.2 = 61⅔) to a numeric sort key."""
    from playball.lib.stats import parse_innings_pitched
    return parse_innings_pitched(ip_raw)

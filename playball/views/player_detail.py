from __future__ import annotations

import pandas as pd
import streamlit as st

from playball.data.savant import (
    format_savant_table,
    get_batter_pitch_profile,
    get_pitcher_arsenal,
    get_player_expected_row,
)
from playball.lib.charts import pitch_mix_chart


def _fmt_rate(value) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:.3f}".replace("0.", ".").replace("-0.", "-.")


def _fmt_pct(value) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:.1f}%"


def _player_note(name: str, role: str, expected_row, detail: pd.DataFrame) -> str:
    if expected_row is None:
        return f"{name} does not have enough current-season Statcast volume yet. Start with role, usage, and recent game context."

    gap = expected_row.get("luck_gap")
    if role == "Pitcher":
        if gap > 0.045:
            luck = "Results have been rougher than the contact profile suggests."
        elif gap < -0.045:
            luck = "Results are beating the expected contact profile, so watch for regression risk."
        else:
            luck = "Actual and expected contact quality are mostly aligned."
        if not detail.empty:
            best = detail.sort_values("xwoba", ascending=True).iloc[0]
            primary = detail.iloc[0]
            return f"{luck} Primary pitch: {primary['pitch_name']}. Best expected-result pitch: {best['pitch_name']}."
        return luck

    if gap < -0.045:
        luck = "The contact quality is better than the surface results."
    elif gap > 0.045:
        luck = "The surface line is running ahead of the expected contact."
    else:
        luck = "The surface line and expected contact are mostly telling the same story."
    if not detail.empty:
        best = detail.sort_values("xwoba", ascending=False).iloc[0]
        trouble = detail.sort_values("whiff_percent", ascending=False).iloc[0]
        return f"{luck} Best pitch-type results: {best['pitch_name']}. Biggest swing-miss area so far: {trouble['pitch_name']}."
    return luck


def _expected_metrics(row) -> None:
    cols = st.columns(6)
    cols[0].metric("PA/BF", int(row.get("pa", 0)) if not pd.isna(row.get("pa")) else "-")
    cols[1].metric("wOBA", _fmt_rate(row.get("woba")))
    cols[2].metric("xwOBA", _fmt_rate(row.get("xwoba")))
    cols[3].metric("Luck Gap", _fmt_rate(row.get("luck_gap")))
    cols[4].metric("xBA", _fmt_rate(row.get("xba")))
    cols[5].metric("xSLG", _fmt_rate(row.get("xslg")))


def _contact_metrics(row) -> None:
    cols = st.columns(5)
    cols[0].metric("EV", f"{row.get('launch_speed'):.1f}" if not pd.isna(row.get("launch_speed")) else "-")
    cols[1].metric("Launch", f"{row.get('launch_angle'):.1f}" if not pd.isna(row.get("launch_angle")) else "-")
    cols[2].metric("Hard-Hit", _fmt_pct(row.get("hardhit_percent")))
    cols[3].metric("Barrel/BIP", _fmt_pct(row.get("barrels_per_bbe_percent")))
    cols[4].metric("Whiff", _fmt_pct(row.get("whiff_percent")))


def _select_existing(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return frame[[col for col in columns if col in frame.columns]]


def render_player_detail(roster: pd.DataFrame) -> None:
    st.subheader("Player Detail")
    st.markdown("A focused read on one player: expected results, contact quality, and pitch-type shape.")

    if roster.empty:
        st.info("Roster data is unavailable.")
        return

    names = roster["name"].dropna().tolist()
    default_index = names.index("Bobby Witt Jr.") if "Bobby Witt Jr." in names else 0
    selected = st.selectbox("Player", names, index=default_index)
    player = roster[roster["name"] == selected].iloc[0]
    player_id = int(player["player_id"])
    role = player["role"]

    st.markdown(f"### {selected}")
    bio = st.columns(4)
    bio[0].metric("Role", role)
    bio[1].metric("Position", player["position"])
    bio[2].metric("Number", player["number"] or "-")
    bio[3].metric("Status", player["status"] or "-")

    expected = get_player_expected_row(player_id, role)
    detail = pd.DataFrame()
    try:
        detail = get_pitcher_arsenal(player_id) if role == "Pitcher" else get_batter_pitch_profile(player_id)
    except Exception as exc:
        st.caption(f"Pitch-type detail unavailable: {exc}")

    st.markdown("#### Expected Stat Card")
    if expected is None:
        st.info("No current-season expected-stat row yet.")
    else:
        _expected_metrics(expected)
        _contact_metrics(expected)

    st.markdown(f"<div class='watch-note'>{_player_note(selected, role, expected, detail)}</div>", unsafe_allow_html=True)

    if detail.empty:
        return

    if role == "Pitcher":
        st.markdown("#### Pitch Arsenal")
        display = _select_existing(
            format_savant_table(detail),
            [
                "pitch_name",
                "pitches",
                "pitch_percent",
                "velocity",
                "spin_rate",
                "whiff_percent",
                "woba",
                "xwoba",
                "hardhit_percent",
                "api_break_z_induced",
                "api_break_x_arm",
            ],
        ).rename(
            columns={
                "pitch_name": "pitch",
                "pitch_percent": "usage",
                "velocity": "velo",
                "spin_rate": "spin",
                "whiff_percent": "whiff",
                "hardhit_percent": "hard-hit",
                "api_break_z_induced": "vert break",
                "api_break_x_arm": "arm-side break",
            }
        )
        st.dataframe(display, width="stretch", hide_index=True)
        st.plotly_chart(pitch_mix_chart(detail, "Pitch Mix and Expected Damage"), use_container_width=True)
    else:
        st.markdown("#### Batter vs Pitch Types")
        display = _select_existing(
            format_savant_table(detail),
            [
                "pitch_name",
                "pitches",
                "pitch_percent",
                "woba",
                "xwoba",
                "xba",
                "xslg",
                "whiff_percent",
                "launch_speed",
                "hardhit_percent",
            ],
        ).rename(
            columns={
                "pitch_name": "pitch",
                "pitch_percent": "seen",
                "whiff_percent": "whiff",
                "launch_speed": "EV",
                "hardhit_percent": "hard-hit",
            }
        )
        st.dataframe(display, width="stretch", hide_index=True)
        st.plotly_chart(pitch_mix_chart(detail, "Pitch Types Seen and Expected Damage"), use_container_width=True)

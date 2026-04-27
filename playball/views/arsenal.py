from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from playball.data.savant import format_savant_table, get_pitcher_arsenal
from playball.lib.charts import pitch_mix_chart


def _fmt_xwoba_metric(name: str, value: float) -> str:
    if pd.isna(value):
        return f"{name} —"
    return f"{name} .{int(value * 1000):03d}"


def _fmt_pct_metric(name: str, value: float) -> str:
    if pd.isna(value):
        return f"{name} —"
    return f"{name} {value:.1f}%"


def _fmt_velo_metric(name: str, value: float) -> str:
    if pd.isna(value):
        return f"{name} —"
    return f"{name} {value:.1f}"


def render_arsenal_lab(roster: pd.DataFrame) -> None:
    st.subheader("Arsenal Lab")
    st.markdown("Pick a Royals pitcher and see the shape of his plan: usage, velocity, whiffs, contact quality, and movement.")

    pitchers = roster[roster["role"] == "Pitcher"].copy()
    if pitchers.empty:
        st.info("No pitchers found on the active roster.")
        return

    names = pitchers["name"].dropna().tolist()
    default_index = names.index("Cole Ragans") if "Cole Ragans" in names else 0
    selected = st.selectbox("Pitcher", names, index=default_index, key="arsenal_lab_pitcher")
    pid_raw = pitchers.loc[pitchers["name"] == selected, "player_id"].iloc[0]
    if pd.isna(pid_raw):
        st.warning("Player ID unavailable for the selected pitcher.")
        return
    player_id = int(pid_raw)

    try:
        arsenal = get_pitcher_arsenal(player_id)
    except Exception as exc:
        st.warning(f"Could not load arsenal data: {exc}")
        return

    if arsenal.empty:
        st.info("No pitch-level grouped data found yet.")
        return

    c1, c2, c3, c4 = st.columns(4)
    primary = arsenal.iloc[0]
    best = arsenal.sort_values("xwoba", ascending=True, na_position="last").iloc[0]
    whiff = arsenal.sort_values("whiff_percent", ascending=False, na_position="last").iloc[0]
    hardest = arsenal.sort_values("velocity", ascending=False, na_position="last").iloc[0]
    c1.metric("Primary Pitch", primary["pitch_name"])
    c2.metric("Best xwOBA", _fmt_xwoba_metric(best["pitch_name"], best["xwoba"]))
    c3.metric("Whiff Pitch", _fmt_pct_metric(whiff["pitch_name"], whiff["whiff_percent"]))
    c4.metric("Top Velo", _fmt_velo_metric(hardest["pitch_name"], hardest["velocity"]))

    display = format_savant_table(arsenal)[
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
            "barrels_per_bbe_percent",
            "api_break_z_induced",
            "api_break_x_arm",
        ]
    ].rename(
        columns={
            "pitch_name": "pitch",
            "pitch_percent": "usage",
            "velocity": "velo",
            "spin_rate": "spin",
            "whiff_percent": "whiff",
            "hardhit_percent": "hard-hit",
            "barrels_per_bbe_percent": "barrel/bbe",
            "api_break_z_induced": "vert break",
            "api_break_x_arm": "arm-side break",
        }
    )
    st.dataframe(display, width="stretch", hide_index=True)

    st.plotly_chart(pitch_mix_chart(arsenal, "Pitch Mix and Expected Damage"), use_container_width=True)

    st.markdown(
        f"<div class='watch-note'>Watch how {html.escape(selected)} pairs the {html.escape(str(primary['pitch_name']))} with "
        f"{html.escape(str(best['pitch_name']))}. Usage tells you the plan; xwOBA and whiff rate tell you whether hitters are solving it.</div>",
        unsafe_allow_html=True,
    )

from __future__ import annotations

import pandas as pd
import streamlit as st

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
    selected = st.selectbox("Spotlight player", names, index=names.index("Bobby Witt Jr.") if "Bobby Witt Jr." in names else 0)
    st.markdown(f"<div class='watch-note'>{TRACKING_NOTES.get(selected, 'Add a note here once this player shows a trend worth tracking.')}</div>", unsafe_allow_html=True)

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

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from playball.data.mlb import TEAM_ID_ROYALS, get_royals_schedule, get_standings


def render_league_context() -> None:
    st.subheader("League Context")
    st.markdown("Standings and schedule context so the player-level rabbit holes stay attached to the season.")

    standings = get_standings()
    if standings.empty:
        st.info("Standings are unavailable.")
    else:
        royals = standings[standings["team_id"] == TEAM_ID_ROYALS]
        if not royals.empty:
            row = royals.iloc[0]
            cols = st.columns(5)
            cols[0].metric("Royals", f"{row['wins']}-{row['losses']}")
            cols[1].metric("Pct", row["pct"])
            cols[2].metric("Division", row["division"])
            cols[3].metric("Rank", f"#{row['rank']}")
            cols[4].metric("GB", row["gb"])

        st.markdown("#### AL Central")
        central = standings[standings["division"] == "AL Central"].drop(columns=["team_id"])
        st.dataframe(central, width="stretch", hide_index=True)

        st.markdown("#### Full Standings")
        divisions = list(standings["division"].dropna().unique())
        tabs = st.tabs(divisions)
        for tab, division in zip(tabs, divisions):
            with tab:
                table = standings[standings["division"] == division].drop(columns=["team_id"])
                st.dataframe(table, width="stretch", hide_index=True)

    st.markdown("#### Royals Schedule")
    today = date.today()
    left, right = st.columns(2)
    start = left.date_input("Schedule start", today - timedelta(days=14))
    end = right.date_input("Schedule end", today + timedelta(days=21))
    if start > end:
        st.warning("Start date must be before end date.")
        return

    schedule = get_royals_schedule(start, end)
    if schedule.empty:
        st.info("No Royals games found in that window.")
    else:
        st.dataframe(schedule.drop(columns=["game_pk"]), width="stretch", hide_index=True)

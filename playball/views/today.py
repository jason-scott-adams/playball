from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from playball.data.mlb import TEAM_ID_ROYALS, get_live_feed, get_royals_schedule, get_standings, live_scorebug_state, summarize_game, watch_note
from playball.data.watchlist import ensure_watchlist
from playball.lib.scoreboard import render_scorebug_html
from playball.views.my_guys import _expected_snapshot


def render_today(game, roster: pd.DataFrame) -> None:
    st.markdown(
        """
        <div class="pb-hero">
          <div class="muted">Today Briefing</div>
          <h2 style="margin:.1rem 0 .35rem;">What matters for the Royals tonight</h2>
          <div class="gold">Game state, standings pressure, and the players worth watching.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    standings = get_standings()
    royals = standings[standings["team_id"] == TEAM_ID_ROYALS] if not standings.empty else pd.DataFrame()

    top = st.columns(4)
    if not royals.empty:
        row = royals.iloc[0]
        top[0].metric("Royals", f"{row['wins']}-{row['losses']}")
        top[1].metric("AL Central", f"#{row['rank']}")
        top[2].metric("GB", row["gb"])
        top[3].metric("Last 10", row["last_10"])
    else:
        top[0].metric("Royals", "-")
        top[1].metric("AL Central", "-")
        top[2].metric("GB", "-")
        top[3].metric("Last 10", "-")

    if game:
        summary = summarize_game(game)
        st.markdown(f"#### {summary['away_name']} at {summary['home_name']}")
        cols = st.columns(5)
        cols[0].metric("State", summary["state"] or "Unknown")
        cols[1].metric(summary["away_name"] or "Away", summary["away_score"])
        cols[2].metric(summary["home_name"] or "Home", summary["home_score"])
        cols[3].metric("Inning", f"{summary['half']} {summary['inning']}".strip() or "-")
        cols[4].metric("Venue", summary["venue"] or "-")

        feed = None
        matchup = None
        if summary.get("game_pk") and summary["state"] not in {"Scheduled", "Pre-Game", "Warmup"}:
            try:
                feed = get_live_feed(int(summary["game_pk"]))
            except Exception:
                feed = None
        if feed:
            from playball.data.mlb import current_matchup

            matchup = current_matchup(feed)
            st.markdown(render_scorebug_html(live_scorebug_state(feed)), unsafe_allow_html=True)
        st.markdown(f"<div class='watch-note'>{watch_note(summary, matchup)}</div>", unsafe_allow_html=True)
    else:
        st.info("No Royals game found today.")

    left, right = st.columns([1, 1])
    with left:
        st.markdown("#### Next Royals Games")
        schedule = get_royals_schedule(date.today(), date.today() + timedelta(days=10))
        if schedule.empty:
            st.caption("No upcoming games found.")
        else:
            st.dataframe(schedule.drop(columns=["game_pk"]).head(8), width="stretch", hide_index=True)

    with right:
        st.markdown("#### My Guys To Check")
        watch = ensure_watchlist()
        snapshot = _expected_snapshot(watch.head(12))
        if snapshot.empty:
            st.caption("No watchlist snapshots yet.")
        else:
            priority = snapshot[snapshot["snapshot"] != "Aligned"]
            show = priority if not priority.empty else snapshot.head(6)
            st.dataframe(show[["name", "org", "xwoba", "luck_gap", "snapshot"]], width="stretch", hide_index=True)

    st.markdown("#### Modern Stat Lesson")
    st.markdown(
        "<div class='watch-note'><strong>xwOBA</strong> asks what a player's results should look like from contact quality and related inputs. "
        "When it disagrees with wOBA, that is not an answer by itself. It is a reason to watch more closely.</div>",
        unsafe_allow_html=True,
    )

from __future__ import annotations

import html
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from playball.data.mlb import (
    TEAM_ID_ROYALS,
    current_matchup,
    get_live_feed,
    get_royals_schedule,
    get_standings,
    live_scorebug_state,
    summarize_game,
    watch_note,
)
from playball.data.watchlist import ensure_watchlist
from playball.lib.scoreboard import render_scorebug_html
from playball.lib.snapshot import expected_snapshot


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
            except Exception as exc:
                feed = None
                st.caption(f"Live feed unavailable: {exc}")
        if feed:
            matchup = current_matchup(feed)
            st.markdown(render_scorebug_html(live_scorebug_state(feed)), unsafe_allow_html=True)
        st.markdown(
            f"<div class='watch-note'>{html.escape(watch_note(summary, matchup))}</div>",
            unsafe_allow_html=True,
        )
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
        snapshot = expected_snapshot(watch.head(12))
        if snapshot.empty:
            st.caption("No watchlist snapshots yet.")
        else:
            priority = snapshot[snapshot["snapshot"] != "Aligned"]
            show = priority if not priority.empty else snapshot.head(6)
            st.dataframe(show[["name", "org", "xwoba", "luck_gap", "snapshot"]], width="stretch", hide_index=True)

    st.markdown("#### Modern Stat Lesson")
    lesson = _stat_lesson(date.today())
    st.markdown(
        f"<div class='watch-note'><strong>{html.escape(lesson['title'])}.</strong> {html.escape(lesson['body'])}</div>",
        unsafe_allow_html=True,
    )


_LESSONS = [
    {
        "title": "OBP",
        "body": "How often a hitter avoids making an out — walks, hits, hit-by-pitch, divided by plate appearances. .350 is good, .400 is elite. The single most reliable hitter stat.",
    },
    {
        "title": "wOBA",
        "body": "Like OBP but each event is weighted by how much it actually contributes to scoring runs. A double counts more than a single; a walk counts less than a homer. Same scale as OBP — read it the same way.",
    },
    {
        "title": "xwOBA",
        "body": "What wOBA should be based on exit velocity and launch angle on every batted ball. Compare to actual wOBA: gap means luck (good or bad). The Luck Index tab is built on this gap.",
    },
    {
        "title": "Barrel %",
        "body": "Share of batted balls hit at the ideal exit-velocity-plus-launch-angle combo for extra bases. Above 10% is real damage. Tells you who is hitting the ball with intent.",
    },
    {
        "title": "FIP",
        "body": "ERA stripped of defense and luck — uses only HRs, walks, hit-by-pitch, and strikeouts. If a pitcher's ERA and FIP disagree, the gap usually closes over time.",
    },
    {
        "title": "K-BB%",
        "body": "Strikeout rate minus walk rate. The single cleanest pitcher dominance number. 20% is excellent, 25% is ace.",
    },
    {
        "title": "ISO",
        "body": "SLG minus AVG — pure raw power, the part of slugging that isn't singles. .200 is a power hitter, .250 is elite.",
    },
]


def _stat_lesson(today: date) -> dict:
    # Rotates through the lesson set so the front-door doesn't repeat the same line every visit.
    return _LESSONS[today.toordinal() % len(_LESSONS)]

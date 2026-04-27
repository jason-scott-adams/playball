from __future__ import annotations

import html
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from playball.data.mlb import current_matchup, get_live_feed, live_scorebug_state, recent_plays, summarize_game, watch_note
from playball.data.savant import format_savant_table, get_batter_pitch_profile, get_pitcher_arsenal
from playball.lib.charts import pitch_mix_chart
from playball.lib.scoreboard import render_scorebug_html


def render_game_companion(game: Optional[Dict[str, Any]]) -> None:
    if not game:
        st.info("No Royals game found for this date.")
        return

    summary = summarize_game(game)
    is_liveish = summary["state"] not in {"Scheduled", "Pre-Game", "Warmup"}

    matchup = None
    feed = None
    if summary.get("game_pk") and is_liveish:
        try:
            feed = get_live_feed(int(summary["game_pk"]))
            matchup = current_matchup(feed)
        except Exception as exc:
            st.warning(f"Live feed is unavailable right now: {exc}")

    st.subheader(f"{summary['away_name']} at {summary['home_name']}")
    cols = st.columns(5)
    cols[0].metric("State", summary["state"] or "Unknown")
    cols[1].metric(summary["away_name"] or "Away", summary["away_score"])
    cols[2].metric(summary["home_name"] or "Home", summary["home_score"])
    cols[3].metric("Inning", f"{summary['half']} {summary['inning']}".strip() or "-")
    cols[4].metric("Venue", summary["venue"] or "-")

    st.markdown(
        f"<div class='watch-note'>{html.escape(watch_note(summary, matchup))}</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.05, 1])
    with left:
        st.markdown("#### Probable Starters")
        starters = pd.DataFrame(
            [
                {"club": summary["away_name"], "probable": summary["away_probable"], "record_pct": summary["away_record"]},
                {"club": summary["home_name"], "probable": summary["home_probable"], "record_pct": summary["home_record"]},
            ]
        )
        st.dataframe(starters, width="stretch", hide_index=True)

    with right:
        st.markdown("#### Current Matchup")
        if matchup:
            st.metric("Batter", matchup["batter"])
            st.metric("Pitcher", matchup["pitcher"])
            st.caption(f"Count {matchup['balls']}-{matchup['strikes']} | Outs {matchup['outs']}")
        else:
            st.write("Matchup appears once the live feed has a current play.")

    if feed:
        st.markdown(render_scorebug_html(live_scorebug_state(feed)), unsafe_allow_html=True)

    st.markdown("#### Last Plays")
    if feed:
        plays = recent_plays(feed)
        if plays.empty:
            st.write("No play log yet.")
        else:
            st.dataframe(plays, width="stretch", hide_index=True)
    else:
        st.write("Play log appears after first pitch.")

    if matchup and matchup.get("pitcher_id"):
        st.markdown("#### Current Matchup Shape")
        try:
            arsenal = get_pitcher_arsenal(int(matchup["pitcher_id"]))
            if arsenal.empty:
                st.caption("No pitch arsenal data yet.")
            else:
                pitcher_col, batter_col = st.columns(2)
                display = format_savant_table(arsenal)[
                    [
                        "pitch_name",
                        "pitches",
                        "pitch_percent",
                        "velocity",
                        "spin_rate",
                        "whiff_percent",
                        "xwoba",
                        "hardhit_percent",
                        "api_break_z_induced",
                        "api_break_x_arm",
                    ]
                ]
                display = display.rename(
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
                with pitcher_col:
                    st.markdown(f"##### {matchup['pitcher']} Arsenal")
                    st.dataframe(display, width="stretch", hide_index=True)
                    fig = pitch_mix_chart(arsenal, "Pitch Mix")
                    fig.update_layout(height=320, margin=dict(l=10, r=10, t=45, b=10))
                    st.plotly_chart(fig, use_container_width=True)
                top = arsenal.iloc[0]
                best = arsenal.sort_values("xwoba", ascending=True, na_position="last").iloc[0]
                with batter_col:
                    if matchup.get("batter_id"):
                        batter_profile = get_batter_pitch_profile(int(matchup["batter_id"]))
                        st.markdown(f"##### {matchup['batter']} vs Pitch Types")
                        if batter_profile.empty:
                            st.caption("No batter pitch-type data yet.")
                        else:
                            batter_display = format_savant_table(batter_profile)[
                                ["pitch_name", "pitches", "pitch_percent", "woba", "xwoba", "whiff_percent", "launch_speed"]
                            ].rename(
                                columns={
                                    "pitch_name": "pitch",
                                    "pitch_percent": "seen",
                                    "whiff_percent": "whiff",
                                    "launch_speed": "EV",
                                }
                            )
                            st.dataframe(batter_display, width="stretch", hide_index=True)
                            same_pitch = batter_profile[batter_profile["pitch_type"] == top["pitch_type"]]
                            if not same_pitch.empty:
                                row = same_pitch.iloc[0]
                                xwoba_str = f"{row['xwoba']:.3f}" if not pd.isna(row.get("xwoba")) else "—"
                                whiff_str = f"{row['whiff_percent']:.1f}%" if not pd.isna(row.get("whiff_percent")) else "—%"
                                st.caption(f"Against {top['pitch_name']}: {xwoba_str} xwOBA, {whiff_str} whiff.")
                    else:
                        st.caption("Batter profile appears when the live feed exposes a batter id.")
                top_usage = f"{top['pitch_percent']:.1f}%" if not pd.isna(top.get("pitch_percent")) else "—%"
                best_xwoba = f"{best['xwoba']:.3f}" if not pd.isna(best.get("xwoba")) else "—"
                st.markdown(
                    "<div class='watch-note'>"
                    f"{html.escape(str(matchup['pitcher']))} leans most on the {html.escape(str(top['pitch_name']))} "
                    f"({top_usage} usage). Best expected-result pitch so far: "
                    f"{html.escape(str(best['pitch_name']))} at {best_xwoba} xwOBA. "
                    f"Now watch whether {html.escape(str(matchup['batter']))} makes him move to the second plan."
                    "</div>",
                    unsafe_allow_html=True,
                )
        except Exception as exc:
            st.caption(f"Matchup shape unavailable: {exc}")

from __future__ import annotations

import streamlit as st

from playball.data.mlb import get_leaders
from playball.data.savant import format_savant_table, get_savant_batters, get_savant_pitchers


HITTING_CATEGORIES = ["homeRuns", "onBasePlusSlugging", "runsBattedIn", "battingAverage"]
PITCHING_CATEGORIES = ["earnedRunAverage", "strikeouts", "wins"]


def _render_block(title: str, blocks) -> None:
    st.markdown(f"#### {title}")
    if not blocks:
        st.info("No leader data returned.")
        return
    tabs = st.tabs(list(blocks.keys()))
    for tab, (category, frame) in zip(tabs, blocks.items()):
        with tab:
            st.dataframe(frame, width="stretch", hide_index=True)


def render_leaders() -> None:
    st.subheader("Stars Right Now")
    st.markdown(
        "Early-season leaderboards are noisy, but they are perfect for discovery. Treat these as names to investigate, not final verdicts."
    )

    left, right = st.columns(2)
    with left:
        _render_block("Hitters", get_leaders("hitting", HITTING_CATEGORIES, limit=12))
    with right:
        _render_block("Pitchers", get_leaders("pitching", PITCHING_CATEGORIES, limit=12))

    st.markdown("#### Expected-Stat Leaders")
    batters = get_savant_batters(25).sort_values("xwoba", ascending=False).head(15)
    pitchers = get_savant_pitchers(25).sort_values("xwoba", ascending=True).head(15)
    savant_left, savant_right = st.columns(2)
    with savant_left:
        st.markdown("##### Hitters by xwOBA")
        st.dataframe(
            format_savant_table(batters)[["name", "pa", "xwoba", "woba", "xba", "xslg", "launch_speed", "barrels_per_bbe_percent"]],
            width="stretch",
            hide_index=True,
        )
    with savant_right:
        st.markdown("##### Pitchers by xwOBA Allowed")
        st.dataframe(
            format_savant_table(pitchers)[["name", "pa", "xwoba", "woba", "xba", "xslg", "launch_speed", "hardhit_percent"]],
            width="stretch",
            hide_index=True,
        )

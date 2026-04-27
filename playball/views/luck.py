from __future__ import annotations

import streamlit as st

from playball.data.savant import format_savant_table, get_savant_batters, get_savant_pitchers


def render_luck_index() -> None:
    st.subheader("Luck Index")
    st.markdown(
        "Actual `wOBA` minus expected `xwOBA`. For hitters, negative means the contact quality is better than the results. "
        "For pitchers, positive means the contact allowed is better than the runs/results have looked."
    )

    min_pa = st.slider("Minimum plate appearances / batters faced", 10, 100, 25, step=5)
    hitters = get_savant_batters(min_pa)
    pitchers = get_savant_pitchers(min_pa)

    hit_left, hit_right = st.columns(2)
    with hit_left:
        st.markdown("#### Hitters Due Better")
        due = hitters.sort_values("luck_gap", ascending=True).head(15)
        st.dataframe(
            format_savant_table(due)[["name", "pa", "woba", "xwoba", "luck_gap", "xba", "xslg", "launch_speed", "hardhit_percent"]],
            width="stretch",
            hide_index=True,
        )
    with hit_right:
        st.markdown("#### Hitters Outrunning Contact")
        hot = hitters.sort_values("luck_gap", ascending=False).head(15)
        st.dataframe(
            format_savant_table(hot)[["name", "pa", "woba", "xwoba", "luck_gap", "xba", "xslg", "launch_speed", "hardhit_percent"]],
            width="stretch",
            hide_index=True,
        )

    pit_left, pit_right = st.columns(2)
    with pit_left:
        st.markdown("#### Pitchers Getting Burned")
        burned = pitchers.sort_values("luck_gap", ascending=False).head(15)
        st.dataframe(
            format_savant_table(burned)[["name", "pa", "woba", "xwoba", "luck_gap", "xba", "xslg", "launch_speed", "hardhit_percent"]],
            width="stretch",
            hide_index=True,
        )
    with pit_right:
        st.markdown("#### Pitchers Skating By")
        skating = pitchers.sort_values("luck_gap", ascending=True).head(15)
        st.dataframe(
            format_savant_table(skating)[["name", "pa", "woba", "xwoba", "luck_gap", "xba", "xslg", "launch_speed", "hardhit_percent"]],
            width="stretch",
            hide_index=True,
        )

from __future__ import annotations

import pandas as pd
import streamlit as st


# Last hand-curated update. Bump this whenever the PROSPECTS list below is reviewed.
PROSPECTS_LAST_UPDATED = "2026-04-26"


PROSPECTS = [
    {
        "rank": 1,
        "name": "Konnor Griffin",
        "org": "Pirates",
        "pos": "SS/OF",
        "why": "Best-tools prospect in the minors entering 2026.",
    },
    {
        "rank": 2,
        "name": "Kevin McGonigle",
        "org": "Tigers",
        "pos": "SS",
        "why": "Elite pure-hitting reputation; AL Central problem to know.",
    },
    {
        "rank": 3,
        "name": "Jesus Made",
        "org": "Brewers",
        "pos": "SS/2B",
        "why": "Teenage performer with loud offensive trajectory.",
    },
    {
        "rank": 4,
        "name": "Leo De Vries",
        "org": "Athletics",
        "pos": "SS",
        "why": "High-end tools, already prominent after a major trade.",
    },
    {
        "rank": 5,
        "name": "JJ Wetherholt",
        "org": "Cardinals",
        "pos": "INF",
        "why": "Advanced bat, near the front of the shortstop/infielder wave.",
    },
    {
        "rank": 18,
        "name": "Carter Jensen",
        "org": "Royals",
        "pos": "C",
        "why": "Royals catcher who jumped sharply on 2026 industry lists.",
    },
]


def render_prospects(roster: pd.DataFrame) -> None:
    st.subheader("Prospect Radar")
    st.markdown(
        "**Editorial — author's hand-curated notes.** "
        f"Last reviewed **{PROSPECTS_LAST_UPDATED}**. "
        "This is not data-backed prospect tracking — there is no clean public MiLB Statcast at every level "
        "and most scouting grades are paywalled. Treat this list as one fan's mental map of names to know, "
        "not as analysis. Bump `PROSPECTS_LAST_UPDATED` in code when you refresh the list."
    )
    frame = pd.DataFrame(PROSPECTS)
    st.dataframe(frame, width="stretch", hide_index=True)

    st.markdown("#### Royals Young-Player Watch")
    royals_names = set(roster["name"].dropna()) if not roster.empty else set()
    focus = []
    for name in ["Carter Jensen", "Jac Caglianone", "Bobby Witt Jr.", "Maikel Garcia", "Cole Ragans"]:
        focus.append(
            {
                "name": name,
                "on_active_roster": "yes" if name in royals_names else "not today",
                "watch": {
                    "Carter Jensen": "Can the bat be above average at catcher?",
                    "Jac Caglianone": "Does the power come with playable swing decisions?",
                    "Bobby Witt Jr.": "Is he merely great or in MVP shape?",
                    "Maikel Garcia": "Does the on-base/defense package add up to more than traditional stats show?",
                    "Cole Ragans": "Is the command sharp enough for ace-level dominance?",
                }[name],
            }
        )
    st.dataframe(pd.DataFrame(focus), width="stretch", hide_index=True)

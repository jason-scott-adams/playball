from datetime import date

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from playball.data.mlb import TEAM_ID_ROYALS, get_active_roster, get_royals_game
from playball.views.arsenal import render_arsenal_lab
from playball.views.game_companion import render_game_companion
from playball.views.league_context import render_league_context
from playball.views.leaders import render_leaders
from playball.views.luck import render_luck_index
from playball.views.my_guys import render_my_guys
from playball.views.player_detail import render_player_detail
from playball.views.prospects import render_prospects
from playball.views.royals import render_royals
from playball.views.today import render_today


st.set_page_config(
    page_title="Playball",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --pb-bg: #f4f7fb;
        --pb-panel: #ffffff;
        --pb-panel-soft: #f8fafc;
        --pb-ink: #172033;
        --pb-muted: #5b6678;
        --pb-line: #d8e0ea;
        --pb-blue: #004687;
        --pb-blue-2: #7ab2dd;
        --pb-blue-soft: #e6f1fb;
        --pb-gold: #bd9b60;
        --pb-gold-soft: #fff6df;
        --pb-green: #237a57;
        --pb-red: #b42318;
    }

    html, body, [class*="css"] {
        font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    .stApp {
        background:
            linear-gradient(180deg, rgba(0, 70, 135, 0.08), rgba(244, 247, 251, 0) 220px),
            var(--pb-bg);
        color: var(--pb-ink);
    }

    .block-container {
        padding-top: 1.35rem;
        padding-bottom: 2rem;
        max-width: 1440px;
    }

    h1, h2, h3, h4, h5, h6,
    div[data-testid="stMarkdownContainer"] h1,
    div[data-testid="stMarkdownContainer"] h2,
    div[data-testid="stMarkdownContainer"] h3,
    div[data-testid="stMarkdownContainer"] h4,
    div[data-testid="stMarkdownContainer"] h5,
    div[data-testid="stMarkdownContainer"] h6 {
        color: var(--pb-ink) !important;
        letter-spacing: 0;
    }

    div[data-testid="stMarkdownContainer"],
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] li,
    label,
    .stCaptionContainer {
        color: var(--pb-ink) !important;
    }

    div[data-testid="stSidebar"] {
        background: #eaf2fb;
        border-right: 1px solid var(--pb-line);
    }

    div[data-testid="stMetric"] {
        border: 1px solid var(--pb-line);
        border-radius: 8px;
        padding: 0.72rem 0.85rem;
        background: var(--pb-panel);
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.05);
    }
    div[data-testid="stMetric"],
    div[data-testid="stMetric"] * {
        color: var(--pb-ink) !important;
    }
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] * {
        color: var(--pb-muted) !important;
        font-weight: 650 !important;
    }

    div[data-testid="stMetricValue"] {
        font-weight: 760 !important;
    }

    div[data-testid="stTabs"] button {
        color: var(--pb-muted) !important;
        font-weight: 650;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--pb-blue) !important;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--pb-line);
        border-radius: 8px;
        overflow: hidden;
        background: var(--pb-panel);
    }

    .playball-kicker {
        color: var(--pb-blue);
        font-size: 0.86rem;
        text-transform: uppercase;
        letter-spacing: .08em;
        font-weight: 800;
        margin-bottom: -0.35rem;
    }

    .watch-note {
        border: 1px solid #bfd5ec;
        border-left: 5px solid var(--pb-blue);
        padding: .78rem .95rem;
        background: linear-gradient(90deg, var(--pb-blue-soft), #ffffff 72%);
        border-radius: 0 8px 8px 0;
        margin: .25rem 0 1rem;
        color: var(--pb-ink) !important;
        font-weight: 560;
        line-height: 1.45;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
    }

    .watch-note,
    .watch-note *,
    div[data-testid="stMarkdownContainer"] .watch-note,
    div[data-testid="stMarkdownContainer"] .watch-note * {
        color: var(--pb-ink) !important;
    }

    button[kind="secondary"],
    button[kind="primary"] {
        border-radius: 8px !important;
        font-weight: 700 !important;
    }

    a {
        color: var(--pb-blue) !important;
    }

    .pb-hero {
        border: 1px solid #c6d7ea;
        border-radius: 8px;
        background: linear-gradient(135deg, #003b73 0%, #004687 54%, #0d5ea8 100%);
        color: #ffffff !important;
        padding: 1rem 1.1rem;
        box-shadow: 0 8px 24px rgba(0, 70, 135, 0.16);
        margin-bottom: 1rem;
    }
    .pb-hero, .pb-hero * { color: #ffffff !important; }
    .pb-hero .muted { color: #d8e8f8 !important; }
    .pb-hero .gold { color: #f3d58a !important; }

    .scorebug {
        border: 1px solid #c6d7ea;
        background: #ffffff;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(16, 24, 40, 0.06);
    }
    .scorebug, .scorebug * { color: var(--pb-ink) !important; }
    .scorebug-title {
        color: var(--pb-blue) !important;
        font-size: .82rem;
        font-weight: 850;
        letter-spacing: .08em;
        text-transform: uppercase;
        margin-bottom: .75rem;
    }
    .scorebug-grid {
        display: grid;
        grid-template-columns: 1fr 170px;
        gap: 1rem;
        align-items: center;
    }
    .diamond {
        position: relative;
        width: 136px;
        height: 136px;
        margin: 0 auto;
    }
    .base {
        position: absolute;
        width: 31px;
        height: 31px;
        transform: rotate(45deg);
        border: 2px solid var(--pb-blue);
        background: #f5f9fd;
        box-shadow: inset 0 0 0 2px #ffffff;
    }
    .base.occupied {
        background: var(--pb-gold);
        border-color: #8a6b2d;
    }
    .base.first { right: 18px; top: 53px; }
    .base.second { left: 52px; top: 0; }
    .base.third { left: 18px; top: 53px; }
    .base.home { left: 52px; bottom: 0; background: var(--pb-blue); border-color: var(--pb-blue); }
    .count-row {
        display: grid;
        grid-template-columns: 64px 1fr;
        gap: .55rem;
        align-items: center;
        margin: .35rem 0;
        font-weight: 700;
    }
    .lights { display: flex; gap: .35rem; }
    .light {
        width: 14px;
        height: 14px;
        border-radius: 999px;
        border: 1px solid #9aa9bc;
        background: #e9eef5;
    }
    .light.on.balls { background: var(--pb-green); border-color: #1b6849; }
    .light.on.strikes { background: var(--pb-gold); border-color: #8a6b2d; }
    .light.on.outs { background: var(--pb-red); border-color: #8a1e15; }
    .lineup-small {
        font-size: .9rem;
        line-height: 1.45;
        margin-top: .75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def main() -> None:
    today = date.today()

    st.markdown("<div class='playball-kicker'>Royals modern baseball cockpit</div>", unsafe_allow_html=True)
    st.title("Playball")

    with st.sidebar:
        st.header("Controls")
        selected_date = st.date_input("Game date", value=today)
        auto_refresh = st.toggle("Auto-refresh", value=False, help="Rerun the app on a timer. Useful during live games.")
        refresh_interval = st.selectbox(
            "Refresh interval",
            [15, 30, 45, 60, 120],
            index=2,
            format_func=lambda seconds: f"{seconds} seconds",
            disabled=not auto_refresh,
        )
        if auto_refresh:
            st_autorefresh(interval=int(refresh_interval) * 1000, key="playball_auto_refresh")
            st.caption(f"Auto-refreshing every {refresh_interval} seconds.")
        refresh = st.button("Refresh data", width="stretch")
        if refresh:
            st.cache_data.clear()
            st.rerun()

        st.caption("Built local-first. MLB data is public API based; advanced stats can be extended as sources mature.")

    game = get_royals_game(selected_date)
    roster = get_active_roster(TEAM_ID_ROYALS)

    tabs = st.tabs(["Today", "Game Companion", "My Guys", "Royals Pulse", "Player Detail", "League Context", "Research Lab"])
    with tabs[0]:
        render_today(game, roster)
    with tabs[1]:
        render_game_companion(game)
    with tabs[2]:
        render_my_guys()
    with tabs[3]:
        render_royals(roster)
    with tabs[4]:
        render_player_detail(roster)
    with tabs[5]:
        render_league_context()
    with tabs[6]:
        sub_tabs = st.tabs(["Arsenal", "Stars", "Luck", "Prospects"])
        with sub_tabs[0]:
            render_arsenal_lab(roster)
        with sub_tabs[1]:
            render_leaders()
        with sub_tabs[2]:
            render_luck_index()
        with sub_tabs[3]:
            render_prospects(roster)


if __name__ == "__main__":
    main()

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
        --pb-bg: #0b1220;
        --pb-panel: #11192a;
        --pb-panel-soft: #0f1626;
        --pb-ink: #e5ecf7;
        --pb-muted: #8a9bb6;
        --pb-line: #1f2a44;
        --pb-blue: #004687;
        --pb-blue-2: #7ab2dd;
        --pb-blue-soft: rgba(122, 178, 221, 0.12);
        --pb-gold: #c9a14a;
        --pb-gold-soft: rgba(201, 161, 74, 0.18);
        --pb-green: #2eb27c;
        --pb-red: #e35858;
    }

    html, body, [class*="css"] {
        font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    .stApp {
        background:
            radial-gradient(ellipse at top, rgba(0, 70, 135, 0.30) 0%, rgba(11, 18, 32, 0) 50%),
            linear-gradient(180deg, #0b1220 0%, #0a0f1c 100%);
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
        background: #0a1426;
        border-right: 1px solid var(--pb-line);
    }
    div[data-testid="stSidebar"] * {
        color: var(--pb-ink) !important;
    }

    div[data-testid="stMetric"] {
        border: 1px solid var(--pb-line);
        border-radius: 10px;
        padding: 0.72rem 0.85rem;
        background: var(--pb-panel);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.02) inset, 0 8px 20px rgba(0, 0, 0, 0.35);
    }
    div[data-testid="stMetric"],
    div[data-testid="stMetric"] * {
        color: var(--pb-ink) !important;
    }
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] * {
        color: var(--pb-muted) !important;
        font-weight: 650 !important;
        letter-spacing: 0.02em;
    }

    div[data-testid="stMetricValue"] {
        font-weight: 760 !important;
        color: #ffffff !important;
    }

    div[data-testid="stTabs"] button {
        color: var(--pb-muted) !important;
        font-weight: 650;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--pb-gold) !important;
        border-bottom-color: var(--pb-gold) !important;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--pb-line);
        border-radius: 10px;
        overflow: hidden;
        background: var(--pb-panel);
    }
    /* Streamlit dataframe header/body coloring */
    div[data-testid="stDataFrame"] [role="columnheader"] {
        background: #0c1424 !important;
        color: var(--pb-muted) !important;
        border-color: var(--pb-line) !important;
    }
    div[data-testid="stDataFrame"] [role="gridcell"] {
        color: var(--pb-ink) !important;
        border-color: var(--pb-line) !important;
    }

    .playball-kicker {
        color: var(--pb-gold);
        font-size: 0.86rem;
        text-transform: uppercase;
        letter-spacing: .08em;
        font-weight: 800;
        margin-bottom: -0.35rem;
    }

    .watch-note {
        border: 1px solid var(--pb-line);
        border-left: 5px solid var(--pb-gold);
        padding: .78rem .95rem;
        background: linear-gradient(90deg, var(--pb-gold-soft), rgba(17, 25, 42, 0.6) 78%);
        border-radius: 0 10px 10px 0;
        margin: .25rem 0 1rem;
        color: var(--pb-ink) !important;
        font-weight: 560;
        line-height: 1.45;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.30);
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
        color: var(--pb-blue-2) !important;
    }

    .pb-hero {
        border: 1px solid #1c2a4a;
        border-radius: 12px;
        background:
            radial-gradient(ellipse at right, rgba(201, 161, 74, 0.18) 0%, rgba(0, 70, 135, 0) 60%),
            linear-gradient(135deg, #002554 0%, #003b73 50%, #0a4f93 100%);
        color: #ffffff !important;
        padding: 1.1rem 1.2rem;
        box-shadow: 0 14px 30px rgba(0, 0, 0, 0.45);
        margin-bottom: 1rem;
    }
    .pb-hero, .pb-hero * { color: #ffffff !important; }
    .pb-hero .muted { color: #b6cfe8 !important; }
    .pb-hero .gold { color: var(--pb-gold) !important; }

    .scorebug {
        border: 1px solid var(--pb-line);
        background: linear-gradient(180deg, #0f1828 0%, #0b1220 100%);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.45);
    }
    .scorebug, .scorebug * { color: var(--pb-ink) !important; }
    .scorebug-title {
        color: var(--pb-gold) !important;
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
        border: 2px solid var(--pb-blue-2);
        background: #0f1828;
        box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.04);
    }
    .base.occupied {
        background: var(--pb-gold);
        border-color: #8a6b2d;
        box-shadow: inset 0 0 0 2px rgba(0, 0, 0, 0.25), 0 0 12px rgba(201, 161, 74, 0.5);
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
        border: 1px solid #2a3a5c;
        background: #0c1424;
    }
    .light.on.balls { background: var(--pb-green); border-color: #19774f; box-shadow: 0 0 10px rgba(46, 178, 124, 0.5); }
    .light.on.strikes { background: var(--pb-gold); border-color: #8a6b2d; box-shadow: 0 0 10px rgba(201, 161, 74, 0.5); }
    .light.on.outs { background: var(--pb-red); border-color: #8a2424; box-shadow: 0 0 10px rgba(227, 88, 88, 0.45); }
    .lineup-small {
        font-size: .9rem;
        line-height: 1.45;
        margin-top: .75rem;
    }

    /* Streamlit input controls: dark-mode polish */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    .stTextArea textarea {
        background: var(--pb-panel) !important;
        color: var(--pb-ink) !important;
        border-color: var(--pb-line) !important;
    }
    .stTextArea textarea::placeholder,
    div[data-baseweb="input"] input::placeholder {
        color: var(--pb-muted) !important;
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

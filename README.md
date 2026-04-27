# Playball

A Royals-first baseball second-screen app for watching the season with modern context.

Built for the fan who knows the box score but wants the newer layer: expected stats, pitch mix, contact quality, watchlists, prospects, and live game context — without turning baseball into homework.

## What It Does

- **Today** — front-door briefing: game state, standings pressure, upcoming Royals games, My Guys snapshots, and a rotating modern-stat lesson.
- **Game Companion** — live score/state, probable starters, recent plays, current matchup intelligence (pitcher arsenal × batter pitch-type splits), and a base/out/count scorebug.
- **My Guys** — local personal watchlist seeded with Royals core players, league stars, and prospects. Editable, searchable, persisted to CSV.
- **Royals Pulse** — active roster, Royals-specific expected-stat context, plus a **Modern Stats box** (FIP, K-BB%, OBP, ISO) computed locally from the MLB Stats API.
- **Player Detail** — one player at a time: expected stats, contact quality, pitch-type profile, season totals (FIP/K-BB% for pitchers, OBP/ISO for hitters), and a plain-English watch note.
- **League Context** — MLB standings by division and an adjustable Royals schedule window.
- **Research Lab** — Arsenal Lab, league leaders, Luck Index, and a hand-curated Prospect Radar.

## Screens And Data

Playball uses public baseball data sources:

- **MLB Stats API** — schedule, roster, standings, live game feed, box score, public leaders, per-player season totals.
- **Baseball Savant / Statcast (CSV endpoint)** — expected stats, contact quality, pitch tracking, pitch mix, pitch-type profiles.
- **Local computation** — FIP, K-BB%, OBP, ISO, BB%, K% derived from the MLB Stats API box-score fields. Logic in `playball/lib/stats.py`, tested in `tests/test_stats.py`.

The watchlist lives at `data/watchlist.csv` — starter players plus your notes; meant to be edited.

## Modern Stat Short List

| Stat | Plain-English Use | Status |
| --- | --- | --- |
| OBP | How often a hitter avoids making an out. | ✅ MLB Stats API |
| wOBA | OBP that weights extra-base hits properly. | ✅ Baseball Savant |
| xwOBA | What wOBA *should* be from contact quality. | ✅ Baseball Savant |
| Luck Gap | Actual `wOBA − xwOBA`. Big gaps invite a closer look. | ✅ Computed |
| Barrel% | How often contact has the ideal exit-velo / launch combo. | ✅ Baseball Savant |
| Hard-Hit% | Share of batted balls 95+ mph. | ✅ Baseball Savant |
| ISO | SLG − AVG. Pure power. | ✅ Computed |
| FIP | ERA stripped of defense and luck (HR/BB/HBP/K only). | ✅ Computed |
| K-BB% | Pitcher dominance minus self-inflicted damage. | ✅ Computed |
| K% / BB% | Strikeout rate, walk rate. | ✅ Computed |
| **wRC+** | Park- and league-adjusted total offense, 100 = average. | 🚧 Roadmap (FanGraphs only; Cloudflare-blocked) |
| **WAR** | Broad estimate of total value over a replacement-level player. | 🚧 Roadmap (needs defensive metrics) |
| **Stuff+** | Raw nastiness of the pitches. | 🚧 Roadmap (proprietary FanGraphs model) |

**Why the Roadmap stats aren't wired:** they require FanGraphs data. As of April 2026 FanGraphs is Cloudflare-protected — `pybaseball` returns 403, and direct HTTP fetches with browser User-Agent return Cloudflare's interstitial. Until there's a stable free path (or we add a Bright Data proxy / headless-browser fetcher), wRC+, WAR, and Stuff+ stay marked Roadmap rather than silently dropped or pretended into existence.

## Run Locally

```bash
git clone https://github.com/jason-scott-adams/playball.git
cd playball                 # the cloned repo root
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open <http://127.0.0.1:8501>.

## Refreshing Data

Sidebar:

- **Refresh data** clears Streamlit's cache immediately.
- **Auto-refresh** reruns the app on a tunable interval (15s–120s), useful during live games.

Cached source TTLs:

- live game feed — ~45 seconds
- Royals game lookup — ~60 seconds
- standings, schedule — ~10 minutes
- Savant expected stats and pitch profiles — ~15 minutes
- per-player advanced stats (FIP, K-BB%, ISO, etc.) — ~15 minutes
- active roster — ~1 hour

## Pre-Game Health Check

Before pulling out the laptop for an actual game, run the live smoke test:

```bash
python -m scripts.smoke_test
```

It hits MLB Stats API, Baseball Savant, the per-player advanced fetcher, the watchlist, and the local stats formulas. **Exits non-zero on any failure** so you know before first pitch whether anything has drifted.

## Tests

```bash
pytest
```

Currently covers the stats module — FIP / K-BB% / ISO formulas with real-player fixtures.

## Prospects

The `Research Lab → Prospects` view is **editorial — author-curated notes**, not data-backed prospect tracking. There is no clean public MiLB Statcast at every level and most scouting grades are paywalled. Update the date stamp in `playball/views/prospects.py` (`PROSPECTS_LAST_UPDATED`) when you refresh the list.

## Roadmap

- Rolling 7/15/30-day trend lines for My Guys.
- Click-through from My Guys into Player Detail.
- Better batter matchup panels: platoon side, hot zones, chase and whiff tendencies.
- FanGraphs-backed wRC+, WAR, Stuff+ once a stable free path opens.
- Game leverage / win-probability deltas where available.

## Project Notes

Playball is an unofficial fan project. It is not affiliated with, endorsed by, or sponsored by Major League Baseball, MLB Advanced Media, Baseball Savant, FanGraphs, the Kansas City Royals, or any listed data provider. Respect each data provider's terms of use.

## License

MIT. See [LICENSE](LICENSE).

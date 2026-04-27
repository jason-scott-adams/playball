# Playball

A Royals-first baseball second-screen app for watching the season with modern context.

Playball is built for the fan who knows the box score but wants the newer layer: expected stats, pitch mix, contact quality, watchlists, prospects, and live game context without turning baseball into homework.

## What It Does

- **Today**: a front-door briefing with game state, standings pressure, upcoming Royals games, My Guys snapshots, and a short modern-stat lesson.
- **Game Companion**: live score/state, probable starters, recent plays, current matchup intelligence, and a base/out/count scorebug.
- **My Guys**: a local personal watchlist seeded with Royals core players, league stars, and prospects.
- **Royals Pulse**: active roster plus Royals-specific expected-stat context.
- **Player Detail**: one-player expected stats, hitter pitch-type profiles, pitcher arsenals, and a plain-English watch note.
- **League Context**: MLB standings by division and an adjustable Royals schedule window.
- **Research Lab**: deeper views for arsenals, league leaders, luck index, and prospects.

## Screens And Data

Playball uses public baseball data sources:

- MLB Stats API for schedule, roster, standings, live game feed, box score, and public leaders.
- Baseball Savant / Statcast for expected stats, contact quality, pitch tracking, pitch mix, and pitch-type profiles.
- Curated prospect context from public industry lists.

The app keeps a small local watchlist at `data/watchlist.csv`. It contains starter players and your notes; it is meant to be edited.

## Run Locally

```bash
cd playball
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open:

```text
http://127.0.0.1:8501
```

## Refreshing Data

The sidebar has two refresh controls:

- **Refresh data** clears Streamlit's cache immediately.
- **Auto-refresh** reruns the app on a selected interval, useful during live games.

Cached source TTLs are intentionally short for live views and longer for slower-changing data:

- live game feed: about 45 seconds
- Royals game lookup: about 60 seconds
- standings and schedule: about 10 minutes
- Savant expected stats and pitch profiles: about 15 minutes
- active roster: about 1 hour

## Modern Stat Short List

| Stat | Plain-English Use |
| --- | --- |
| OBP | How often a hitter avoids making an out. |
| wRC+ | Total offensive value adjusted for league and park; 100 is average. |
| xwOBA | Expected offensive value based on contact quality and related inputs. |
| Luck Gap | Actual `wOBA - xwOBA`; big gaps are invitations to investigate. |
| Barrel% | How often contact has the ideal exit velocity and launch angle mix. |
| K-BB% | Pitcher dominance minus self-inflicted damage. |
| FIP | Pitcher run prevention using strikeouts, walks, hit batters, and homers. |
| WAR | Broad estimate of total value over a replacement-level player. |

## Roadmap

- Rolling 7/15/30-day trend lines for My Guys.
- Click-through from My Guys into Player Detail.
- Better batter matchup panels: platoon side, hot zones, chase and whiff tendencies.
- FanGraphs seasonal tables for `wRC+`, `WAR`, `FIP`, `K-BB%`, and plate discipline.
- Game leverage and win-probability deltas where available.

## Project Notes

Playball is an unofficial fan project. It is not affiliated with, endorsed by, or sponsored by Major League Baseball, MLB Advanced Media, Baseball Savant, FanGraphs, the Kansas City Royals, or any listed data provider. Respect each data provider's terms of use.

## License

MIT. See [LICENSE](LICENSE).

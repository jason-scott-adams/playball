from __future__ import annotations

import html


def _lights(kind: str, current: int, total: int) -> str:
    current = max(0, min(int(current or 0), total))
    return "".join(f"<span class='light {'on ' + kind if i < current else ''}'></span>" for i in range(total))


def _e(value) -> str:
    """Escape a string field that may come from the MLB live feed before injection into HTML."""
    return html.escape(str(value)) if value not in (None, "") else "-"


def render_scorebug_html(state: dict) -> str:
    first = "occupied" if state.get("first") else ""
    second = "occupied" if state.get("second") else ""
    third = "occupied" if state.get("third") else ""
    runners = []
    for label in ["first", "second", "third"]:
        if state.get(label):
            runners.append(f"{html.escape(label.title())}: {html.escape(str(state[label]))}")
    runner_text = "<br>".join(runners) if runners else "Bases empty"
    half = html.escape(str(state.get("half") or ""))
    inning = html.escape(str(state.get("inning") or ""))
    return f"""
    <div class="scorebug">
      <div class="scorebug-title">Live Scoreboard</div>
      <div class="scorebug-grid">
        <div>
          <div class="count-row"><span>Balls</span><div class="lights">{_lights('balls', state.get('balls', 0), 4)}</div></div>
          <div class="count-row"><span>Strikes</span><div class="lights">{_lights('strikes', state.get('strikes', 0), 3)}</div></div>
          <div class="count-row"><span>Outs</span><div class="lights">{_lights('outs', state.get('outs', 0), 3)}</div></div>
          <div class="lineup-small">
            <strong>{half} {inning}</strong><br>
            Batter: {_e(state.get('batter'))}<br>
            Pitcher: {_e(state.get('pitcher'))}<br>
            On deck: {_e(state.get('on_deck'))}<br>
            {runner_text}
          </div>
        </div>
        <div class="diamond" aria-label="Base runner diamond">
          <div class="base second {second}"></div>
          <div class="base third {third}"></div>
          <div class="base first {first}"></div>
          <div class="base home"></div>
        </div>
      </div>
    </div>
    """

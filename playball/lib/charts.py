from __future__ import annotations

import pandas as pd
import plotly.express as px


def pitch_mix_chart(frame: pd.DataFrame, title: str):
    chart = frame.sort_values("pitch_percent", ascending=True)
    fig = px.bar(
        chart,
        x="pitch_percent",
        y="pitch_name",
        orientation="h",
        color="xwoba",
        color_continuous_scale="RdYlBu_r",
        labels={"pitch_percent": "Usage %", "pitch_name": "Pitch", "xwoba": "xwOBA"},
        title=title,
    )
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10), coloraxis_colorbar=dict(title="xwOBA"))
    return fig

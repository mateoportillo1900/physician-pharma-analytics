"""
Shared Plotly chart helpers. Keeps the visual style consistent across pages.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# Reusable color palette — colorblind-safe, professional
PALETTE = [
    "#0066CC",
    "#FF6B35",
    "#16A085",
    "#9B59B6",
    "#F39C12",
    "#E74C3C",
    "#1ABC9C",
    "#34495E",
    "#D35400",
    "#27AE60",
]


def style_figure(fig: go.Figure, height: int = 420) -> go.Figure:
    """Apply consistent styling to any Plotly figure."""
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(family="Inter, system-ui, sans-serif", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(font_size=12),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    fig.update_xaxes(gridcolor="rgba(0,0,0,0.08)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.08)", zeroline=False)
    return fig


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    orientation: str = "v",
    color: str | None = None,
) -> go.Figure:
    """Standard bar chart with the project's styling."""
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        orientation=orientation,
        color=color,
        color_discrete_sequence=PALETTE,
    )
    return style_figure(fig)


def scatter_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    hover_data: list[str] | None = None,
    size: str | None = None,
    log_x: bool = False,
    log_y: bool = False,
) -> go.Figure:
    """Standard scatter chart."""
    fig = px.scatter(
        df,
        x=x,
        y=y,
        title=title,
        color=color,
        size=size,
        hover_data=hover_data,
        color_discrete_sequence=PALETTE,
        log_x=log_x,
        log_y=log_y,
        opacity=0.6,
    )
    return style_figure(fig)


def choropleth_us(
    df: pd.DataFrame,
    state_col: str,
    value_col: str,
    title: str,
    color_scale: str = "Blues",
) -> go.Figure:
    """US state-level choropleth."""
    fig = px.choropleth(
        df,
        locations=state_col,
        locationmode="USA-states",
        color=value_col,
        scope="usa",
        title=title,
        color_continuous_scale=color_scale,
    )
    return style_figure(fig, height=500)


def donut_chart(
    df: pd.DataFrame,
    names: str,
    values: str,
    title: str,
    label_threshold_pct: float = 5.0,
) -> go.Figure:
    """Donut chart for proportional breakdowns.

    Only labels slices >= label_threshold_pct of total to avoid label
    overlap. Smaller slices show on hover and in the legend.
    """
    total = df[values].sum()
    pct = df[values] / total * 100

    # Build per-slice text: only show label for big slices
    text = [
        f"{name}<br>{p:.1f}%" if p >= label_threshold_pct else ""
        for name, p in zip(df[names], pct, strict=False)
    ]

    fig = px.pie(
        df,
        names=names,
        values=values,
        title=title,
        hole=0.55,
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(
        text=text,
        textposition="outside",
        textinfo="text",
        hovertemplate="<b>%{label}</b><br>$%{value:.1f}<br>%{percent}<extra></extra>",
    )
    fig.update_layout(uniformtext_minsize=11, uniformtext_mode="hide")
    return style_figure(fig, height=450)


def proportional_bar(
    df: pd.DataFrame, category_col: str, value_col: str, title: str
) -> go.Figure:
    """Horizontal bar — preferred over donut when there are many categories
    or many small slices that would clutter a pie."""
    sorted_df = df.sort_values(value_col, ascending=True)
    fig = px.bar(
        sorted_df,
        x=value_col,
        y=category_col,
        orientation="h",
        title=title,
        color_discrete_sequence=[PALETTE[0]],
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>$%{x:,.1f}<extra></extra>",
    )
    fig.update_yaxes(title=None)
    return style_figure(fig)

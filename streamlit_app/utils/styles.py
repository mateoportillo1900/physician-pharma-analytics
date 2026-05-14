"""
Global UI styling for the Pharma Analytics dashboard.

Centralizes:
  • Custom CSS overrides (typography, spacing, hiding Streamlit chrome)
  • The shared page_icon (consistent across all pages)
  • Helper for rendering professional KPI cards
"""

from __future__ import annotations

import streamlit as st


# ── Identity ─────────────────────────────────────────────────────────────────
# Single source of truth for the app icon. Used in every page's
# st.set_page_config call. Change here, propagates everywhere.
PAGE_ICON = "📊"
APP_NAME = "Pharma Analytics"


# ── Color palette ────────────────────────────────────────────────────────────
COLORS = {
    "primary": "#1E3A8A",  # deep navy
    "primary_light": "#3B82F6",  # bright blue
    "accent": "#F59E0B",  # amber
    "success": "#10B981",  # emerald
    "danger": "#EF4444",  # red
    "neutral_900": "#0F172A",
    "neutral_700": "#334155",
    "neutral_500": "#64748B",
    "neutral_300": "#CBD5E1",
    "neutral_100": "#F1F5F9",
    "neutral_50": "#F8FAFC",
}


# ── Global CSS ───────────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
/* ── Typography ──────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Bigger, tighter headings */
h1 {
    font-weight: 800 !important;
    font-size: 1.9rem !important;
    line-height: 1.1 !important;
    letter-spacing: -0.025em !important;
    color: #0F172A !important;
    margin-top: 0 !important;
    margin-bottom: 0.35rem !important;
    padding-top: 0 !important;
}

h2 {
    font-weight: 700 !important;
    font-size: 1.35rem !important;
    letter-spacing: -0.015em !important;
    color: #1E293B !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.5rem !important;
}

h3 {
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    color: #334155 !important;
    margin-top: 1rem !important;
}

/* ── Hide Streamlit chrome ───────────────────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; height: 0; }
.stDeployButton { display: none; }
div[data-testid="stToolbar"] { display: none; }

/* ── Layout — wider main content, tight top padding ─────────────────────── */
.main .block-container {
    max-width: 1280px;
    padding-top: 1.25rem;
    padding-bottom: 3rem;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #0F172A;
    border-right: 1px solid #1E293B;
}
section[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #F8FAFC !important;
}
section[data-testid="stSidebar"] a {
    color: #93C5FD !important;
    text-decoration: none !important;
}

/* Sidebar branding block */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 0.5rem 0 0.25rem 0;
}
.sidebar-brand-icon {
    font-size: 1.6rem;
    line-height: 1;
}
.sidebar-brand-name {
    font-size: 1.15rem;
    font-weight: 700;
    color: #F8FAFC !important;
    letter-spacing: -0.01em;
}
.sidebar-tagline {
    color: #94A3B8 !important;
    font-size: 0.78rem;
    line-height: 1.4;
    margin-bottom: 0.25rem;
}

/* Sidebar section label (uppercase mini-heading like "VIEWS" / "SOURCES") */
.sidebar-nav-label {
    color: #64748B !important;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 0.25rem 0 0.5rem 0;
}

/* st.page_link styling — highlight the current page */
section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
    padding: 0.5rem 0.75rem;
    border-radius: 8px;
    margin: 1px 0;
    transition: background 0.15s;
    color: #CBD5E1 !important;
    font-weight: 500;
}
section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
    background: rgba(255,255,255,0.05);
    color: #F8FAFC !important;
}

/* ── KPI cards (st.metric) ───────────────────────────────────────────────── */
div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
    transition: box-shadow 0.2s, transform 0.2s;
}
div[data-testid="stMetric"]:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
    transform: translateY(-1px);
}
div[data-testid="stMetric"] label {
    color: #64748B !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #0F172A !important;
    font-weight: 700 !important;
    font-size: 1.875rem !important;
    margin-top: 0.25rem !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
    color: #64748B !important;
}

/* ── Hero / sub-headline below page title ────────────────────────────────── */
.app-hero-sub {
    font-size: 1rem;
    color: #475569;
    line-height: 1.5;
    margin-top: 0.15rem;
    margin-bottom: 1.25rem;
    max-width: 760px;
}
.app-hero-meta {
    font-size: 0.75rem;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 1rem;
}

/* ── Section heading badge ───────────────────────────────────────────────── */
.section-heading {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    font-size: 0.72rem;
    font-weight: 600;
    color: #1E3A8A;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
}
.section-heading::before {
    content: "";
    width: 5px;
    height: 5px;
    background: #F59E0B;
    border-radius: 50%;
}

/* ── Subtle divider line ─────────────────────────────────────────────────── */
hr[data-testid="stDivider"] {
    margin: 2rem 0 1.5rem 0;
    border-color: #E2E8F0;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
button[kind="secondary"],
button[data-testid="baseButton-secondary"] {
    background: #FFFFFF;
    color: #1E3A8A;
    border: 1px solid #CBD5E1;
    font-weight: 500;
    border-radius: 8px;
    padding: 0.4rem 1rem;
    transition: all 0.15s;
}
button[kind="secondary"]:hover,
button[data-testid="baseButton-secondary"]:hover {
    background: #F1F5F9;
    border-color: #1E3A8A;
    color: #1E3A8A;
}

/* ── Selectbox + multiselect ─────────────────────────────────────────────── */
div[data-baseweb="select"] > div {
    border-color: #CBD5E1 !important;
    border-radius: 8px !important;
}

/* ── Info / warning banners ──────────────────────────────────────────────── */
div[data-testid="stAlert"] {
    border-radius: 8px;
    border-left-width: 4px;
}

/* ── Expander ────────────────────────────────────────────────────────────── */
div[data-testid="stExpander"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
}
div[data-testid="stExpander"] summary {
    font-weight: 500;
    color: #1E293B;
}

/* ── DataFrames ──────────────────────────────────────────────────────────── */
div[data-testid="stDataFrame"] {
    border-radius: 8px;
    border: 1px solid #E2E8F0;
    overflow: hidden;
}

/* ── Plotly chart container — give some breathing room ───────────────────── */
div[data-testid="stPlotlyChart"] {
    margin-bottom: 0.5rem;
}

/* ── Hero card with gradient background ─────────────────────────────────── */
.hero-card {
    background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 55%, #6D28D9 100%);
    border-radius: 16px;
    padding: 2rem 2.25rem 1.75rem 2.25rem;
    margin-bottom: 1.5rem;
    color: #F8FAFC;
    box-shadow: 0 10px 30px rgba(15,23,42,0.18);
    position: relative;
    overflow: hidden;
}
.hero-card::before {
    /* Decorative geometric pattern in the corner */
    content: "";
    position: absolute;
    top: -40px;
    right: -40px;
    width: 220px;
    height: 220px;
    background: radial-gradient(circle, rgba(245,158,11,0.18) 0%, transparent 70%);
    pointer-events: none;
}
.hero-card-tag {
    display: inline-block;
    background: rgba(245,158,11,0.18);
    color: #FBBF24;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 4px 12px;
    border-radius: 999px;
    margin-bottom: 1rem;
}
.hero-card-title {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    line-height: 1.1;
    color: #F8FAFC !important;
    margin: 0 0 0.6rem 0;
}
.hero-card-title .accent {
    background: linear-gradient(90deg, #FBBF24, #F472B6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-card-sub {
    color: #CBD5E1;
    font-size: 1rem;
    line-height: 1.6;
    max-width: 780px;
    margin: 0 0 1.25rem 0;
}
/* Single accent style for the *one* highlighted phrase in the subtitle —
   white-bold, no color, so it doesn't compete with the title gradient. */
.hero-card-sub strong {
    color: #FFFFFF;
    font-weight: 600;
}

/* KPI strip inside the hero */
.hero-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem;
    margin-top: 0.5rem;
}
.hero-stat { padding: 0.4rem 0; }
.hero-stat-value {
    font-size: 1.7rem;
    font-weight: 800;
    color: #F8FAFC;
    letter-spacing: -0.01em;
    line-height: 1.15;
}
.hero-stat-label {
    color: #94A3B8;
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 0.15rem;
}

/* Tech pills row — each gets a per-technology accent color */
.hero-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin-top: 1.25rem;
}
.hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(15,23,42,0.55);
    color: #F1F5F9;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 5px 11px;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.10);
    backdrop-filter: blur(4px);
}
.hero-pill::before {
    content: "";
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
    opacity: 0.95;
}
.hero-pill.postgres { color: #60A5FA; }   /* blue */
.hero-pill.dbt      { color: #FB923C; }   /* orange */
.hero-pill.streamlit{ color: #F87171; }   /* red */
.hero-pill.groq     { color: #34D399; }   /* emerald */
.hero-pill.plotly   { color: #A78BFA; }   /* violet */
.hero-pill .pill-text { color: #F1F5F9; }

/* ── Chart-level intro block: explains what + what to look for ───────────── */
.chart-intro {
    background: #F8FAFC;
    border-left: 3px solid #1E3A8A;
    border-radius: 4px;
    padding: 0.7rem 0.9rem;
    margin: 0.2rem 0 0.8rem 0;
    font-size: 0.85rem;
    line-height: 1.5;
    color: #334155;
}
.chart-intro b { color: #1E3A8A; }

/* ── Page guidance callout — "What you're looking at" ───────────────────── */
.page-guide {
    background: linear-gradient(180deg, #F1F5F9 0%, #FFFFFF 100%);
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 1.25rem;
}
.page-guide-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #1E3A8A;
    margin-bottom: 0.5rem;
}
.page-guide-title::before {
    content: "→";
    color: #F59E0B;
    font-weight: 700;
}
.page-guide-body {
    color: #334155;
    font-size: 0.92rem;
    line-height: 1.55;
}
.page-guide-body strong { color: #0F172A; }

</style>
"""


def apply_global_styles() -> None:
    """Inject the global CSS. Call this once at the top of each page."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def section_heading(label: str) -> None:
    """Render an uppercase section badge (e.g., 'OVERVIEW', 'INSIGHTS')."""
    st.markdown(
        f'<div class="section-heading">{label}</div>',
        unsafe_allow_html=True,
    )


def _md_bold_to_html(text: str) -> str:
    """Convert `**bold**` markdown to `<strong>` HTML.

    Needed because when we wrap text in an HTML <div> and pass it to
    st.markdown, Streamlit treats the contents as HTML and skips its
    markdown processor — so `**bold**` would render as literal asterisks.
    """
    import re  # noqa: PLC0415

    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


def hero(title: str, subtitle: str, meta: str | None = None) -> None:
    """Render the consistent (plain) hero section at the top of a sub-page.

    For the Executive Dashboard's gradient hero card, use `hero_card`.
    """
    st.markdown(f"# {title}")
    st.markdown(
        f'<div class="app-hero-sub">{_md_bold_to_html(subtitle)}</div>',
        unsafe_allow_html=True,
    )
    if meta:
        st.markdown(
            f'<div class="app-hero-meta">{meta}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="margin-bottom: 1.5rem"></div>',
            unsafe_allow_html=True,
        )


def hero_card(
    tag: str,
    title_lead: str,
    title_accent: str,
    subtitle: str,
    stats: list[tuple[str, str]],
    pills: list[tuple[str, str]] | None = None,
) -> None:
    """Render the gradient hero card for the dashboard landing.

    Args:
        tag: small uppercase pill label (e.g. "COMMERCIAL ANALYTICS")
        title_lead: white portion of the title (e.g. "Physician × Pharma")
        title_accent: gradient-colored portion (e.g. "Analytics")
        subtitle: one-sentence description (supports **bold**)
        stats: list of (value, label) tuples shown in the KPI strip
        pills: optional list of (label, css_class) tuples for tech badges.
            Class names available: postgres, dbt, streamlit, groq, plotly.
    """
    stats_html = "".join(
        f'<div class="hero-stat">'
        f'<div class="hero-stat-value">{val}</div>'
        f'<div class="hero-stat-label">{lab}</div>'
        f"</div>"
        for val, lab in stats
    )
    pills_html = ""
    if pills:
        pill_items = "".join(
            f'<span class="hero-pill {css_class}">'
            f'<span class="pill-text">{label}</span>'
            f"</span>"
            for label, css_class in pills
        )
        pills_html = f'<div class="hero-pills">{pill_items}</div>'

    html = (
        f'<div class="hero-card">'
        f'<div class="hero-card-tag">{tag}</div>'
        f'<div class="hero-card-title">{title_lead} '
        f'<span class="accent">{title_accent}</span></div>'
        f'<div class="hero-card-sub">{_md_bold_to_html(subtitle)}</div>'
        f'<div class="hero-stats">{stats_html}</div>'
        f"{pills_html}"
        f"</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def page_guide(title: str, body: str) -> None:
    """Render a "What you're looking at / How to use" callout near the top
    of a sub-page. Title is uppercase, body supports **bold** markdown.
    """
    html = (
        '<div class="page-guide">'
        f'<div class="page-guide-title">{title}</div>'
        f'<div class="page-guide-body">{_md_bold_to_html(body)}</div>'
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def chart_intro(body: str) -> None:
    """Render a small intro / interpretation hint above a chart.

    Supports **bold** markdown. Place immediately before the chart.
    """
    html = f'<div class="chart-intro">{_md_bold_to_html(body)}</div>'
    st.markdown(html, unsafe_allow_html=True)


PAGE_CARD_CSS = """
<style>
.page-card-row {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    margin-top: 0.5rem;
    margin-bottom: 1.5rem;
}
.page-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #1E3A8A;
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    transition: transform 0.15s, box-shadow 0.15s;
}
.page-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(15,23,42,0.08);
}
.page-card-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 0.3rem;
}
.page-card-tag {
    display: inline-block;
    background: #F1F5F9;
    color: #1E3A8A;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 2px 8px;
    border-radius: 4px;
    margin-bottom: 0.5rem;
}
.page-card-desc {
    color: #475569;
    font-size: 0.92rem;
    line-height: 1.55;
}
</style>
"""


def render_page_cards(cards: list[dict]) -> None:
    """Render a 2-column grid of page-purpose cards on the landing page.

    Each card dict: {tag, title, description}

    NB: Streamlit's markdown processor interprets lines indented 4+ spaces
    as code blocks, so the HTML must be left-aligned (no leading whitespace
    per line) for `unsafe_allow_html` to actually render it as HTML and
    not display the raw <div> tags.
    """
    st.markdown(PAGE_CARD_CSS, unsafe_allow_html=True)

    parts = ['<div class="page-card-row">']
    for card in cards:
        parts.append(
            '<div class="page-card">'
            f'<div class="page-card-tag">{card["tag"]}</div>'
            f'<div class="page-card-title">{card["title"]}</div>'
            f'<div class="page-card-desc">{card["description"]}</div>'
            "</div>"
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)

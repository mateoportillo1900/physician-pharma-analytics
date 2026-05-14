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
    "primary": "#1E3A8A",       # deep navy
    "primary_light": "#3B82F6", # bright blue
    "accent": "#F59E0B",        # amber
    "success": "#10B981",       # emerald
    "danger": "#EF4444",        # red
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
    font-size: 2.25rem !important;
    line-height: 1.15 !important;
    letter-spacing: -0.025em !important;
    color: #0F172A !important;
    margin-bottom: 0.4rem !important;
}

h2 {
    font-weight: 700 !important;
    font-size: 1.5rem !important;
    letter-spacing: -0.015em !important;
    color: #1E293B !important;
    margin-top: 2rem !important;
    margin-bottom: 0.75rem !important;
}

h3 {
    font-weight: 600 !important;
    font-size: 1.125rem !important;
    color: #334155 !important;
    margin-top: 1.5rem !important;
}

/* ── Hide Streamlit chrome ───────────────────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; height: 0; }
.stDeployButton { display: none; }
div[data-testid="stToolbar"] { display: none; }

/* ── Layout — wider main content ─────────────────────────────────────────── */
.main .block-container {
    max-width: 1280px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
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
    color: #60A5FA !important;
}
/* sidebar nav links */
section[data-testid="stSidebarNav"] a {
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    transition: background 0.15s;
}
section[data-testid="stSidebarNav"] a:hover {
    background: rgba(255,255,255,0.05);
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
    font-size: 1.05rem;
    color: #475569;
    line-height: 1.55;
    margin-top: 0.25rem;
    margin-bottom: 0.5rem;
    max-width: 760px;
}
.app-hero-meta {
    font-size: 0.8rem;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 1.5rem;
}

/* ── Section heading badge ───────────────────────────────────────────────── */
.section-heading {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.78rem;
    font-weight: 600;
    color: #1E3A8A;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 2rem;
    margin-bottom: 0.4rem;
}
.section-heading::before {
    content: "";
    width: 6px;
    height: 6px;
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


def hero(title: str, subtitle: str, meta: str | None = None) -> None:
    """Render the consistent hero section at the top of each page."""
    st.markdown(f"# {title}")
    st.markdown(
        f'<div class="app-hero-sub">{subtitle}</div>',
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
    """
    st.markdown(PAGE_CARD_CSS, unsafe_allow_html=True)

    cards_html = ['<div class="page-card-row">']
    for card in cards:
        cards_html.append(f"""
            <div class="page-card">
                <div class="page-card-tag">{card['tag']}</div>
                <div class="page-card-title">{card['title']}</div>
                <div class="page-card-desc">{card['description']}</div>
            </div>
        """)
    cards_html.append("</div>")
    st.markdown("\n".join(cards_html), unsafe_allow_html=True)

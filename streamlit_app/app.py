"""
Physician × Pharma Commercial Analytics — entry point
═════════════════════════════════════════════════════

Uses Streamlit's st.navigation() API to define the page set explicitly.
This gives full control over:
  • The labels shown in the sidebar (no more "app" from filename)
  • Page order
  • Per-page icons
  • The default page on first load

Run locally:
    streamlit run streamlit_app/app.py

Deploy:
    Streamlit Cloud → set "Main file path" to streamlit_app/app.py.
"""

from __future__ import annotations

import streamlit as st

from utils.styles import APP_NAME, PAGE_ICON, apply_global_styles

st.set_page_config(
    page_title=APP_NAME,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject global CSS once so it applies to every page in the navigation
apply_global_styles()


# ─── Sidebar identity ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"## {PAGE_ICON}  {APP_NAME}")
    st.caption(
        "Commercial intelligence on CMS Open Payments + Medicare Part D "
        "(2022 reporting year)."
    )


# ─── Page registry ───────────────────────────────────────────────────────────
nav = st.navigation([
    st.Page(
        "views/dashboard.py",
        title="Executive Dashboard",
        icon=":material/dashboard:",
        default=True,
    ),
    st.Page(
        "views/kol_finder.py",
        title="KOL Finder",
        icon=":material/search:",
    ),
    st.Page(
        "views/company_intelligence.py",
        title="Company Intelligence",
        icon=":material/business:",
    ),
    st.Page(
        "views/payment_vs_prescribing.py",
        title="Payment vs. Prescribing",
        icon=":material/trending_up:",
    ),
    st.Page(
        "views/market_map.py",
        title="Market Opportunity Map",
        icon=":material/map:",
    ),
])


# ─── Sidebar footer (rendered below the auto-nav from st.navigation) ────────
with st.sidebar:
    st.divider()
    st.caption(
        "**Sources**  \n"
        "[CMS Open Payments](https://www.cms.gov/openpayments)  \n"
        "[Medicare Part D PUF](https://data.cms.gov)"
    )
    st.caption(
        "All physician identifiers are anonymized surrogate IDs (e.g. "
        "`Physician #4837`)."
    )


nav.run()

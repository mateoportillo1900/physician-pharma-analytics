"""
Physician × Pharma Commercial Analytics — entry point
═════════════════════════════════════════════════════

Uses Streamlit's st.navigation() API with `position="hidden"` so we
hide the auto-rendered nav and build a custom sidebar (branding ABOVE
the page links) using st.page_link.

Run locally:
    streamlit run streamlit_app/app.py
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

apply_global_styles()


# ─── Page registry — auto-nav hidden, we'll render our own ──────────────────
nav = st.navigation(
    [
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
    ],
    position="hidden",
)


# ─── Custom sidebar (full control over order) ────────────────────────────────
with st.sidebar:
    # 1. Branding — at the top
    st.markdown(
        f"""
<div class="sidebar-brand">
  <div class="sidebar-brand-icon">{PAGE_ICON}</div>
  <div class="sidebar-brand-name">{APP_NAME}</div>
</div>
<div class="sidebar-tagline">
  Commercial intelligence on CMS Open Payments + Medicare Part D · 2022.
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # 2. Navigation — our own page_link list, in our own order
    st.markdown(
        '<div class="sidebar-nav-label">VIEWS</div>',
        unsafe_allow_html=True,
    )
    st.page_link("views/dashboard.py", label="Executive Dashboard",
                 icon=":material/dashboard:")
    st.page_link("views/kol_finder.py", label="KOL Finder",
                 icon=":material/search:")
    st.page_link("views/company_intelligence.py", label="Company Intelligence",
                 icon=":material/business:")
    st.page_link("views/payment_vs_prescribing.py", label="Payment vs. Prescribing",
                 icon=":material/trending_up:")
    st.page_link("views/market_map.py", label="Market Opportunity Map",
                 icon=":material/map:")

    st.divider()

    # 3. Sources + privacy note at the bottom
    st.markdown(
        '<div class="sidebar-nav-label">SOURCES</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "[CMS Open Payments](https://www.cms.gov/openpayments)  \n"
        "[Medicare Part D PUF](https://data.cms.gov)",
    )
    st.caption(
        "All physician identifiers are anonymized surrogate IDs "
        "(e.g. `Physician #4837`)."
    )


nav.run()

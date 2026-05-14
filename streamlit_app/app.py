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

from utils.styles import APP_NAME, GITHUB_URL, PAGE_ICON, apply_global_styles

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
<a class="sidebar-github" href="{GITHUB_URL}" target="_blank" rel="noopener">
  <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"
       xmlns="http://www.w3.org/2000/svg">
    <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38v-1.32c-2.22.48-2.69-1.07-2.69-1.07-.36-.93-.89-1.18-.89-1.18-.73-.5.06-.49.06-.49.81.06 1.23.83 1.23.83.72 1.23 1.88.87 2.34.67.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.58.82-2.14-.08-.2-.36-1.01.08-2.1 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.03 2.2-.82 2.2-.82.44 1.09.16 1.9.08 2.1.51.56.82 1.27.82 2.14 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48v2.19c0 .21.15.46.55.38C13.71 14.53 16 11.54 16 8c0-4.42-3.58-8-8-8z"/>
  </svg>
  <span>View on GitHub</span>
</a>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # 2. Navigation — our own page_link list, in our own order
    st.markdown(
        '<div class="sidebar-nav-label">VIEWS</div>',
        unsafe_allow_html=True,
    )
    st.page_link(
        "views/dashboard.py", label="Executive Dashboard", icon=":material/dashboard:"
    )
    st.page_link("views/kol_finder.py", label="KOL Finder", icon=":material/search:")
    st.page_link(
        "views/company_intelligence.py",
        label="Company Intelligence",
        icon=":material/business:",
    )
    st.page_link(
        "views/payment_vs_prescribing.py",
        label="Payment vs. Prescribing",
        icon=":material/trending_up:",
    )
    st.page_link(
        "views/market_map.py", label="Market Opportunity Map", icon=":material/map:"
    )

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

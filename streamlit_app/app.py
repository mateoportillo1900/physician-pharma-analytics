"""
Physician–Pharma Commercial Analytics Platform
═══════════════════════════════════════════════

Streamlit entry point. The four sub-pages live in streamlit_app/pages/
and are auto-discovered by Streamlit's multipage router.

Run locally:
    streamlit run streamlit_app/app.py
"""

from __future__ import annotations

import streamlit as st

from utils.charts import bar_chart, proportional_bar
from utils.db import run_query
from utils.llm import render_explain_button
from utils.styles import (
    APP_NAME,
    PAGE_ICON,
    apply_global_styles,
    hero,
    render_page_cards,
    section_heading,
)

# ─── Page config — first Streamlit call, must precede everything else ────────
st.set_page_config(
    page_title=f"{APP_NAME} | Executive Dashboard",
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_global_styles()


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"## {PAGE_ICON}  {APP_NAME}")
    st.caption("Commercial intelligence on CMS Open Payments + Medicare Part D")
    st.divider()
    st.caption(
        "**Sources** · "
        "[CMS Open Payments](https://www.cms.gov/openpayments) · "
        "[Medicare Part D PUF](https://data.cms.gov)"
    )
    st.caption(
        "All physician identifiers in this app are anonymized "
        "surrogate IDs (e.g. `Physician #4837`)."
    )


# ─── Hero — clear "what is this and who is it for" ───────────────────────────
hero(
    title="Physician × Pharma Commercial Analytics",
    subtitle=(
        "A self-serve analytics platform that joins **CMS Open Payments** "
        "(every dollar pharma companies pay U.S. physicians, required by the "
        "Sunshine Act) with **Medicare Part D Prescribing** data — answering "
        "the core question every pharma commercial team analyzes: "
        "**do paid physicians prescribe more of that company's drugs?**"
    ),
    meta="2022 reporting year · 10 tracked manufacturers · 391,234 payment records · 815,863 physicians",
)


# ─── What's inside ───────────────────────────────────────────────────────────
section_heading("What you can explore")

st.markdown(
    "The app has five views, each answering a different commercial-analytics "
    "question. Use the sidebar navigation, or read the descriptions below to "
    "decide where to start."
)

render_page_cards(
    [
        {
            "tag": "📊  Executive Dashboard",
            "title": "This page",
            "description": (
                "Where the money goes overall — top spenders, payment-type "
                "breakdown, which physician specialties get paid most, and a "
                "first look at the paid-vs-unpaid prescribing comparison."
            ),
        },
        {
            "tag": "🔍  KOL Finder",
            "title": "Find the top prescribers in any therapeutic class",
            "description": (
                "Filter by class (Oncology, Endocrinology, etc.), state, and "
                "payment status. Get a ranked list of the highest-volume "
                "Medicare Part D prescribers — the people pharma commercial "
                "teams call KOLs (Key Opinion Leaders)."
            ),
        },
        {
            "tag": "🏢  Company Intelligence",
            "title": "Deep dive on a single manufacturer",
            "description": (
                "Pick AbbVie, Pfizer, etc., and see their entire 2022 "
                "commercial footprint: specialty mix, payment-type mix, "
                "geographic distribution, and the top 25 physicians they paid."
            ),
        },
        {
            "tag": "📈  Payment vs. Prescribing",
            "title": "The headline research question",
            "description": (
                "Reproduces the methodology from DeJong et al. (JAMA Internal "
                "Medicine, 2016): do physicians who receive payments from a "
                "company prescribe more of that company's drugs — controlled "
                "for specialty? Includes lift ratio + correlation."
            ),
        },
        {
            "tag": "🗺️  Market Opportunity Map",
            "title": "Geographic over/under-investment",
            "description": (
                "Where is pharma over- or under-invested relative to actual "
                "prescribing volume? A US choropleth showing 'investment ratio' "
                "(payment share ÷ Rx share) — the classic territory-planning view."
            ),
        },
    ]
)


st.divider()


# ─── KPI strip ───────────────────────────────────────────────────────────────
section_heading("At a glance")

kpis = run_query("""
    SELECT
        (SELECT COUNT(*)  FROM raw_mart.fact_payments)             AS payment_count,
        (SELECT SUM(payment_amount_usd) FROM raw_mart.fact_payments) AS total_payments,
        (SELECT COUNT(DISTINCT company_name)
            FROM raw_mart.fact_payments)                           AS companies,
        (SELECT COUNT(DISTINCT physician_npi)
            FROM raw_mart.fact_payments)                           AS paid_physicians,
        (SELECT COUNT(*)  FROM raw_mart.dim_physician)             AS total_physicians
""")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Pharma Spend (2022)", f"${kpis['total_payments'].iloc[0] / 1e6:.0f}M")
c2.metric("Payment Records", f"{kpis['payment_count'].iloc[0]:,}")
c3.metric("Manufacturers Tracked", f"{kpis['companies'].iloc[0]:,}")
c4.metric("Paid Physicians", f"{kpis['paid_physicians'].iloc[0]:,}")
st.caption(
    f"Across {kpis['total_physicians'].iloc[0]:,} unique physicians in the "
    "joined dataset (Medicare Part D prescribers + Open Payments recipients)."
)


# ─── Row 1: Top companies + payment categories ───────────────────────────────
section_heading("Where the money goes")

col1, col2 = st.columns([3, 2])

with col1:
    top_companies = run_query("""
        SELECT
            company_name,
            ROUND(SUM(payment_amount_usd)::numeric / 1e6, 2) AS spend_millions
        FROM raw_mart.fact_payments
        GROUP BY company_name
        ORDER BY spend_millions DESC
    """)
    fig = bar_chart(
        top_companies.sort_values("spend_millions"),
        x="spend_millions",
        y="company_name",
        title="2022 Spend by Manufacturer ($M)",
        orientation="h",
    )
    fig.update_xaxes(title="Spend ($ Millions)")
    fig.update_yaxes(title=None)
    st.plotly_chart(fig, use_container_width=True)

    render_explain_button(
        chart_title="Top Companies by Payments",
        business_question=(
            "Which pharmaceutical companies spent the most paying U.S. "
            "physicians in 2022, and what does the concentration look like?"
        ),
        data=top_companies,
        key_suffix="top_companies",
    )

with col2:
    payment_types = run_query("""
        SELECT
            payment_category,
            ROUND(SUM(payment_amount_usd)::numeric / 1e6, 2) AS spend_millions
        FROM raw_mart.fact_payments
        GROUP BY payment_category
        ORDER BY spend_millions DESC
    """)
    fig = proportional_bar(
        payment_types,
        category_col="payment_category",
        value_col="spend_millions",
        title="Spend by Payment Type ($M)",
    )
    fig.update_xaxes(title="Spend ($ Millions)")
    st.plotly_chart(fig, use_container_width=True)

    render_explain_button(
        chart_title="Payment Type Breakdown",
        business_question=(
            "What types of payments dominate pharma physician spending in "
            "2022? Speaking fees, consulting, royalties, meals?"
        ),
        data=payment_types,
        key_suffix="payment_types",
    )


# ─── Row 2: Spend by specialty + paid vs unpaid ─────────────────────────────
section_heading("Who receives the payments")

col3, col4 = st.columns(2)

with col3:
    spend_by_specialty = run_query("""
        SELECT
            dp.specialty,
            ROUND(SUM(fp.payment_amount_usd)::numeric / 1e6, 2) AS spend_millions,
            COUNT(DISTINCT fp.physician_npi) AS physicians_paid
        FROM raw_mart.fact_payments AS fp
        JOIN raw_mart.dim_physician AS dp USING (physician_npi)
        WHERE dp.specialty IS NOT NULL AND dp.specialty != 'Unknown'
        GROUP BY dp.specialty
        ORDER BY spend_millions DESC
        LIMIT 12
    """)
    fig = bar_chart(
        spend_by_specialty.sort_values("spend_millions"),
        x="spend_millions",
        y="specialty",
        title="Top 12 Specialties by Payments Received ($M)",
        orientation="h",
    )
    fig.update_xaxes(title="Spend ($ Millions)")
    fig.update_yaxes(title=None)
    st.plotly_chart(fig, use_container_width=True)

    render_explain_button(
        chart_title="Spend by Specialty",
        business_question=(
            "Which physician specialties received the most pharma payments, "
            "and what does that reveal about pharma's commercial priorities?"
        ),
        data=spend_by_specialty,
        key_suffix="spec_spend",
    )

with col4:
    paid_vs_unpaid = run_query("""
        SELECT
            CASE WHEN received_pharma_payments
                THEN 'Received payments'
                ELSE 'No payments'
            END AS group_label,
            COUNT(*) AS n_physicians,
            ROUND(AVG(total_claim_count)::numeric, 0) AS avg_claims
        FROM raw_mart.dim_physician
        WHERE total_claim_count IS NOT NULL
        GROUP BY received_pharma_payments
    """)
    fig = bar_chart(
        paid_vs_unpaid,
        x="group_label",
        y="avg_claims",
        title="Mean Part D Claims: Paid vs. Unpaid Physicians",
        color="group_label",
    )
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="Average Claims per Physician")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    render_explain_button(
        chart_title="Paid vs. Unpaid Physician Prescribing",
        business_question=(
            "Do physicians who received pharma payments prescribe more "
            "than those who didn't, on average? (Specialty-controlled "
            "version is on the Payment vs. Prescribing page.)"
        ),
        data=paid_vs_unpaid,
        key_suffix="paid_vs_unpaid",
    )


# ─── Footer ──────────────────────────────────────────────────────────────────
st.divider()

with st.expander("Data sources, methodology, and disclaimers"):
    st.markdown(
        """
        **Data sources.** All data in this app comes from two publicly
        released federal datasets:
        - **CMS Open Payments** (openpaymentsdata.cms.gov) — pharma-to-physician
          payment disclosures required by the Sunshine Act
        - **CMS Medicare Part D Prescriber Public Use File** (data.cms.gov) —
          aggregated, de-identified prescribing data published by CMS for
          research and transparency

        **No patient data is processed by this application.** The Part D
        file is aggregated at the provider level; cell counts under 11
        are pre-suppressed by CMS. Physician NPIs are professional
        identifiers, not PHI under HIPAA, but the app exposes only
        anonymized surrogate IDs (e.g., `Physician #4837`).

        **Methodology.** Analyses are **descriptive, not causal**. Payment
        and prescribing relationships in observational data may reflect
        physicians self-selecting into pharma relationships based on
        existing prescribing patterns. See `METHODOLOGY.md` in the source
        repository for the full discussion of limitations.

        **Purpose.** This is a portfolio project demonstrating
        commercial-analytics tradecraft. It is not investigative
        journalism and makes no claims about the propriety of any
        specific payment-prescribing relationship.
        """
    )

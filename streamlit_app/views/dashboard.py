"""
Executive Dashboard
═══════════════════

Default landing view. Tight hero, KPIs immediately below, then key
"where the money goes" + "who receives it" charts. Page-purpose cards
are tucked into an expander so they don't push KPIs below the fold.
"""

from __future__ import annotations

import streamlit as st

from utils.charts import bar_chart, proportional_bar
from utils.db import run_query
from utils.llm import render_explain_button
from utils.styles import (
    apply_global_styles,
    hero,
    render_page_cards,
    section_heading,
)

apply_global_styles()

# ─── Hero — single tight sentence ────────────────────────────────────────────
hero(
    title="Executive Dashboard",
    subtitle=(
        "Where pharma money flows in 2022 — and a first read on whether "
        "**paid physicians prescribe more.**"
    ),
)

# ─── KPI strip — immediately visible ─────────────────────────────────────────
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
c1.metric("Total 2022 Spend", f"${kpis['total_payments'].iloc[0] / 1e6:.0f}M")
c2.metric("Payment Records", f"{kpis['payment_count'].iloc[0]:,}")
c3.metric("Manufacturers", f"{kpis['companies'].iloc[0]:,}")
c4.metric("Paid Physicians", f"{kpis['paid_physicians'].iloc[0]:,}")


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
    fig.update_xaxes(title="$ Millions")
    fig.update_yaxes(title=None)
    st.plotly_chart(fig, use_container_width=True)

    render_explain_button(
        chart_title="Top Companies by Payments",
        business_question=(
            "Which pharmaceutical companies spent the most paying U.S. "
            "physicians in 2022, and how concentrated is the spend?"
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
    fig.update_xaxes(title="$ Millions")
    st.plotly_chart(fig, use_container_width=True)

    render_explain_button(
        chart_title="Payment Type Breakdown",
        business_question=(
            "What types of payments dominate pharma physician spending? "
            "Speaking fees, consulting, royalties, meals?"
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
            ROUND(SUM(fp.payment_amount_usd)::numeric / 1e6, 2) AS spend_millions
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
    fig.update_xaxes(title="$ Millions")
    fig.update_yaxes(title=None)
    st.plotly_chart(fig, use_container_width=True)

    render_explain_button(
        chart_title="Spend by Specialty",
        business_question=(
            "Which physician specialties received the most pharma payments, "
            "and what does that reveal about commercial priorities?"
        ),
        data=spend_by_specialty,
        key_suffix="spec_spend",
    )

with col4:
    paid_vs_unpaid = run_query("""
        SELECT
            CASE WHEN received_pharma_payments
                THEN 'Received payments' ELSE 'No payments'
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
        title="Mean Part D Claims — Paid vs. Unpaid",
        color="group_label",
    )
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="Claims / physician")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    render_explain_button(
        chart_title="Paid vs. Unpaid Physician Prescribing",
        business_question=(
            "Do physicians who received pharma payments prescribe more "
            "than those who didn't? (Specialty-controlled version on "
            "the Payment vs. Prescribing view.)"
        ),
        data=paid_vs_unpaid,
        key_suffix="paid_vs_unpaid",
    )


# ─── About / page guide — tucked below the fold in an expander ──────────────
st.divider()

with st.expander("About this app & the four sub-views"):
    st.markdown(
        "A self-serve analytics platform that joins **CMS Open Payments** "
        "(every dollar pharma companies pay U.S. physicians, required by "
        "the Sunshine Act) with **Medicare Part D Prescribing** data, on "
        "the 2022 reporting year.\n\n"
        "Use the sidebar to navigate. Here's what each sub-view does:"
    )

    render_page_cards([
        {
            "tag": "KOL Finder",
            "title": "Top prescribers in any therapeutic class",
            "description": (
                "Filter by class, state, and payment status to surface the "
                "highest-volume Medicare Part D prescribers — pharma's "
                "Key Opinion Leaders."
            ),
        },
        {
            "tag": "Company Intelligence",
            "title": "Deep dive on a single manufacturer",
            "description": (
                "Specialty mix, payment-type mix, geographic distribution, "
                "and top 25 paid physicians for any company."
            ),
        },
        {
            "tag": "Payment vs. Prescribing",
            "title": "The headline research question",
            "description": (
                "Reproduces DeJong et al. (JAMA, 2016): do paid physicians "
                "prescribe more, controlled for specialty? Lift ratio + "
                "Pearson correlation."
            ),
        },
        {
            "tag": "Market Opportunity Map",
            "title": "Geographic over/under-investment",
            "description": (
                "US choropleth showing payment share ÷ Rx share. Highlights "
                "states pharma is over- or under-investing relative to "
                "actual prescribing volume."
            ),
        },
    ])


with st.expander("Data sources, methodology, and disclaimers"):
    st.markdown(
        """
        **Data sources.** Two publicly released federal datasets:
        - **CMS Open Payments** (openpaymentsdata.cms.gov) — pharma-to-physician
          payment disclosures required by the Sunshine Act
        - **CMS Medicare Part D Prescriber Public Use File** (data.cms.gov) —
          aggregated, de-identified prescribing data

        **No patient data is processed.** The Part D file is aggregated at
        the provider level; cell counts under 11 are pre-suppressed by CMS.
        Physician identifiers in this app are anonymized surrogate IDs
        (e.g., `Physician #4837`).

        **Methodology.** Analyses are **descriptive, not causal**. Payment
        and prescribing relationships in observational data may reflect
        physicians self-selecting into pharma relationships based on
        existing prescribing patterns. See `METHODOLOGY.md` in the source
        repository for the full discussion.

        **Purpose.** A portfolio project demonstrating pharma commercial
        analytics tradecraft. Not investigative journalism, and makes no
        claims about any specific payment-prescribing relationship.
        """
    )

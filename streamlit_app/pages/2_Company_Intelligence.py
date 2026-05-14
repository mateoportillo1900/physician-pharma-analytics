"""
Company Intelligence
═══════════════════════

Drill into a single pharma company's commercial footprint:
  • Total spend, count of physicians paid
  • Spend by physician specialty
  • Geographic distribution of spend
  • Payment type mix (consulting, speaking, meals, etc.)
  • Top 25 physicians by payments received
"""

from __future__ import annotations

import streamlit as st

from utils.charts import bar_chart, choropleth_us, donut_chart
from utils.db import run_query
from utils.llm import render_explain_button
from utils.styles import APP_NAME, PAGE_ICON, apply_global_styles, hero, section_heading

st.set_page_config(
    page_title=f"{APP_NAME} | Company Intelligence",
    page_icon=PAGE_ICON,
    layout="wide",
)
apply_global_styles()

hero(
    title="Company Intelligence",
    subtitle=(
        "Deep dive into a pharmaceutical company's 2022 commercial "
        "footprint — where they invested, with whom, and on what."
    ),
)

# ─── Company selector ───────────────────────────────────────────────────────
section_heading("Select Company")

companies = run_query("""
    SELECT
        company_name,
        ROUND(SUM(payment_amount_usd)::numeric / 1e6, 1) AS total_m
    FROM raw_mart.fact_payments
    GROUP BY company_name
    ORDER BY total_m DESC
""")
companies["label"] = (
    companies["company_name"] + " ($" + companies["total_m"].astype(str) + "M)"
)

selected_label = st.selectbox("Company", companies["label"].tolist(),
                              label_visibility="collapsed")
selected_company = companies.loc[
    companies["label"] == selected_label, "company_name"
].iloc[0]


# ─── KPI strip ───────────────────────────────────────────────────────────────
section_heading(f"{selected_company} — At a Glance")

kpis = run_query(
    """
    SELECT
        SUM(payment_amount_usd) AS total_spend,
        COUNT(*) AS n_payments,
        COUNT(DISTINCT physician_npi) AS physicians_paid,
        AVG(payment_amount_usd) AS avg_payment
    FROM raw_mart.fact_payments
    WHERE company_name = %s
    """,
    params=(selected_company,),
)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Spend", f"${kpis['total_spend'].iloc[0] / 1e6:.1f}M")
c2.metric("Payment Records", f"{kpis['n_payments'].iloc[0]:,}")
c3.metric("Physicians Paid", f"{kpis['physicians_paid'].iloc[0]:,}")
c4.metric("Avg Payment", f"${kpis['avg_payment'].iloc[0]:,.0f}")


# ─── Row 1: Specialty + Payment Type ─────────────────────────────────────────
section_heading("Spend Mix")

col1, col2 = st.columns(2)

with col1:
    spec_df = run_query(
        """
        SELECT
            dp.specialty,
            ROUND(SUM(fp.payment_amount_usd)::numeric / 1000, 1) AS spend_k
        FROM raw_mart.fact_payments AS fp
        JOIN raw_mart.dim_physician AS dp USING (physician_npi)
        WHERE fp.company_name = %s
            AND dp.specialty IS NOT NULL AND dp.specialty != 'Unknown'
        GROUP BY dp.specialty
        ORDER BY spend_k DESC
        LIMIT 10
        """,
        params=(selected_company,),
    )
    fig = bar_chart(
        spec_df.sort_values("spend_k"),
        x="spend_k", y="specialty",
        title=f"Top 10 Specialties by Spend ($K)",
        orientation="h",
    )
    fig.update_xaxes(title="Spend ($ Thousands)")
    fig.update_yaxes(title=None)
    st.plotly_chart(fig, use_container_width=True)

    render_explain_button(
        chart_title=f"{selected_company} Spend by Specialty",
        business_question=(
            f"What does {selected_company}'s 2022 specialty investment mix "
            f"reveal about their therapeutic focus and commercial strategy?"
        ),
        data=spec_df,
        key_suffix=f"co_spec_{selected_company}",
    )

with col2:
    cat_df = run_query(
        """
        SELECT
            payment_category,
            ROUND(SUM(payment_amount_usd)::numeric / 1000, 1) AS spend_k
        FROM raw_mart.fact_payments
        WHERE company_name = %s
        GROUP BY payment_category
        ORDER BY spend_k DESC
        """,
        params=(selected_company,),
    )
    fig = donut_chart(
        cat_df, names="payment_category", values="spend_k",
        title="Payment Type Mix",
    )
    st.plotly_chart(fig, use_container_width=True)

    render_explain_button(
        chart_title=f"{selected_company} Payment Category Mix",
        business_question=(
            f"Is {selected_company} primarily paying for speaking, "
            f"consulting, meals, travel, or something else? What does "
            f"that say about their commercial engagement strategy?"
        ),
        data=cat_df,
        key_suffix=f"co_cat_{selected_company}",
    )


# ─── Row 2: Geographic Distribution ──────────────────────────────────────────
section_heading("Geographic Distribution")

geo_df = run_query(
    """
    SELECT
        recipient_state AS state,
        ROUND(SUM(payment_amount_usd)::numeric / 1000, 1) AS spend_k,
        COUNT(DISTINCT physician_npi) AS physicians
    FROM raw_mart.fact_payments
    WHERE company_name = %s
        AND recipient_state IS NOT NULL
        AND length(recipient_state) = 2
    GROUP BY recipient_state
    ORDER BY spend_k DESC
    """,
    params=(selected_company,),
)

fig = choropleth_us(
    geo_df, state_col="state", value_col="spend_k",
    title=f"2022 Spend by State ($K)",
)
st.plotly_chart(fig, use_container_width=True)

render_explain_button(
    chart_title=f"{selected_company} Geographic Spend",
    business_question=(
        f"Which states does {selected_company} invest the most in, and "
        f"are there concentrations or notable gaps in coverage?"
    ),
    data=geo_df.head(15),
    key_suffix=f"co_geo_{selected_company}",
)


# ─── Row 3: Top 25 Physicians Paid ───────────────────────────────────────────
section_heading("Top 25 Physicians Paid")

top_phys = run_query(
    """
    SELECT
        dp.physician_display_id,
        dp.specialty,
        dp.state,
        SUM(fp.payment_amount_usd) AS total_paid,
        COUNT(*) AS payment_count,
        MAX(fp.payment_amount_usd) AS largest_single
    FROM raw_mart.fact_payments AS fp
    JOIN raw_mart.dim_physician AS dp USING (physician_npi)
    WHERE fp.company_name = %s
    GROUP BY dp.physician_display_id, dp.specialty, dp.state
    ORDER BY total_paid DESC
    LIMIT 25
    """,
    params=(selected_company,),
)

display_top = top_phys.copy()
display_top["total_paid"] = display_top["total_paid"].apply(lambda x: f"${x:,.0f}")
display_top["largest_single"] = display_top["largest_single"].apply(
    lambda x: f"${x:,.0f}"
)
display_top.columns = ["Physician", "Specialty", "State", "Total Paid",
                       "# Payments", "Largest Single"]
st.dataframe(display_top, use_container_width=True, hide_index=True, height=400)

render_explain_button(
    chart_title=f"{selected_company} Top Physicians",
    business_question=(
        f"Who are {selected_company}'s most-paid physician relationships, "
        f"and what does the concentration look like — is spending broad or "
        f"focused on a small set of high-value KOLs?"
    ),
    data=top_phys,
    key_suffix=f"co_top_phys_{selected_company}",
)

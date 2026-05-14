"""
Payment vs. Prescribing
═══════════════════════

The analytical centerpiece. Reproduces the published research question
(DeJong et al. 2016, JAMA Internal Medicine): do physicians who receive
payments from a pharma company prescribe more of that company's drugs?

Backing analysis: dbt_project/analyses/02_payment_prescribing_correlation.sql
"""

from __future__ import annotations

import streamlit as st

from utils.charts import bar_chart, scatter_chart
from utils.db import run_query
from utils.llm import render_explain_button
from utils.styles import apply_global_styles, hero, section_heading

apply_global_styles()

hero(
    title="Payment vs. Prescribing",
    subtitle=(
        "Do paid physicians prescribe more of a company's drugs? "
        "The published research question, controlled for specialty."
    ),
)

st.info(
    "**Methodology note.** Analyses are descriptive, not causal. "
    "Observational data cannot distinguish *payment-influences-prescribing* "
    "from *prescribers-attract-payments*. Treat the lift ratio as an "
    "association measure, not a treatment effect."
)


# ─── Filters ─────────────────────────────────────────────────────────────────
section_heading("Filters")

companies = run_query("""
    SELECT DISTINCT company_name
    FROM raw_mart.fact_payment_prescribing
    WHERE total_payment_usd > 0 AND company_claim_count > 0
    ORDER BY company_name
""")["company_name"].tolist()

specialties = run_query("""
    SELECT DISTINCT specialty
    FROM raw_mart.fact_payment_prescribing
    WHERE specialty IS NOT NULL AND specialty != 'Unknown'
    ORDER BY specialty
""")["specialty"].tolist()

c1, c2 = st.columns(2)
with c1:
    selected_company = st.selectbox("Company", companies)
with c2:
    selected_specialty = st.selectbox(
        "Specialty",
        ["All specialties"] + specialties,
    )


# ─── Aggregate stats (paid vs unpaid) ───────────────────────────────────────
spec_filter = "AND specialty = %s" if selected_specialty != "All specialties" else ""
params = (
    (selected_company, selected_specialty)
    if selected_specialty != "All specialties"
    else (selected_company,)
)

summary_df = run_query(
    f"""
    SELECT
        CASE WHEN total_payment_usd > 0
            THEN 'Received payments' ELSE 'No payments'
        END AS group_label,
        COUNT(*) AS n_physicians,
        ROUND(AVG(company_claim_count)::numeric, 1) AS avg_claims,
        ROUND(
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY company_claim_count)::numeric,
            1
        ) AS median_claims,
        ROUND(SUM(company_claim_count)::numeric, 0) AS total_claims
    FROM raw_mart.fact_payment_prescribing
    WHERE company_name = %s
        AND company_claim_count > 0
        {spec_filter}
    GROUP BY group_label
    """,
    params=params,
)

if summary_df.empty or len(summary_df) < 2:
    st.warning(
        "Not enough data to compare paid vs. unpaid groups for this "
        "company/specialty combination. Try widening the filters."
    )
    st.stop()

# Compute lift
try:
    avg_paid = summary_df.loc[
        summary_df["group_label"] == "Received payments", "avg_claims"
    ].iloc[0]
    avg_unpaid = summary_df.loc[
        summary_df["group_label"] == "No payments", "avg_claims"
    ].iloc[0]
    lift = round(float(avg_paid) / float(avg_unpaid), 2) if avg_unpaid else None
except (IndexError, ZeroDivisionError):
    lift = None


# ─── KPIs ────────────────────────────────────────────────────────────────────
section_heading(f"{selected_company} — {selected_specialty}")

c1, c2, c3, c4 = st.columns(4)

paid_row = summary_df[summary_df["group_label"] == "Received payments"].iloc[0]
unpaid_row = summary_df[summary_df["group_label"] == "No payments"].iloc[0]

c1.metric("Paid Physicians (n)", f"{paid_row['n_physicians']:,}")
c2.metric("Avg Claims — Paid", f"{paid_row['avg_claims']:,.0f}")
c3.metric("Avg Claims — Unpaid", f"{unpaid_row['avg_claims']:,.0f}")
c4.metric(
    "Lift Ratio",
    f"{lift:.2f}×" if lift else "N/A",
    delta="Paid prescribe more" if lift and lift > 1 else None,
    delta_color="off",
)


# ─── Bar comparison ──────────────────────────────────────────────────────────
fig = bar_chart(
    summary_df,
    x="group_label",
    y="avg_claims",
    title="Mean Prescribing Volume — Paid vs. Unpaid",
    color="group_label",
)
fig.update_xaxes(title=None)
fig.update_yaxes(title="Mean Claims per Physician")
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)

render_explain_button(
    chart_title=f"{selected_company} Paid vs Unpaid Comparison",
    business_question=(
        f"For {selected_company}'s drugs, how does prescribing volume "
        f"compare between physicians who received payments and those who "
        f"didn't, within the same specialty?"
    ),
    data=summary_df,
    extra_context=(
        f"Company: {selected_company}\n"
        f"Specialty: {selected_specialty}\n"
        f"Lift ratio: {lift}× (paid vs unpaid)"
    ),
    key_suffix=f"summary_{selected_company}_{selected_specialty}",
)


# ─── Scatter: $ vs Rx for paid physicians ───────────────────────────────────
section_heading("Payment Amount vs. Prescribing Volume")

scatter_df = run_query(
    f"""
    SELECT
        total_payment_usd,
        company_claim_count,
        specialty,
        state
    FROM raw_mart.fact_payment_prescribing
    WHERE company_name = %s
        AND total_payment_usd > 0
        AND company_claim_count > 0
        {spec_filter}
    """,
    params=params,
)

if not scatter_df.empty and len(scatter_df) >= 10:
    pearson = scatter_df["total_payment_usd"].corr(scatter_df["company_claim_count"])

    fig = scatter_chart(
        scatter_df,
        x="total_payment_usd",
        y="company_claim_count",
        title=(
            f"Payments vs. Claims — {selected_company} "
            f"(r = {pearson:.3f}, n = {len(scatter_df):,})"
        ),
        color="specialty" if selected_specialty == "All specialties" else None,
        hover_data=["state"],
        log_x=True,
        log_y=True,
    )
    fig.update_xaxes(title="Payments Received ($, log scale)")
    fig.update_yaxes(title="Part D Claims for Company's Drugs (log scale)")
    st.plotly_chart(fig, use_container_width=True)

    render_explain_button(
        chart_title=f"{selected_company} Payment-Prescribing Scatter",
        business_question=(
            f"Among physicians who receive payments from {selected_company}, "
            f"is there a relationship between payment size and prescribing "
            f"volume? What's the Pearson correlation telling us?"
        ),
        data=scatter_df.head(50),
        extra_context=f"Pearson r = {pearson:.3f}, n = {len(scatter_df)}",
        key_suffix=f"scatter_{selected_company}_{selected_specialty}",
    )
else:
    st.info("Insufficient paid-physician data for a scatter plot.")

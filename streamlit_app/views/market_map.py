"""
Market Opportunity Map
══════════════════════

Geographic territory-planning view. Identifies states where pharma
investment is over- or under-indexed relative to Part D prescribing
volume — i.e., where coverage gaps and saturated markets exist.

Backing analysis: dbt_project/analyses/04_geographic_market_analysis.sql
"""

from __future__ import annotations

import streamlit as st

from utils.charts import choropleth_us
from utils.db import run_query
from utils.llm import render_explain_button
from utils.styles import apply_global_styles, hero, page_guide, section_heading

apply_global_styles()

hero(
    title="Market Opportunity Map",
    subtitle=(
        "Where is pharma over- or under-invested vs. actual Part D "
        "prescribing volume? Spot growth markets and saturation risks."
    ),
)

page_guide(
    title="How to use this view",
    body=(
        "The map colors each state by its **investment ratio** — "
        "payment share of national pharma spend ÷ Rx share of national "
        "prescribing volume. **Red states** are over-invested "
        "(>1.25× — pharma spends more here than prescribing volume "
        "justifies). **Blue states** are under-invested (<0.75× — "
        "possible coverage gaps). **White states** are balanced. "
        "Filter by company to see one manufacturer's territory pattern. "
        "Useful for **rep deployment planning** and **KOL gap analysis**."
    ),
)

st.info(
    "**How to read this.** The *investment ratio* compares a state's share "
    "of national pharma payments to its share of national prescribing "
    "volume. **1.0 = perfectly proportional.** Above 1.25 = over-invested "
    "(spending more than prescribing volume justifies). Below 0.75 = "
    "under-invested (a possible coverage gap)."
)


# ─── Filter ──────────────────────────────────────────────────────────────────
section_heading("Filter")

all_companies = run_query(
    "SELECT DISTINCT company_name FROM raw_mart.fact_payments ORDER BY company_name"
)["company_name"].tolist()

selected = st.selectbox(
    "Company view",
    ["All companies"] + all_companies,
    label_visibility="collapsed",
)


# ─── Build the query ────────────────────────────────────────────────────────
if selected == "All companies":
    company_filter_payments = ""
    company_filter_rx = ""
    params: tuple = ()
else:
    company_filter_payments = "WHERE company_name = %s"
    company_filter_rx = "WHERE company_name = %s"
    params = (selected, selected)

market_df = run_query(
    f"""
    WITH state_payments AS (
        SELECT
            recipient_state AS state,
            SUM(payment_amount_usd) AS state_payment_usd,
            COUNT(DISTINCT physician_npi) AS paid_physicians
        FROM raw_mart.fact_payments
        {company_filter_payments}
            {("AND" if company_filter_payments else "WHERE")}
            recipient_state IS NOT NULL AND length(recipient_state) = 2
        GROUP BY recipient_state
    ),
    state_prescribing AS (
        SELECT
            dp.state,
            SUM(fr.total_claim_count) AS state_claim_count,
            SUM(fr.total_drug_cost_usd) AS state_drug_cost_usd
        FROM raw_mart.fact_prescriptions AS fr
        JOIN raw_mart.dim_physician AS dp USING (physician_npi)
        {company_filter_rx}
            {("AND" if company_filter_rx else "WHERE")}
            dp.state IS NOT NULL AND length(dp.state) = 2
        GROUP BY dp.state
    ),
    national AS (
        SELECT
            (SELECT SUM(state_payment_usd) FROM state_payments) AS us_pay,
            (SELECT SUM(state_claim_count) FROM state_prescribing) AS us_rx
    )
    SELECT
        COALESCE(p.state, r.state) AS state,
        COALESCE(p.state_payment_usd, 0) AS state_payment_usd,
        COALESCE(p.paid_physicians, 0) AS paid_physicians,
        COALESCE(r.state_claim_count, 0) AS state_claim_count,
        COALESCE(r.state_drug_cost_usd, 0) AS state_drug_cost_usd,

        ROUND(
            (COALESCE(p.state_payment_usd, 0)::numeric /
                NULLIF((SELECT us_pay FROM national), 0)) * 100,
            3
        ) AS payment_share_pct,

        ROUND(
            (COALESCE(r.state_claim_count, 0)::numeric /
                NULLIF((SELECT us_rx FROM national), 0)) * 100,
            3
        ) AS prescribing_share_pct,

        ROUND(
            (
                (COALESCE(p.state_payment_usd, 0)::numeric /
                    NULLIF((SELECT us_pay FROM national), 0))
                /
                NULLIF(
                    COALESCE(r.state_claim_count, 0)::numeric /
                        NULLIF((SELECT us_rx FROM national), 0),
                    0
                )
            )::numeric,
            3
        ) AS investment_ratio,

        CASE
            WHEN (
                COALESCE(p.state_payment_usd, 0)::numeric /
                    NULLIF((SELECT us_pay FROM national), 0)
            )
            / NULLIF(
                COALESCE(r.state_claim_count, 0)::numeric /
                    NULLIF((SELECT us_rx FROM national), 0),
                0
            ) > 1.25 THEN 'Over-invested'
            WHEN (
                COALESCE(p.state_payment_usd, 0)::numeric /
                    NULLIF((SELECT us_pay FROM national), 0)
            )
            / NULLIF(
                COALESCE(r.state_claim_count, 0)::numeric /
                    NULLIF((SELECT us_rx FROM national), 0),
                0
            ) < 0.75 THEN 'Under-invested'
            ELSE 'Balanced'
        END AS market_classification

    FROM state_payments AS p
    FULL OUTER JOIN state_prescribing AS r USING (state)
    ORDER BY state_claim_count DESC
    """,
    params=params,
)


# ─── Map ─────────────────────────────────────────────────────────────────────
section_heading(f"Investment Ratio by State — {selected}")

fig = choropleth_us(
    market_df,
    state_col="state",
    value_col="investment_ratio",
    title="Investment Ratio (payment share ÷ prescribing share)",
    color_scale="RdBu_r",
)
fig.update_coloraxes(cmid=1.0)
st.plotly_chart(fig, use_container_width=True)

render_explain_button(
    chart_title=f"{selected} Investment Ratio Map",
    business_question=(
        f"Across U.S. states, where is {selected} over- or under-invested "
        f"relative to Part D prescribing volume? What are the obvious "
        f"opportunities and risks?"
    ),
    data=market_df.head(20),
    key_suffix=f"map_{selected}",
)


# ─── Tables: top under-invested + top over-invested ─────────────────────────
section_heading("Strategic Implications")

col1, col2 = st.columns(2)

under = (
    market_df[market_df["market_classification"] == "Under-invested"]
    .sort_values("state_claim_count", ascending=False)
    .head(10)
)
over = (
    market_df[market_df["market_classification"] == "Over-invested"]
    .sort_values("state_claim_count", ascending=False)
    .head(10)
)

with col1:
    st.markdown("##### Under-Invested *(growth opportunities)*")
    display = under[
        ["state", "investment_ratio", "payment_share_pct", "prescribing_share_pct"]
    ].copy()
    display.columns = ["State", "Inv. Ratio", "Pay Share %", "Rx Share %"]
    st.dataframe(display, use_container_width=True, hide_index=True)

    render_explain_button(
        chart_title=f"{selected} Under-Invested Growth Markets",
        business_question=(
            "Which states are most under-invested by pharma relative to "
            "their prescribing volume, and what does that suggest for "
            "rep deployment or KOL development?"
        ),
        data=under,
        key_suffix=f"under_{selected}",
    )

with col2:
    st.markdown("##### Over-Invested *(saturation risk)*")
    display = over[
        ["state", "investment_ratio", "payment_share_pct", "prescribing_share_pct"]
    ].copy()
    display.columns = ["State", "Inv. Ratio", "Pay Share %", "Rx Share %"]
    st.dataframe(display, use_container_width=True, hide_index=True)

    render_explain_button(
        chart_title=f"{selected} Over-Invested Saturation Markets",
        business_question=(
            "Which states show signs of pharma over-investment (saturation), "
            "and what risks does that suggest?"
        ),
        data=over,
        key_suffix=f"over_{selected}",
    )

"""
KOL Finder
══════════

Lets a user pick a therapeutic class + filters and instantly see the top
Key Opinion Leaders by Part D prescribing volume, with their payment
relationships overlaid.

Backing analysis: dbt_project/analyses/01_kol_identification.sql
"""

from __future__ import annotations

import streamlit as st

from utils.charts import scatter_chart
from utils.db import run_query
from utils.llm import render_explain_button
from utils.styles import (
    apply_global_styles,
    hero,
    page_guide,
    section_heading,
    view_banner,
)

apply_global_styles()

view_banner("kol_finder", label="KOL Finder")

hero(
    title="KOL Finder",
    subtitle=(
        "Highest-volume Part D prescribers in any therapeutic class, with "
        "their pharma payment relationships overlaid."
    ),
)

page_guide(
    title="How to use this view",
    body=(
        "Pick a therapeutic class to surface the top prescribers in that "
        "category. These are the physicians pharma commercial teams refer "
        "to as **KOLs (Key Opinion Leaders)** — typically the top 1-5% of "
        "prescribers by volume. **What to look for**: which KOLs already "
        "have payment relationships (the **Paid** column), and whether "
        "any high-volume prescribers are *unpaid* — those are the "
        "highest-value uncultivated targets."
    ),
)


# ─── Filters ─────────────────────────────────────────────────────────────────
section_heading("Filters")

classes = run_query(
    "SELECT DISTINCT therapeutic_class FROM raw_mart.fact_prescriptions "
    "ORDER BY therapeutic_class"
)["therapeutic_class"].tolist()

states = run_query(
    "SELECT DISTINCT state FROM raw_mart.dim_physician "
    "WHERE state IS NOT NULL AND length(state) = 2 ORDER BY state"
)["state"].tolist()

c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
with c1:
    selected_class = st.selectbox("Therapeutic Class", classes, index=0)
with c2:
    selected_states = st.multiselect("State (optional)", states)
with c3:
    payment_filter = st.selectbox(
        "Payment Relationship",
        ["All physicians", "Paid only", "Unpaid only"],
    )
with c4:
    top_n = st.slider("Top N", 10, 200, 50, step=10)

# ─── Query ───────────────────────────────────────────────────────────────────
state_filter_sql = "AND dp.state = ANY(%s)" if selected_states else ""
payment_filter_sql = {
    "Paid only": "AND dp.received_pharma_payments = TRUE",
    "Unpaid only": "AND dp.received_pharma_payments = FALSE",
    "All physicians": "",
}[payment_filter]

query = f"""
    WITH class_volume AS (
        SELECT
            fp.physician_npi,
            SUM(fp.total_claim_count) AS class_claims,
            SUM(fp.total_drug_cost_usd) AS class_drug_cost
        FROM raw_mart.fact_prescriptions AS fp
        WHERE fp.therapeutic_class = %s
        GROUP BY fp.physician_npi
    ),
    payments_for_class AS (
        SELECT
            fpp.physician_npi,
            SUM(fpp.total_payment_usd) AS total_payment_usd
        FROM raw_mart.fact_payment_prescribing AS fpp
        WHERE fpp.company_name IN (
            SELECT DISTINCT company_name
            FROM raw_mart.fact_prescriptions
            WHERE therapeutic_class = %s
        )
        GROUP BY fpp.physician_npi
    )
    SELECT
        ROW_NUMBER() OVER (ORDER BY cv.class_claims DESC) AS rank,
        dp.physician_display_id,
        dp.specialty,
        dp.state,
        cv.class_claims,
        cv.class_drug_cost,
        COALESCE(p.total_payment_usd, 0) AS total_payments_usd,
        CASE WHEN dp.received_pharma_payments THEN '✓' ELSE '—' END AS paid
    FROM class_volume AS cv
    JOIN raw_mart.dim_physician AS dp USING (physician_npi)
    LEFT JOIN payments_for_class AS p ON cv.physician_npi = p.physician_npi
    -- KOLs are MD/DO specialists. Exclude mid-level providers
    -- (Nurse Practitioner, Physician Assistant) and physicians with
    -- no specialty on file — they're not the targets of pharma
    -- commercial engagement and skew the rankings.
    WHERE dp.specialty NOT IN (
            'Nurse Practitioner',
            'Physician Assistant',
            'Unknown'
        )
        {payment_filter_sql}
        {state_filter_sql}
    ORDER BY cv.class_claims DESC
    LIMIT %s
"""

if selected_states:
    params = (selected_class, selected_class, selected_states, top_n)
else:
    params = (selected_class, selected_class, top_n)

with st.spinner("Finding KOLs..."):
    kol_df = run_query(query, params=params)

if kol_df.empty:
    st.warning("No physicians found matching those filters.")
    st.stop()

# ─── Table ───────────────────────────────────────────────────────────────────
section_heading(f"Top {len(kol_df)} KOLs — {selected_class}")

display_df = kol_df.copy()
display_df["class_claims"] = display_df["class_claims"].apply(lambda x: f"{x:,}")
display_df["class_drug_cost"] = display_df["class_drug_cost"].apply(
    lambda x: f"${x:,.0f}"
)
display_df["total_payments_usd"] = display_df["total_payments_usd"].apply(
    lambda x: f"${x:,.0f}"
)
display_df.columns = [
    "Rank",
    "Physician",
    "Specialty",
    "State",
    "Class Claims",
    "Class Drug Cost",
    "Payments Received",
    "Paid",
]

st.dataframe(display_df, use_container_width=True, hide_index=True, height=420)

render_explain_button(
    chart_title=f"Top KOLs in {selected_class}",
    business_question=(
        f"Who are the top prescribers (KOLs) in {selected_class}, and "
        f"what does the data reveal about which ones have existing "
        f"pharma payment relationships?"
    ),
    data=kol_df.head(30),
    extra_context=(
        f"Therapeutic class: {selected_class}\n"
        f"State filter: {selected_states or 'All states'}\n"
        f"Payment filter: {payment_filter}"
    ),
    key_suffix=f"kol_{selected_class}",
)

# ─── Visual: KOL volume vs payments scatter ──────────────────────────────────
section_heading("Volume vs. Payments")
st.caption(
    "Each point is one of the top KOLs. Logarithmic axes — payments span "
    "many orders of magnitude."
)

scatter_data = kol_df[kol_df["total_payments_usd"] > 0].copy()
if not scatter_data.empty:
    fig = scatter_chart(
        scatter_data,
        x="total_payments_usd",
        y="class_claims",
        title=f"KOL Volume vs. Payments — {selected_class}",
        color="specialty",
        hover_data=["physician_display_id", "state"],
        log_x=True,
        log_y=True,
    )
    fig.update_xaxes(title="Total Payments Received ($, log scale)")
    fig.update_yaxes(title="Class Prescribing Claims (log scale)")
    st.plotly_chart(fig, use_container_width=True)

    render_explain_button(
        chart_title="KOL Volume vs Payments Scatter",
        business_question=(
            "Is there a visible relationship between how much a KOL is "
            "paid and how much they prescribe in their therapeutic class?"
        ),
        data=scatter_data.head(50),
        key_suffix=f"kol_scatter_{selected_class}",
    )
else:
    st.info(
        "All KOLs in this filtered view are unpaid — there's nothing to "
        "plot on the payment axis."
    )

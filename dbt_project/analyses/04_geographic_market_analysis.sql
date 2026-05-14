-- ═════════════════════════════════════════════════════════════════════════════
-- ANALYSIS 4 — Geographic Market Analysis
--
-- Business question:
--   "Which states are over- or under-invested by pharma relative to their
--    prescribing volume? Where are the under-served growth markets?"
--
-- This is the classic territory-planning exercise pharma commercial ops
-- teams do every year. If a state generates 8% of national prescriptions
-- for a drug but only 4% of payments, the company is "under-invested"
-- there — a sign the rep coverage model may need adjusting.
--
-- Methodology:
--   • Aggregate payment $ and prescription claim count by state
--   • Compute each state's share of national totals
--   • Calculate the "investment ratio" — payment share / prescribing share.
--     A ratio of 1.0 = perfectly proportional. > 1.0 = over-invested
--     relative to volume. < 1.0 = under-invested
--   • Bucket into Over / Balanced / Under for the Streamlit choropleth
-- ═════════════════════════════════════════════════════════════════════════════

with state_payments as (
    select
        recipient_state as state,
        sum(payment_amount_usd) as state_payment_usd,
        count(distinct physician_npi) as paid_physicians
    from {{ ref('fact_payments') }}
    where recipient_state is not null
        and length(recipient_state) = 2
    group by recipient_state
),

state_prescribing as (
    select
        dp.state,
        sum(fr.total_claim_count) as state_claim_count,
        sum(fr.total_drug_cost_usd) as state_drug_cost_usd,
        count(distinct fr.physician_npi) as prescribing_physicians
    from {{ ref('fact_prescriptions') }} as fr
    inner join {{ ref('dim_physician') }} as dp using (physician_npi)
    where dp.state is not null
        and length(dp.state) = 2
    group by dp.state
),

national_totals as (
    select
        sum(state_payment_usd) as us_payment_usd
    from state_payments
),

national_rx as (
    select
        sum(state_claim_count) as us_claim_count
    from state_prescribing
),

joined as (
    select
        coalesce(p.state, r.state) as state,
        coalesce(p.state_payment_usd, 0) as state_payment_usd,
        coalesce(p.paid_physicians, 0) as paid_physicians,
        coalesce(r.state_claim_count, 0) as state_claim_count,
        coalesce(r.state_drug_cost_usd, 0) as state_drug_cost_usd,
        coalesce(r.prescribing_physicians, 0) as prescribing_physicians
    from state_payments as p
    full outer join state_prescribing as r using (state)
),

with_shares as (
    select
        j.*,

        round(
            (j.state_payment_usd::numeric / nullif(n.us_payment_usd, 0)) * 100, 3
        ) as payment_share_pct,

        round(
            (j.state_claim_count::numeric / nullif(nr.us_claim_count, 0)) * 100, 3
        ) as prescribing_share_pct,

        round(
            ((j.state_payment_usd::numeric / nullif(n.us_payment_usd, 0))
            / nullif(j.state_claim_count::numeric / nullif(nr.us_claim_count, 0), 0))
            ::numeric, 3
        ) as investment_ratio
    from joined as j
    cross join national_totals as n
    cross join national_rx as nr
)

select
    state,
    state_payment_usd,
    paid_physicians,
    state_claim_count,
    state_drug_cost_usd,
    prescribing_physicians,
    payment_share_pct,
    prescribing_share_pct,
    investment_ratio,
    case
        when investment_ratio is null then 'Insufficient data'
        when investment_ratio > 1.25 then 'Over-invested'
        when investment_ratio < 0.75 then 'Under-invested'
        else 'Balanced'
    end as market_classification
from with_shares
order by state_claim_count desc

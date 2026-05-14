-- ═════════════════════════════════════════════════════════════════════════════
-- ANALYSIS 3 — Company Spend Efficiency
--
-- Business question:
--   "Which pharma companies get the best prescribing 'return' on their
--    physician investment?"
--
-- Caveat upfront: causal language ("return on investment") would be wrong
-- here because we cannot establish causation from observational data —
-- payment may follow prescribing rather than drive it. We use the term
-- *association ratio* throughout, and report it as a descriptive measure
-- only. This is how ZS Associates and similar firms frame these analyses
-- internally too.
--
-- Methodology:
--   • For each company, sum total payments and total prescribing
--     volume of their drugs by paid physicians
--   • Compute three ratios that capture different aspects of efficiency:
--       - Claims per $1K paid
--       - $ Rx volume per $1 paid
--       - Average payment size (concentrated vs. dispersed strategy)
-- ═════════════════════════════════════════════════════════════════════════════

with company_rollup as (
    select
        company_name,

        -- Spending
        sum(total_payment_usd) as total_spend_usd,
        sum(payment_count) as total_payment_count,
        count(distinct physician_npi)
            filter (where total_payment_usd > 0)
            as physicians_paid,

        -- Prescribing — by paid physicians only
        sum(company_claim_count) filter (where total_payment_usd > 0)
            as claims_from_paid,
        sum(company_drug_cost_usd) filter (where total_payment_usd > 0)
            as drug_revenue_from_paid_usd,

        -- Prescribing — by unpaid physicians (baseline)
        sum(company_claim_count) filter (where total_payment_usd = 0)
            as claims_from_unpaid,
        sum(company_drug_cost_usd) filter (where total_payment_usd = 0)
            as drug_revenue_from_unpaid_usd

    from {{ ref('fact_payment_prescribing') }}
    group by company_name
),

with_metrics as (
    select
        company_name,
        total_spend_usd,
        physicians_paid,
        claims_from_paid,
        drug_revenue_from_paid_usd,
        claims_from_unpaid,

        -- Avg spend per physician (concentration vs. dispersion)
        round((total_spend_usd / nullif(physicians_paid, 0))::numeric, 2)
            as avg_spend_per_paid_physician,

        -- Claims per $1K paid — descriptive efficiency
        round(
            (claims_from_paid / nullif(total_spend_usd / 1000.0, 0))::numeric, 2
        ) as claims_per_1k_spend,

        -- Drug $ associated per $ paid — descriptive return
        round(
            (drug_revenue_from_paid_usd / nullif(total_spend_usd, 0))::numeric, 2
        ) as rx_dollar_per_payment_dollar,

        -- Share of company's Rx volume coming from paid physicians
        round(
            (claims_from_paid::numeric
            / nullif(claims_from_paid + claims_from_unpaid, 0)) * 100, 2
        ) as paid_share_of_total_rx_pct

    from company_rollup
    where total_spend_usd > 0
)

select * from with_metrics
order by rx_dollar_per_payment_dollar desc nulls last

-- ═════════════════════════════════════════════════════════════════════════════
-- ANALYSIS 2 — Payment-to-Prescribing Correlation
--
-- Business question:
--   "Do physicians who receive payments from a pharma company prescribe
--    more of that company's drugs — controlling for specialty?"
--
-- This is the central research question of the project. It has been
-- published in JAMA (DeJong 2016), NEJM, and PLOS Medicine. The version
-- below replicates the standard methodology used in those papers.
--
-- Methodology:
--   • Split (physician × company) pairs into paid vs. unpaid
--   • Within each specialty, compute mean and median prescribing volume
--     for both groups
--   • Compute Pearson correlation between payment $ and prescribing
--     volume for the paid group (where both are non-zero)
--   • Compute the "lift ratio" — how much more do paid physicians
--     prescribe relative to unpaid peers in the same specialty
--
-- Why specialty-controlled:
--   A cardiologist prescribes more cardiac drugs than a dermatologist
--   does — irrespective of payments. Comparing across specialties would
--   confound the effect we're trying to measure.
-- ═════════════════════════════════════════════════════════════════════════════

with base as (
    select
        physician_npi,
        company_name,
        specialty,
        total_payment_usd,
        company_claim_count,
        case when total_payment_usd > 0 then 1 else 0 end as is_paid
    from {{ ref('fact_payment_prescribing') }}
    where specialty is not null
        and specialty != 'Unknown'
        and company_claim_count > 0          -- exclude paid-but-never-prescribed
),

specialty_stats as (
    select
        specialty,
        company_name,

        -- Paid group
        avg(company_claim_count) filter (where is_paid = 1)
            as avg_claims_paid,
        percentile_cont(0.5) within group (order by company_claim_count)
            filter (where is_paid = 1)
            as median_claims_paid,
        count(*) filter (where is_paid = 1) as n_paid,

        -- Unpaid group
        avg(company_claim_count) filter (where is_paid = 0)
            as avg_claims_unpaid,
        percentile_cont(0.5) within group (order by company_claim_count)
            filter (where is_paid = 0)
            as median_claims_unpaid,
        count(*) filter (where is_paid = 0) as n_unpaid,

        -- Correlation between $ and Rx (paid group only)
        corr(total_payment_usd, company_claim_count) filter (where is_paid = 1)
            as pearson_correlation
    from base
    group by specialty, company_name
    having count(*) filter (where is_paid = 1) >= 30      -- minimum sample size
        and count(*) filter (where is_paid = 0) >= 30
)

select
    specialty,
    company_name,
    n_paid,
    n_unpaid,
    round(avg_claims_paid::numeric, 1) as avg_claims_paid,
    round(median_claims_paid::numeric, 1) as median_claims_paid,
    round(avg_claims_unpaid::numeric, 1) as avg_claims_unpaid,
    round(median_claims_unpaid::numeric, 1) as median_claims_unpaid,

    -- Lift ratio — how much more do paid physicians prescribe?
    round((avg_claims_paid / nullif(avg_claims_unpaid, 0))::numeric, 2) as lift_ratio,

    round(pearson_correlation::numeric, 3) as pearson_correlation
from specialty_stats
order by lift_ratio desc nulls last

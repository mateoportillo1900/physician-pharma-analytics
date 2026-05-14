-- ═════════════════════════════════════════════════════════════════════════════
-- ANALYSIS 5 — Physician Loyalty Scoring
--
-- Business question:
--   "Which physicians appear to be 'loyal' to one manufacturer vs.
--    multi-source prescribers within a therapeutic class?"
--
-- In therapeutic classes with multiple competing drugs (e.g., GLP-1
-- agonists for diabetes: Ozempic from Novo Nordisk vs. Mounjaro from
-- Lilly), physicians often display a strong brand preference. Identifying
-- "loyalists" vs. "splitters" is the foundation of switch-targeting
-- marketing campaigns.
--
-- Methodology — Herfindahl-Hirschman Index (HHI):
--   • Within each (physician, therapeutic_class), compute each company's
--     share of that physician's class prescribing volume
--   • Sum the squared shares. Result ranges from 0 to 10,000
--     - 10,000 = single company prescribed exclusively (max loyalty)
--     -  1,000 = spread evenly across 10 companies
--   • Bucket into Loyalist / Strong Preference / Mixed / Highly Diversified
--
-- HHI is the standard concentration measure in antitrust economics and
-- is well-suited to this question.
-- ═════════════════════════════════════════════════════════════════════════════

with physician_class_company as (
    select
        physician_npi,
        therapeutic_class,
        company_name,
        sum(total_claim_count) as company_claims
    from {{ ref('fact_prescriptions') }}
    group by physician_npi, therapeutic_class, company_name
),

physician_class_total as (
    select
        physician_npi,
        therapeutic_class,
        sum(company_claims) as class_total_claims
    from physician_class_company
    group by physician_npi, therapeutic_class
),

shares as (
    select
        c.physician_npi,
        c.therapeutic_class,
        c.company_name,
        c.company_claims,
        t.class_total_claims,
        (c.company_claims::numeric / nullif(t.class_total_claims, 0)) as share
    from physician_class_company as c
    inner join physician_class_total as t using (physician_npi, therapeutic_class)
),

-- HHI = sum of squared shares × 10,000 (industry-standard scaling)
hhi as (
    select
        physician_npi,
        therapeutic_class,
        max(class_total_claims) as total_claims,
        count(distinct company_name) as distinct_companies,
        round(
            (sum(share * share) * 10000)::numeric, 0
        ) as hhi_score,
        -- Dominant company = company with highest share
        (array_agg(company_name order by share desc))[1] as dominant_company,
        max(share) as dominant_share
    from shares
    group by physician_npi, therapeutic_class
),

with_segment as (
    select
        h.*,
        case
            when hhi_score >= 9000 then 'Loyalist (single source)'
            when hhi_score >= 5000 then 'Strong preference'
            when hhi_score >= 2500 then 'Mixed prescriber'
            else 'Highly diversified'
        end as loyalty_segment,
        dp.physician_display_id,
        dp.specialty,
        dp.state
    from hhi as h
    left join {{ ref('dim_physician') }} as dp using (physician_npi)
    where total_claims >= 20    -- minimum activity threshold for stability
)

select
    physician_npi,
    physician_display_id,
    specialty,
    state,
    therapeutic_class,
    total_claims,
    distinct_companies,
    hhi_score,
    loyalty_segment,
    dominant_company,
    round((dominant_share * 100)::numeric, 1) as dominant_share_pct
from with_segment
order by therapeutic_class, hhi_score desc

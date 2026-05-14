-- ─────────────────────────────────────────────────────────────────────────────
-- int_physician_drug_prescribing
--
-- Joins Part D drug prescribing volume to the drug→company mapping so we
-- can express each prescription line as "Dr. X prescribed Y claims of
-- {company}'s drug." This is what makes the payment-to-prescribing
-- correlation possible — without the company attribution, the question
-- can't be answered.
-- ─────────────────────────────────────────────────────────────────────────────

with prescribing as (
    select * from {{ ref('stg_part_d_by_drug') }}
),

mapping as (
    select * from {{ ref('int_drug_company_mapping') }}
),

joined as (
    select
        p.physician_npi,
        p.drug_brand_name,
        m.drug_generic_name,
        m.company_name,
        m.therapeutic_class,
        p.total_claim_count,
        p.total_drug_cost_usd
    from prescribing as p
    inner join mapping as m
        on upper(trim(p.drug_brand_name)) = m.drug_brand_name_upper
),

-- Aggregate to (physician, company) — physicians often prescribe multiple
-- drugs from the same manufacturer
aggregated as (
    select
        physician_npi,
        company_name,
        sum(total_claim_count) as company_claim_count,
        sum(total_drug_cost_usd) as company_drug_cost_usd,
        count(distinct drug_brand_name) as distinct_drugs_prescribed,
        string_agg(distinct drug_brand_name, ', ' order by drug_brand_name)
            as drugs_prescribed_list
    from joined
    group by physician_npi, company_name
)

select * from aggregated

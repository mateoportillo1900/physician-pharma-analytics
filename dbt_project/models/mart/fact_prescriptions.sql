-- ─────────────────────────────────────────────────────────────────────────────
-- fact_prescriptions
--
-- Grain: one row per (physician, drug) combination for 2022.
-- Foreign keys: dim_physician, dim_drug, dim_company.
--
-- This is the granular prescribing fact table. For the
-- payment-to-prescribing correlation analysis we aggregate this up to
-- (physician × company) on the fly via fact_payment_prescribing.
-- ─────────────────────────────────────────────────────────────────────────────

with prescribing as (
    select * from {{ ref('stg_part_d_by_drug') }}
),

mapping as (
    select * from {{ ref('int_drug_company_mapping') }}
),

joined as (
    select
        {{ dbt_utils.generate_surrogate_key([
            'p.physician_npi', 'p.drug_brand_name', 'm.company_name'
        ]) }} as prescription_id,

        p.physician_npi,                     -- fk → dim_physician
        p.drug_brand_name,                   -- fk → dim_drug (partial)
        m.company_name,                      -- fk → dim_company
        m.therapeutic_class,

        p.total_claim_count,
        p.total_drug_cost_usd,

        case
            when p.total_claim_count is null
                or p.total_claim_count = 0 then null
            else round(p.total_drug_cost_usd / p.total_claim_count, 2)
        end as cost_per_claim_usd

    from prescribing as p
    inner join mapping as m
        on upper(trim(p.drug_brand_name)) = m.drug_brand_name_upper
)

select * from joined

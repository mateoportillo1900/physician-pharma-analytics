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

{{ config(
    post_hook=[
        "CREATE INDEX IF NOT EXISTS fact_rx_class_idx ON {{ this }} (therapeutic_class)",
        "CREATE INDEX IF NOT EXISTS fact_rx_npi_idx ON {{ this }} (physician_npi)"
    ]
) }}

with prescribing as (
    select * from {{ ref('stg_part_d_by_drug') }}
),

mapping as (
    select * from {{ ref('int_drug_company_mapping') }}
),

joined as (
    select
        p.physician_npi,                     -- fk → dim_physician
        p.drug_brand_name,                   -- fk → dim_drug (partial)
        m.company_name,                      -- fk → dim_company
        m.therapeutic_class,

        p.total_claim_count,
        p.total_drug_cost_usd

    from prescribing as p
    inner join mapping as m
        on upper(trim(p.drug_brand_name)) = m.drug_brand_name_upper
)

select * from joined

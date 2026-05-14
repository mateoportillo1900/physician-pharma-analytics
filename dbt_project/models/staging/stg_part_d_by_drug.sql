-- ─────────────────────────────────────────────────────────────────────────────
-- stg_part_d_by_drug
--
-- Drug-level prescribing detail per physician. Drives the
-- payment ↔ prescribing correlation analysis (Page 4 of the Streamlit app).
--
-- Loaded as a filtered subset (top ~30 drugs across cardiology, oncology,
-- immunology, endocrinology). See scripts/download_data.py for the drug list.
-- ─────────────────────────────────────────────────────────────────────────────

with source as (
    select * from {{ source('raw', 'part_d_by_drug') }}
),

cleaned as (
    select
        lpad(trim(cast(physician_npi as text)), 10, '0') as physician_npi,

        -- Brand and generic names: preserve casing, trim whitespace
        trim(drug_brand_name) as drug_brand_name,
        trim(drug_generic_name) as drug_generic_name,

        case
            when trim(cast(total_claim_count as text)) ~ '^[0-9]+$'
                then cast(total_claim_count as integer)
            else null
        end as total_claim_count,

        case
            when trim(cast(total_drug_cost_usd as text)) ~ '^[0-9.]+$'
                then cast(total_drug_cost_usd as numeric(14, 2))
            else null
        end as total_drug_cost_usd

    from source
    where physician_npi is not null
        and drug_brand_name is not null
)

select * from cleaned

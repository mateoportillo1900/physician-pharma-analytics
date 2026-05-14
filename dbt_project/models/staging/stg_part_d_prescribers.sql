-- ─────────────────────────────────────────────────────────────────────────────
-- stg_part_d_prescribers
--
-- Cleans the raw CMS Medicare Part D Prescribers by Provider file.
-- One row per physician NPI with their total 2022 Part D activity.
--
-- Notes on data quality:
--   • CMS suppresses cell counts where N < 11 for beneficiary privacy
--     ("redacted" in the source). We treat these as NULL, not zero
--   • Specialty taxonomy comes from CMS provider files; we normalize the
--     common values to a smaller canonical list for downstream analysis
-- ─────────────────────────────────────────────────────────────────────────────

with source as (
    select * from {{ source('raw', 'part_d_prescribers') }}
),

cleaned as (
    select
        -- 10-digit NPI with leading zeros preserved
        lpad(trim(cast(physician_npi as text)), 10, '0') as physician_npi,

        -- Provider name (preserve case for display)
        trim(provider_first_name) as provider_first_name,
        trim(provider_last_name) as provider_last_name,

        -- Specialty: collapse the long CMS taxonomy into the high-cardinality
        -- specialties that drive most of pharma's commercial spend
        case
            when specialty ilike '%cardiolog%' then 'Cardiology'
            when specialty ilike '%oncolog%' then 'Oncology'
            when specialty ilike '%hematolog%' then 'Hematology / Oncology'
            when specialty ilike '%endocrinolog%' then 'Endocrinology'
            when specialty ilike '%rheumatolog%' then 'Rheumatology'
            when specialty ilike '%gastroenterolog%' then 'Gastroenterology'
            when specialty ilike '%neurolog%' then 'Neurology'
            when specialty ilike '%psychiat%' then 'Psychiatry'
            when specialty ilike '%dermatolog%' then 'Dermatology'
            when specialty ilike '%pulmonolog%' then 'Pulmonology'
            when specialty ilike '%nephrolog%' then 'Nephrology'
            when specialty ilike '%urolog%' then 'Urology'
            when specialty ilike '%infectious disease%' then 'Infectious Disease'
            when specialty ilike '%family%practice%'
                or specialty ilike '%family%medicine%' then 'Family Medicine'
            when specialty ilike '%internal%medicine%' then 'Internal Medicine'
            when specialty ilike '%general%practice%' then 'General Practice'
            when specialty ilike '%nurse%practitioner%' then 'Nurse Practitioner'
            when specialty ilike '%physician%assistant%' then 'Physician Assistant'
            else coalesce(trim(specialty), 'Unknown')
        end as specialty,

        upper(trim(state)) as state,

        -- Convert "redacted" markers to NULL, cast remaining to numeric
        case
            when trim(cast(total_claim_count as text)) ~ '^[0-9]+$'
                then cast(total_claim_count as integer)
            else null
        end as total_claim_count,

        case
            when trim(cast(total_drug_cost_usd as text)) ~ '^[0-9.]+$'
                then cast(total_drug_cost_usd as numeric(14, 2))
            else null
        end as total_drug_cost_usd,

        case
            when trim(cast(total_beneficiary_count as text)) ~ '^[0-9]+$'
                then cast(total_beneficiary_count as integer)
            else null
        end as total_beneficiary_count

    from source
    where physician_npi is not null
)

select * from cleaned

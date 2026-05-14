-- ─────────────────────────────────────────────────────────────────────────────
-- dim_physician  (materialized as TABLE — see dbt_project.yml override)
--
-- Physician dimension. Each row is one provider (NPI), with a privacy-
-- preserving SURROGATE display ID (not the real name), specialty,
-- geography, and aggregate Part D activity.
--
-- Unified physician population:
--   Built from the UNION of (a) Medicare Part D prescribers and (b) Open
--   Payments recipients. Many physicians who receive pharma payments don't
--   appear in Part D (residents, hospitalists, non-Medicare prescribers).
--   Including both is the only way to satisfy referential integrity from
--   fact_payments back to this dimension.
--
-- Privacy by design (Option B):
--   Real provider first/last names are intentionally NOT propagated from
--   the staging layer. The public-facing demo displays only deterministic
--   surrogate IDs like "Physician #4837" derived from a hash of the NPI.
--
-- Performance note:
--   Modal state for payment-only physicians is computed in a single CTE
--   (modal_state_per_npi) — no correlated subqueries.
-- ─────────────────────────────────────────────────────────────────────────────

with prescribers as (
    select
        physician_npi,
        specialty,
        state,
        total_claim_count,
        total_drug_cost_usd,
        total_beneficiary_count,
        true as is_part_d_prescriber
    from {{ ref('stg_part_d_prescribers') }}
),

-- For NPIs that only appear in payments, the "modal" state is their most
-- frequent payment-recipient state — a reasonable proxy for practice
-- location. Computed once via aggregation + DISTINCT ON (no subquery
-- inside payment_only).
state_counts as (
    select
        physician_npi,
        recipient_state,
        count(*) as n
    from {{ ref('stg_open_payments') }}
    where recipient_state is not null
    group by physician_npi, recipient_state
),

modal_state_per_npi as (
    select distinct on (physician_npi)
        physician_npi,
        recipient_state as state
    from state_counts
    order by physician_npi, n desc
),

-- Payment recipients who are NOT also Part D prescribers
payment_only_npis as (
    select distinct op.physician_npi
    from {{ ref('stg_open_payments') }} as op
    left join prescribers as p
        on op.physician_npi = p.physician_npi
    where p.physician_npi is null
),

payment_only as (
    select
        po.physician_npi,
        'Unknown' as specialty,
        ms.state,
        null::integer as total_claim_count,
        null::numeric(14, 2) as total_drug_cost_usd,
        null::integer as total_beneficiary_count,
        false as is_part_d_prescriber
    from payment_only_npis as po
    left join modal_state_per_npi as ms using (physician_npi)
),

all_physicians as (
    select * from prescribers
    union all
    select * from payment_only
),

payment_recipients as (
    select distinct physician_npi
    from {{ ref('int_physician_payments_agg') }}
),

final as (
    select
        a.physician_npi,

        -- Surrogate display ID — deterministic 4-digit hash of NPI.
        -- Same NPI always maps to same display ID (consistent UX across
        -- pages) but cannot be reversed to a real name.
        'Physician #' || lpad(
            (
                ('x' || substring(md5(a.physician_npi), 1, 4))::bit(16)::int
            )::text,
            4, '0'
        ) as physician_display_id,

        a.specialty,
        a.state,

        a.total_claim_count,
        a.total_drug_cost_usd,
        a.total_beneficiary_count,

        case
            when a.total_claim_count is null then null
            when a.total_claim_count = 0 then 0
            else round(a.total_drug_cost_usd / a.total_claim_count, 2)
        end as avg_cost_per_claim_usd,

        a.is_part_d_prescriber,

        case
            when r.physician_npi is not null then true
            else false
        end as received_pharma_payments

    from all_physicians as a
    left join payment_recipients as r
        on a.physician_npi = r.physician_npi
)

select * from final

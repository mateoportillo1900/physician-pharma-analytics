-- ─────────────────────────────────────────────────────────────────────────────
-- fact_payment_prescribing
--
-- The headline analytical fact table. One row per (physician × company),
-- with both the dollar value of the company's payments to that physician
-- AND the physician's Part D prescribing volume for that company's drugs.
--
-- This is what makes the central analytical question answerable:
--   "Do physicians who receive payments from a company prescribe more
--    of that company's drugs?"
--
-- Includes both sides of the join — physicians who received payments
-- but didn't prescribe (e.g., research only), and physicians who
-- prescribed but received no payments (e.g., generic prescribers).
-- ─────────────────────────────────────────────────────────────────────────────

with payments as (
    select * from {{ ref('int_physician_payments_agg') }}
),

prescribing as (
    select * from {{ ref('int_physician_drug_prescribing') }}
),

physicians as (
    select * from {{ ref('dim_physician') }}
),

-- FULL OUTER JOIN to keep both populations: those who got paid but
-- didn't prescribe, AND those who prescribed but got nothing.
-- Dropped drugs_prescribed_list (text aggregation, was the heaviest
-- column) so we can materialize this as a table without busting
-- Neon's storage cap. Drug-level prescribing detail is still
-- available via fact_prescriptions.
joined as (
    select
        coalesce(pay.physician_npi, rx.physician_npi) as physician_npi,
        coalesce(pay.company_name, rx.company_name) as company_name,

        coalesce(pay.total_payment_usd, 0) as total_payment_usd,
        coalesce(pay.payment_count, 0) as payment_count,
        coalesce(pay.max_single_payment_usd, 0) as max_single_payment_usd,

        coalesce(rx.company_claim_count, 0) as company_claim_count,
        coalesce(rx.company_drug_cost_usd, 0) as company_drug_cost_usd,
        coalesce(rx.distinct_drugs_prescribed, 0) as distinct_drugs_prescribed,

        case
            when pay.total_payment_usd is not null
                and rx.company_claim_count is not null then 'paid_and_prescribed'
            when pay.total_payment_usd is not null then 'paid_no_rx'
            when rx.company_claim_count is not null then 'rx_no_payment'
            else 'neither'
        end as relationship_type

    from payments as pay
    full outer join prescribing as rx
        on pay.physician_npi = rx.physician_npi
        and pay.company_name = rx.company_name
),

-- Add physician attributes for downstream slicing
with_specialty as (
    select
        j.*,
        p.specialty,
        p.state
    from joined as j
    left join physicians as p
        on j.physician_npi = p.physician_npi
)

select * from with_specialty

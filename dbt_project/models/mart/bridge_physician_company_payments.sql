{{ config(
    post_hook=[
        "CREATE INDEX IF NOT EXISTS bridge_pay_company_idx ON {{ this }} (company_name)"
    ]
) }}

-- ─────────────────────────────────────────────────────────────────────────────
-- bridge_physician_company_payments
--
-- Thin pass-through of int_physician_payments_agg into the mart schema so
-- Streamlit doesn't need to reach into raw_intermediate.
--
-- Why this exists separately from fact_payment_prescribing:
--   fact_payment_prescribing FULL-OUTER-joins payments with prescribing.
--   On Neon's free-tier compute, materializing that join times out at
--   ~10 minutes, and querying it as a view takes ~6 minutes per page
--   load. For lookups that only need the payment side (the KOL Finder
--   "payments_for_class" CTE), going through the join is unnecessary.
--
-- This view trims to just (physician × company × total payments) — 30x
-- faster for the use cases that don't need prescribing data.
-- ─────────────────────────────────────────────────────────────────────────────

select
    physician_npi,
    company_name,
    total_payment_usd,
    payment_count,
    max_single_payment_usd
from {{ ref('int_physician_payments_agg') }}

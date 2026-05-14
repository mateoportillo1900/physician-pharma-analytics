-- ─────────────────────────────────────────────────────────────────────────────
-- fact_payments
--
-- Grain: one row per individual payment transaction.
-- Foreign keys: dim_physician (via physician_npi), dim_company (via company_name).
-- ─────────────────────────────────────────────────────────────────────────────

with payments as (
    select * from {{ ref('stg_open_payments') }}
)

select
    payment_id,                              -- pk
    physician_npi,                           -- fk → dim_physician
    company_name,                            -- fk → dim_company
    payment_date,
    payment_amount_usd,
    payment_category,
    recipient_state,

    -- Date attributes for time-series analysis
    extract(year from payment_date)::int as payment_year,
    extract(quarter from payment_date)::int as payment_quarter,
    extract(month from payment_date)::int as payment_month,

    -- Payment size buckets (for the Streamlit histogram)
    case
        when payment_amount_usd < 100 then '< $100'
        when payment_amount_usd < 1000 then '$100 – $1K'
        when payment_amount_usd < 10000 then '$1K – $10K'
        when payment_amount_usd < 100000 then '$10K – $100K'
        else '> $100K'
    end as payment_size_bucket

from payments

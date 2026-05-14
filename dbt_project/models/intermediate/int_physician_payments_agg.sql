-- ─────────────────────────────────────────────────────────────────────────────
-- int_physician_payments_agg
--
-- One row per (physician, company) pair, with the year's total payments
-- aggregated and broken down by payment category.
--
-- This is the join key for the payment-to-prescribing analysis: for a given
-- physician and a given company, how much did the company pay them?
-- ─────────────────────────────────────────────────────────────────────────────

with payments as (
    select * from {{ ref('stg_open_payments') }}
),

aggregated as (
    select
        physician_npi,
        company_name,

        -- Total spend
        sum(payment_amount_usd) as total_payment_usd,
        count(*) as payment_count,

        -- Spend by category (pivoted via FILTER, which Postgres supports)
        sum(payment_amount_usd) filter (where payment_category = 'Food and Beverage')
            as spend_food_beverage_usd,
        sum(payment_amount_usd) filter (where payment_category = 'Consulting Fee')
            as spend_consulting_usd,
        sum(payment_amount_usd) filter (where payment_category = 'Speaking Fee')
            as spend_speaking_usd,
        sum(payment_amount_usd) filter (where payment_category = 'Travel and Lodging')
            as spend_travel_usd,
        sum(payment_amount_usd) filter (where payment_category = 'Education')
            as spend_education_usd,
        sum(payment_amount_usd) filter (where payment_category = 'Honoraria')
            as spend_honoraria_usd,
        sum(payment_amount_usd) filter (where payment_category = 'Royalty / License')
            as spend_royalty_usd,
        sum(payment_amount_usd) filter (where payment_category in (
                'Gift', 'Entertainment', 'Grant', 'Charitable Contribution',
                'Device Loan', 'Acquisition', 'Debt Forgiveness', 'Other'
            )) as spend_other_usd,

        -- Largest single payment received from this company
        max(payment_amount_usd) as max_single_payment_usd,

        -- Date range of activity
        min(payment_date) as first_payment_date,
        max(payment_date) as last_payment_date

    from payments
    group by physician_npi, company_name
)

select * from aggregated

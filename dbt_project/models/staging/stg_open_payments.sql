-- ─────────────────────────────────────────────────────────────────────────────
-- stg_open_payments
--
-- Cleans the raw CMS Open Payments General Payments table:
--   • Casts payment amount to numeric
--   • Standardizes NPI format (10-digit text, leading zeros preserved)
--   • Normalizes company names (trim, uppercase) and consolidates well-known
--     parent / subsidiary variants into a single canonical name
--   • Drops payments < $1 (rounding noise) and rows with no NPI
--   • Adds a surrogate payment_id for joins
-- ─────────────────────────────────────────────────────────────────────────────

with source as (
    select * from {{ source('raw', 'open_payments') }}
),

cleaned as (
    select
        -- Surrogate key for this payment record
        {{ dbt_utils.generate_surrogate_key([
            'physician_npi',
            'company_name',
            'payment_date',
            'payment_amount_usd',
            'payment_nature'
        ]) }} as payment_id,

        -- Pad NPI to canonical 10-digit string (CMS exports sometimes drop leading 0s)
        lpad(trim(cast(physician_npi as text)), 10, '0') as physician_npi,

        -- Canonicalize company name: trim + uppercase + collapse known aliases
        case
            when upper(trim(company_name)) like 'PFIZER%' then 'PFIZER'
            when upper(trim(company_name)) like 'ABBVIE%' then 'ABBVIE'
            when upper(trim(company_name)) like 'JOHNSON & JOHNSON%'
                or upper(trim(company_name)) like 'JANSSEN%' then 'JOHNSON & JOHNSON'
            when upper(trim(company_name)) like 'NOVO NORDISK%' then 'NOVO NORDISK'
            when upper(trim(company_name)) like 'MERCK%' then 'MERCK'
            when upper(trim(company_name)) like 'BRISTOL%MYERS%'
                or upper(trim(company_name)) like 'CELGENE%'  -- BMS oncology subsidiary
                then 'BRISTOL-MYERS SQUIBB'
            when upper(trim(company_name)) like 'ELI LILLY%'
                or upper(trim(company_name)) like 'LILLY%' then 'ELI LILLY'
            when upper(trim(company_name)) like 'ASTRAZENECA%' then 'ASTRAZENECA'
            when upper(trim(company_name)) like 'NOVARTIS%' then 'NOVARTIS'
            when upper(trim(company_name)) like 'SANOFI%' then 'SANOFI'
            when upper(trim(company_name)) like 'GSK%'
                or upper(trim(company_name)) like 'GLAXO%' then 'GSK'
            when upper(trim(company_name)) like 'GILEAD%' then 'GILEAD'
            when upper(trim(company_name)) like 'AMGEN%' then 'AMGEN'
            when upper(trim(company_name)) like 'BAYER%' then 'BAYER'
            when upper(trim(company_name)) like 'BOEHRINGER%' then 'BOEHRINGER INGELHEIM'
            when upper(trim(company_name)) like 'TAKEDA%' then 'TAKEDA'
            when upper(trim(company_name)) like 'REGENERON%' then 'REGENERON'
            when upper(trim(company_name)) like 'BIOGEN%' then 'BIOGEN'
            when upper(trim(company_name)) like 'VERTEX%' then 'VERTEX'
            when upper(trim(company_name)) like 'MODERNA%' then 'MODERNA'
            else upper(trim(company_name))
        end as company_name,

        cast(payment_amount_usd as numeric(14, 2)) as payment_amount_usd,
        cast(payment_date as date) as payment_date,

        -- Standardize payment-type categories.
        -- Order matters: more-specific patterns must precede less-specific
        -- ones, because CMS's longest nature description literally contains
        -- the word "consulting" ("Compensation for services other than
        -- consulting, including serving as faculty or as a speaker...") and
        -- would be miscategorized if we tested a generic "%consulting%"
        -- rule first.
        case
            when payment_nature ilike '%food and beverage%'
                then 'Food and Beverage'
            when payment_nature ilike '%travel and lodging%'
                then 'Travel and Lodging'
            when payment_nature ilike '%compensation%services other than consulting%'
                or payment_nature ilike '%compensation%speaker%'
                or payment_nature ilike '%compensation%faculty%'
                then 'Speaking Fee'
            when payment_nature ilike '%consulting fee%'
                then 'Consulting Fee'
            when payment_nature ilike '%education%' then 'Education'
            when payment_nature ilike '%honoraria%' then 'Honoraria'
            when payment_nature ilike '%royalty%' then 'Royalty / License'
            when payment_nature ilike '%grant%' then 'Grant'
            when payment_nature ilike '%charitable%' then 'Charitable Contribution'
            when payment_nature ilike '%medical supply%'
                or payment_nature ilike '%device loan%'
                then 'Device Loan'
            when payment_nature ilike '%acquisition%' then 'Acquisition'
            when payment_nature ilike '%debt forgiveness%' then 'Debt Forgiveness'
            when payment_nature ilike '%gift%' then 'Gift'
            when payment_nature ilike '%entertainment%' then 'Entertainment'
            else 'Other'
        end as payment_category,

        upper(trim(recipient_state)) as recipient_state

    from source
    where physician_npi is not null
        and payment_amount_usd >= 1.00       -- drop rounding noise
        and company_name is not null
)

select * from cleaned

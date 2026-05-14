-- ─────────────────────────────────────────────────────────────────────────────
-- dim_company
--
-- Pharma manufacturer dimension. Built from the union of companies that
-- appear in either Open Payments (paying physicians) or our drug mapping
-- (selling drugs Medicare reimburses).
-- ─────────────────────────────────────────────────────────────────────────────

with payment_companies as (
    select distinct company_name
    from {{ ref('stg_open_payments') }}
),

drug_companies as (
    select distinct company_name
    from {{ ref('int_drug_company_mapping') }}
),

unioned as (
    select company_name from payment_companies
    union
    select company_name from drug_companies
),

drug_portfolio as (
    select
        company_name,
        count(distinct drug_brand_name) as drugs_in_portfolio,
        string_agg(distinct therapeutic_class, ', ' order by therapeutic_class)
            as therapeutic_areas
    from {{ ref('int_drug_company_mapping') }}
    group by company_name
)

select
    u.company_name,
    coalesce(d.drugs_in_portfolio, 0) as drugs_in_portfolio,
    coalesce(d.therapeutic_areas, 'N/A') as therapeutic_areas
from unioned as u
left join drug_portfolio as d using (company_name)

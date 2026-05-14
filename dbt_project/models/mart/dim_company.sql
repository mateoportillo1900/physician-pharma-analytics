-- ─────────────────────────────────────────────────────────────────────────────
-- dim_company
--
-- Pharma manufacturer dimension. Built from the union of companies that
-- appear in either Open Payments (paying physicians) or our drug mapping
-- (selling drugs Medicare reimburses).
--
-- `company_name` is the canonical join key (uppercase). `company_display_name`
-- is the human-readable, branded-case version that the UI surfaces in
-- dropdowns and tables ("AbbVie" not "ABBVIE"). The split keeps SQL joins
-- simple while making the app look like a real product, not a database dump.
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

    -- Branded-case display name. Pharma companies have specific
    -- capitalization (AbbVie, AstraZeneca, GSK), so a generic initcap()
    -- wouldn't get them right. Manual mapping covers our top 10.
    case u.company_name
        when 'PFIZER'              then 'Pfizer'
        when 'ABBVIE'              then 'AbbVie'
        when 'JOHNSON & JOHNSON'   then 'Johnson & Johnson'
        when 'MERCK'               then 'Merck'
        when 'BRISTOL-MYERS SQUIBB' then 'Bristol Myers Squibb'
        when 'ELI LILLY'           then 'Eli Lilly'
        when 'NOVO NORDISK'        then 'Novo Nordisk'
        when 'ASTRAZENECA'         then 'AstraZeneca'
        when 'NOVARTIS'            then 'Novartis'
        when 'SANOFI'              then 'Sanofi'
        when 'GSK'                 then 'GSK'
        when 'GILEAD'              then 'Gilead'
        when 'AMGEN'               then 'Amgen'
        when 'BAYER'               then 'Bayer'
        when 'BOEHRINGER INGELHEIM' then 'Boehringer Ingelheim'
        when 'TAKEDA'              then 'Takeda'
        when 'REGENERON'           then 'Regeneron'
        when 'BIOGEN'              then 'Biogen'
        when 'VERTEX'              then 'Vertex'
        when 'MODERNA'             then 'Moderna'
        -- Fallback for anything not in the manual list: initcap each word
        else initcap(lower(u.company_name))
    end as company_display_name,

    coalesce(d.drugs_in_portfolio, 0) as drugs_in_portfolio,
    coalesce(d.therapeutic_areas, 'N/A') as therapeutic_areas
from unioned as u
left join drug_portfolio as d using (company_name)

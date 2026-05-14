-- ─────────────────────────────────────────────────────────────────────────────
-- int_drug_company_mapping
--
-- Maps brand-name drugs to their manufacturer. CMS Part D data has drug
-- brand/generic names; Open Payments has company names. Joining them
-- requires this lookup — which is itself a domain-knowledge artifact
-- (drug → company is publicly known but not in either CMS file).
--
-- The mapping table is curated in scripts/seeds/drug_company_seed.csv and
-- loaded via `dbt seed`. We expose it here through ref() so downstream
-- models stay agnostic to the seed mechanism.
--
-- This is the kind of work an analytics engineer at ZS Associates or
-- Komodo Health does every week.
-- ─────────────────────────────────────────────────────────────────────────────

with seed as (
    select * from {{ ref('drug_company_seed') }}
),

normalized as (
    select
        upper(trim(drug_brand_name)) as drug_brand_name_upper,
        trim(drug_brand_name) as drug_brand_name,
        trim(drug_generic_name) as drug_generic_name,
        upper(trim(manufacturer_canonical)) as company_name,
        therapeutic_class
    from seed
)

select * from normalized

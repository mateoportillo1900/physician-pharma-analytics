-- ─────────────────────────────────────────────────────────────────────────────
-- dim_drug
--
-- Drug dimension. One row per (brand, manufacturer) combination, with the
-- generic name and therapeutic class. Note that the same brand name can
-- legitimately appear under two manufacturers (e.g., Xarelto is co-marketed
-- by Johnson & Johnson and Bayer), which is preserved here.
-- ─────────────────────────────────────────────────────────────────────────────

with mapping as (
    select * from {{ ref('int_drug_company_mapping') }}
)

select
    {{ dbt_utils.generate_surrogate_key([
        'drug_brand_name', 'company_name'
    ]) }} as drug_key,

    drug_brand_name,
    drug_generic_name,
    company_name,
    therapeutic_class

from mapping

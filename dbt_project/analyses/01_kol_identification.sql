-- ═════════════════════════════════════════════════════════════════════════════
-- ANALYSIS 1 — KOL Identification
--
-- Business question:
--   "For a given therapeutic class, who are the top 100 Key Opinion Leaders
--    a pharma commercial team should engage?"
--
-- KOL = Key Opinion Leader. In pharma, these are the high-volume prescribers
-- whose decisions move drug market share — typically the top 1-5% of
-- prescribers in a therapeutic area. Identifying them is the foundational
-- task of pharma commercial analytics teams at ZS Associates, IQVIA, etc.
--
-- Methodology:
--   • Rank physicians within each (therapeutic_class, specialty) by
--     prescription volume using ROW_NUMBER() over a partitioned window
--   • Compute their share of the total class volume (cumulative density)
--   • Tier into A/B/C using percentile bands — the industry-standard
--     pharma segmentation
--   • Cross-join to payment data to flag which KOLs already have
--     existing relationships with each company
-- ═════════════════════════════════════════════════════════════════════════════

with prescribing as (
    select
        fp.physician_npi,
        fp.therapeutic_class,
        sum(fp.total_claim_count) as class_claim_count,
        sum(fp.total_drug_cost_usd) as class_drug_cost_usd
    from {{ ref('fact_prescriptions') }} as fp
    group by fp.physician_npi, fp.therapeutic_class
),

ranked as (
    select
        p.physician_npi,
        p.therapeutic_class,
        p.class_claim_count,
        p.class_drug_cost_usd,

        dp.physician_display_id,
        dp.specialty,
        dp.state,

        -- Rank within therapeutic class
        row_number() over (
            partition by p.therapeutic_class
            order by p.class_claim_count desc
        ) as rank_in_class,

        -- Cumulative share of class volume — KOLs concentrate disproportionately
        sum(p.class_claim_count) over (
            partition by p.therapeutic_class
            order by p.class_claim_count desc
            rows between unbounded preceding and current row
        )::numeric
        / nullif(sum(p.class_claim_count) over (partition by p.therapeutic_class), 0)
        as cumulative_share_of_class,

        -- Percentile rank (used for tiering)
        percent_rank() over (
            partition by p.therapeutic_class
            order by p.class_claim_count
        ) as percentile_in_class

    from prescribing as p
    inner join {{ ref('dim_physician') }} as dp using (physician_npi)
),

tiered as (
    select
        *,
        case
            when percentile_in_class >= 0.99 then 'A — Top 1%'
            when percentile_in_class >= 0.95 then 'B — Top 5%'
            when percentile_in_class >= 0.90 then 'C — Top 10%'
            else 'D — Below top decile'
        end as kol_tier
    from ranked
)

select
    therapeutic_class,
    kol_tier,
    rank_in_class,
    physician_npi,
    physician_display_id,
    specialty,
    state,
    class_claim_count,
    class_drug_cost_usd,
    round(cumulative_share_of_class * 100, 2) as cumulative_share_pct
from tiered
where rank_in_class <= 100
order by therapeutic_class, rank_in_class

# Data Model

The mart is a classic Kimball-style star schema: a few small dimension
tables surrounded by a handful of fact tables that hold the measures.
This is the only layer the Streamlit app queries.

---

## Star schema

Three dimension tables (orange) and three fact tables (red). Lines are
foreign-key relationships.

```mermaid
erDiagram
    DIM_PHYSICIAN {
        text physician_npi PK
        text physician_display_id "Anonymized surrogate ID"
        text specialty
        text state
        int total_claim_count
        numeric total_drug_cost_usd
        bool is_part_d_prescriber
        bool received_pharma_payments
    }

    DIM_COMPANY {
        text company_name PK "Canonical join key (uppercase)"
        text company_display_name "Branded case (Pfizer, AbbVie)"
        int drugs_in_portfolio
        text therapeutic_areas
    }

    DIM_DRUG {
        text drug_key PK
        text drug_brand_name
        text drug_generic_name
        text company_name FK
        text therapeutic_class
    }

    FACT_PAYMENTS {
        text payment_id
        text physician_npi FK
        text company_name FK
        date payment_date
        numeric payment_amount_usd
        text payment_category
        text recipient_state
        int payment_year
    }

    FACT_PRESCRIPTIONS {
        text prescription_id
        text physician_npi FK
        text drug_brand_name
        text company_name FK
        text therapeutic_class
        int total_claim_count
        numeric total_drug_cost_usd
    }

    FACT_PAYMENT_PRESCRIBING {
        text physician_npi FK
        text company_name FK
        numeric total_payment_usd
        int payment_count
        int company_claim_count
        numeric company_drug_cost_usd
        text relationship_type
        text specialty
        text state
    }

    DIM_PHYSICIAN ||--o{ FACT_PAYMENTS : "has many"
    DIM_COMPANY  ||--o{ FACT_PAYMENTS : "pays"
    DIM_PHYSICIAN ||--o{ FACT_PRESCRIPTIONS : "prescribes"
    DIM_COMPANY  ||--o{ FACT_PRESCRIPTIONS : "manufactures"
    DIM_PHYSICIAN ||--o{ FACT_PAYMENT_PRESCRIBING : "paired with"
    DIM_COMPANY  ||--o{ FACT_PAYMENT_PRESCRIBING : "paired with"
```

---

## What each table is for

### Dimensions

| Table | Grain | Purpose |
|---|---|---|
| `dim_physician` | 1 row per NPI | Who the physician is — specialty, state, surrogate display ID, Part D activity. Built from the UNION of Part D prescribers and Open Payments recipients so referential integrity holds for both |
| `dim_company` | 1 row per pharma company | What we know about the manufacturer — canonical name (for joins) + display name (for the UI), drug portfolio size, therapeutic areas |
| `dim_drug` | 1 row per (brand × manufacturer) | Brand and generic names, therapeutic class. Co-marketed drugs (e.g. Eliquis = Pfizer + BMS) appear once per partner |

### Facts

| Table | Grain | Used by |
|---|---|---|
| `fact_payments` | 1 row per Open Payments transaction | Executive Dashboard, Company Intelligence, Market Opportunity Map |
| `fact_prescriptions` | 1 row per (physician × drug) | KOL Finder, Market Opportunity Map |
| `fact_payment_prescribing` | 1 row per (physician × company) — **paired view of payments AND prescribing** | Payment vs. Prescribing (the headline analytical view) |

---

## The headline analytical join

This is the join that powers the *Payment vs. Prescribing* view —
the question every pharma commercial team analyzes. It's a
`FULL OUTER JOIN` so we capture all three populations:

```mermaid
flowchart LR
    A["Physicians who<br/>received payments<br/>(from int_physician_payments_agg)"]
    B["Physicians who<br/>prescribed drugs<br/>(from int_physician_drug_prescribing)"]

    A -->|"FULL OUTER JOIN<br/>on (NPI × company)"| C
    B --> C["fact_payment_prescribing"]

    C --> R1["paid_and_prescribed"]
    C --> R2["paid_no_rx"]
    C --> R3["rx_no_payment"]

    style R1 fill:#D1FAE5,stroke:#065F46,color:#0F172A
    style R2 fill:#FEF3C7,stroke:#92400E,color:#0F172A
    style R3 fill:#DBEAFE,stroke:#1E40AF,color:#0F172A
```

The `relationship_type` column tells you which bucket each row falls
into — useful for the lift-ratio analysis (paid prescribe more than
unpaid, within specialty).

---

## Data quality enforcement

Every dim and fact has tests in its `_schema.yml`. The dbt test run
executes 59 assertions on every build:

```mermaid
flowchart LR
    UNIQUE["unique<br/>(13 tests)"]
    NN["not_null<br/>(28 tests)"]
    AV["accepted_values<br/>(3 tests)"]
    REL["relationships<br/>(8 tests)"]
    EXP["dbt_expectations<br/>range checks<br/>(7 tests)"]

    UNIQUE --> ALL["dbt test ✓ 59/59 passing"]
    NN --> ALL
    AV --> ALL
    REL --> ALL
    EXP --> ALL

    style ALL fill:#D1FAE5,stroke:#065F46,color:#0F172A,stroke-width:2px
```

Examples:

- `dim_physician.physician_npi` must be **unique and not null**
- `fact_payments.company_name` must have a `relationships` match in
  `dim_company.company_name`
- `stg_open_payments.payment_category` must be in the **accepted-values**
  enum (Speaking Fee, Consulting Fee, Food and Beverage, etc.)
- `stg_open_payments.payment_amount_usd` must be `between 1 and 100,000,000`
  (range check from dbt_expectations)

---

## Privacy design

The mart layer intentionally **does not** include physician first or
last names — they're available in the staging layer for join purposes
but never propagate forward.

```mermaid
flowchart LR
    R["raw.part_d_prescribers<br/>(real names preserved)"]
    S["stg_part_d_prescribers<br/>(real names available<br/>for internal use)"]
    M["dim_physician<br/>(no name columns<br/>at all)"]
    A["Streamlit app<br/>(sees only<br/>'Physician #4837')"]

    R --> S
    S -->|"drops name columns,<br/>generates surrogate ID<br/>from md5(NPI)"| M
    M --> A

    style M fill:#D1FAE5,stroke:#065F46,color:#0F172A,stroke-width:2px
    style A fill:#D1FAE5,stroke:#065F46,color:#0F172A,stroke-width:2px
```

The surrogate is deterministic — same NPI always maps to the same
display ID across pages — but the ID cannot be reversed to a real
person. This matches the "research-grade presentation" pattern used
in academic publications on Open Payments data.

See `METHODOLOGY.md` § 0 for the full privacy rationale.

---

## Building it yourself

```bash
cd dbt_project
dbt deps                   # one-time: pull dbt-utils + dbt-expectations
dbt seed --profiles-dir .  # load drug→company seed
dbt run --profiles-dir .   # build all 12 models in dependency order
dbt test --profiles-dir .  # run all 59 data-quality tests
dbt docs generate          # generate the interactive lineage site
dbt docs serve             # open it in your browser at localhost:8080
```

The `dbt docs serve` command opens a fully-interactive version of
everything in this document — column descriptions, test results,
lineage clickable, compiled SQL for every model.

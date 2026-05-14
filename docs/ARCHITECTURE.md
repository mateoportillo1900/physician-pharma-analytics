# Architecture

How the *Physician × Pharma Commercial Analytics* platform is put
together — read this if you want to understand the system before
diving into the code.

All diagrams below are Mermaid; GitHub renders them inline.

---

## 1. System overview

Five layers, each with a clearly bounded job. Anyone clicking around the
deployed Streamlit app touches every layer in a single request — but
the layers are independently testable.

```mermaid
flowchart TB
    subgraph SRC["1 · Data Sources"]
        OP["CMS Open Payments<br/>(General Payments, 2022)"]
        PD["CMS Medicare Part D PUF<br/>(2022)"]
    end

    subgraph STORAGE["2 · Storage  (Neon Postgres)"]
        RAW["raw schema<br/>open_payments<br/>part_d_prescribers<br/>part_d_by_drug"]
        STG["raw_staging<br/>(views)"]
        INT["raw_intermediate<br/>(views)"]
        MART["raw_mart<br/>(star schema:<br/>3 dims + 3 facts)"]
    end

    subgraph TRANSFORM["3 · Transformation  (dbt)"]
        SEED["dbt seed<br/>drug → company<br/>mapping"]
        STG_M["staging models"]
        INT_M["intermediate models"]
        MART_M["mart models"]
        TESTS["59 data tests<br/>(unique, not_null,<br/>accepted_values,<br/>relationships)"]
    end

    subgraph APP["4 · Application  (Streamlit)"]
        APPPY["app.py<br/>(st.navigation hub)"]
        V1["Executive Dashboard"]
        V2["KOL Finder"]
        V3["Company Intelligence"]
        V4["Payment vs. Prescribing"]
        V5["Market Opportunity Map"]
        V6["About this project"]
    end

    subgraph AI["5 · AI Augmentation"]
        BTN["Explain this chart"]
        GROQ["Groq · Llama 3.3 70B"]
    end

    OP -->|"scripts/<br/>download_data.py"| RAW
    PD -->|"scripts/<br/>load_data.py<br/>(filtered)"| RAW

    SEED -.->|"dbt run"| MART
    STG_M -.->|"dbt run"| STG
    INT_M -.->|"dbt run"| INT
    MART_M -.->|"dbt run"| MART

    RAW --> STG
    STG --> INT
    INT --> MART
    STG --> MART

    TESTS -.->|"dbt test"| MART

    MART --> APPPY
    APPPY --> V1
    APPPY --> V2
    APPPY --> V3
    APPPY --> V4
    APPPY --> V5
    APPPY --> V6

    V1 --> BTN
    V2 --> BTN
    V3 --> BTN
    V4 --> BTN
    V5 --> BTN

    BTN -->|"chart data +<br/>system prompt"| GROQ
    GROQ -->|"plain-English<br/>insight"| BTN
```

**Why this shape:** the **dbt mart** is the contract between the data
team (everything left of it) and the application team (everything right
of it). The Streamlit app does not know — and does not need to know —
that raw CMS CSVs ever existed.

---

## 2. Data pipeline (CSV → mart)

The same data flows top-to-bottom on every full rebuild. The mart is
the only layer the Streamlit app ever touches at query time.

```mermaid
flowchart LR
    A["CMS.gov<br/>CSV downloads<br/>(~5 GB)"]
    B["data/raw/<br/>(local disk,<br/>gitignored)"]
    C["raw schema<br/>(filtered:<br/>top 10 mfrs,<br/>≥ $50, top<br/>specialties,<br/>tracked drugs)"]
    D["raw_staging<br/>(views — clean,<br/>type-cast, canonicalize)"]
    E["raw_intermediate<br/>(views — business<br/>logic, joins)"]
    F["raw_mart<br/>(tables + views —<br/>star schema)"]
    G["Streamlit app"]

    A -->|"download_data.py"| B
    B -->|"load_data.py<br/>(stream + filter)"| C
    C -->|"dbt run"| D
    D -->|"dbt run"| E
    E -->|"dbt run"| F
    F -->|"SELECT"| G

    style A fill:#E0E7FF,stroke:#1E3A8A,color:#0F172A
    style B fill:#FEF3C7,stroke:#92400E,color:#0F172A
    style C fill:#DBEAFE,stroke:#1E40AF,color:#0F172A
    style D fill:#D1FAE5,stroke:#065F46,color:#0F172A
    style E fill:#D1FAE5,stroke:#065F46,color:#0F172A
    style F fill:#FCE7F3,stroke:#9F1239,color:#0F172A
    style G fill:#F3E8FF,stroke:#6D28D9,color:#0F172A
```

**Free-tier discipline:** the load script filters aggressively *before*
inserting into Neon (top 10 manufacturers + payments ≥ $50 +
top-prescribing specialties only) — that's how we stay under the 512 MB
storage cap while preserving the headline analyses.

---

## 3. dbt model lineage

Twelve models, organized in three layers. dbt builds them bottom-up
based on `ref()` calls. Dashed lines are FK relationships that the
schema tests enforce.

```mermaid
flowchart TB
    subgraph SRC["sources"]
        S_OP["raw.open_payments"]
        S_PD["raw.part_d_prescribers"]
        S_PDD["raw.part_d_by_drug"]
        SEED["seed:<br/>drug_company_seed"]
    end

    subgraph STG["staging (views)"]
        STG_OP["stg_open_payments"]
        STG_PD["stg_part_d_prescribers"]
        STG_PDD["stg_part_d_by_drug"]
    end

    subgraph INT["intermediate (views)"]
        INT_DC["int_drug_company_<br/>mapping"]
        INT_PA["int_physician_<br/>payments_agg"]
        INT_DR["int_physician_<br/>drug_prescribing"]
    end

    subgraph MART["mart"]
        DIM_C["dim_company<br/>(table)"]
        DIM_D["dim_drug<br/>(table)"]
        DIM_P["dim_physician<br/>(table)"]
        FACT_PAY["fact_payments<br/>(view)"]
        FACT_RX["fact_prescriptions<br/>(view)"]
        FACT_PP["fact_payment_<br/>prescribing<br/>(view)"]
    end

    S_OP --> STG_OP
    S_PD --> STG_PD
    S_PDD --> STG_PDD
    SEED --> INT_DC

    STG_OP --> INT_PA
    STG_PDD --> INT_DR
    INT_DC --> INT_DR

    STG_OP --> DIM_C
    INT_DC --> DIM_C
    STG_PD --> DIM_P
    STG_OP --> DIM_P
    INT_PA --> DIM_P
    INT_DC --> DIM_D

    STG_OP --> FACT_PAY
    STG_PDD --> FACT_RX
    INT_DC --> FACT_RX
    INT_PA --> FACT_PP
    INT_DR --> FACT_PP
    DIM_P --> FACT_PP

    style DIM_C fill:#FCE7F3,stroke:#9F1239,color:#0F172A
    style DIM_D fill:#FCE7F3,stroke:#9F1239,color:#0F172A
    style DIM_P fill:#FCE7F3,stroke:#9F1239,color:#0F172A
    style FACT_PAY fill:#FEE2E2,stroke:#991B1B,color:#0F172A
    style FACT_RX fill:#FEE2E2,stroke:#991B1B,color:#0F172A
    style FACT_PP fill:#FEE2E2,stroke:#991B1B,color:#0F172A
```

**Why dims are tables and facts are views:** the dims are tiny and
joined to often, so we materialize. The facts have many rows but
mostly pass-through logic, so views keep us under Neon's storage cap.
`fact_payment_prescribing` is a full-outer-join of two intermediates —
a *table* would be ~150 MB; a *view* recomputes in ~3 sec on demand
and Streamlit caches for 10 minutes. The right trade-off for free-tier
infra.

---

## 4. User interaction flow (per page load)

What happens when a user picks a filter and hits *Apply*. Each step
is independently logged in Streamlit's runtime.

```mermaid
sequenceDiagram
    autonumber
    participant U as User (browser)
    participant ST as Streamlit (Cloud)
    participant DB as Neon Postgres
    participant CACHE as @st.cache_data

    U->>ST: Selects company + specialty
    ST->>CACHE: Cache hit?
    alt cached (last 10 min)
        CACHE-->>ST: cached DataFrame
    else not cached
        ST->>DB: SELECT ... FROM raw_mart.fact_payment_prescribing<br/>WHERE company_name = %s AND specialty = %s
        DB-->>ST: rows
        ST->>CACHE: store
    end
    ST->>ST: Compute lift ratio, render Plotly figs
    ST-->>U: Page rendered (KPIs + charts)
```

**Caching matters because Neon's free-tier compute auto-suspends after
5 minutes of inactivity, and the first query after a suspend takes
~10 sec to wake the warehouse.** With the 10-minute query cache, most
clicks return instantly from local memory.

---

## 5. "Explain this chart" LLM flow

Every chart has an *Explain this chart* button. Clicking it sends the
chart's underlying data plus a domain-aware system prompt to Groq.

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant ST as Streamlit
    participant LLM as utils/llm.py
    participant GROQ as Groq API<br/>(Llama 3.3 70B)

    U->>ST: Clicks "Explain this chart"
    ST->>LLM: explain_chart(<br/>  title, business_question,<br/>  data (top 20 rows + stats),<br/>  filter context<br/>)
    LLM->>LLM: Compose system prompt:<br/>"You are a senior pharma<br/>commercial analytics consultant<br/>at ZS Associates..."
    LLM->>LLM: Compose user prompt:<br/>title + question + data + filters
    LLM->>GROQ: POST /chat/completions<br/>(model=llama-3.3-70b-versatile)
    GROQ-->>LLM: 2-3 sentence insight +<br/>caveats + next-step
    LLM-->>ST: Markdown response
    ST-->>U: Insight in expander below chart
```

**Why this design:**

- The system prompt sets the **persona** (pharma analyst at ZS) so the
  LLM's vocabulary matches the audience.
- We send only **summarized data** (top 20 rows + describe() stats), not
  the full dataset — keeps the prompt under ~2K tokens and the cost
  near-zero on Groq's free tier.
- Hard rules in the system prompt forbid causal claims, made-up numbers,
  and moralizing — so insights stay analytical, not journalistic.

---

## Where each piece lives

| Concern | Code location |
|---|---|
| Data download / load | `scripts/download_data.py`, `scripts/load_data.py` |
| Filter parameters | `scripts/config.py` |
| dbt models | `dbt_project/models/{staging,intermediate,mart}/` |
| Data quality tests | `dbt_project/models/**/_schema.yml` |
| Drug-company mapping | `dbt_project/seeds/drug_company_seed.csv` |
| Streamlit entry | `streamlit_app/app.py` (navigation hub) |
| Six views | `streamlit_app/views/*.py` |
| Shared UI components | `streamlit_app/utils/styles.py` |
| Database access | `streamlit_app/utils/db.py` |
| LLM integration | `streamlit_app/utils/llm.py` |
| Chart helpers | `streamlit_app/utils/charts.py` |
| CI | `.github/workflows/ci.yml` |
| Pre-commit hooks | `.pre-commit-config.yaml` |

# Physician × Pharma Commercial Analytics

A pharmaceutical commercial analytics platform built on two free, public
CMS datasets — answering the central question that pharma commercial
teams, regulators, and health-economics researchers debate:

> **Do physicians who receive payments from a pharma company prescribe
> more of that company's drugs?**

Built with the modern analytics-engineering stack: **PostgreSQL · dbt ·
Streamlit · Python**, with an LLM-powered *"Explain This Chart"* feature
on every visualization.

---

## 📊 Live Demo

→ **[Open the deployed Streamlit app](https://your-app-url.streamlit.app)**
(update once deployed)

→ **[dbt docs site](https://your-username.github.io/physician-pharma-analytics)**
(update once deployed to GitHub Pages)

---

## The Business Question

The U.S. government collects two public datasets that, taken together,
allow this question to be asked rigorously:

| Dataset | What it tracks | Source |
|---|---|---|
| **CMS Open Payments** (Sunshine Act) | Every dollar a pharma / med-device company paid a U.S. physician — speaking fees, consulting, meals, travel, research | [openpaymentsdata.cms.gov](https://openpaymentsdata.cms.gov) |
| **CMS Medicare Part D Prescribers** | Every drug prescribed under Medicare Part D, by physician, with claim volume and cost | [data.cms.gov](https://data.cms.gov) |

Neither dataset answers the question alone. Joining them on physician
NPI — and attributing each prescribed drug to a manufacturer (a curated
mapping; CMS doesn't publish one) — is the analytics-engineering work
this project does.

The same join sits behind every pharma commercial analytics function:
ZS Associates, IQVIA, Komodo Health, Veeva, and every Big Pharma
in-house brand analytics team builds variations of it.

---

## What's in This Repo

```
.
├── dbt_project/                  # Analytics warehouse (dbt + Postgres)
│   ├── models/
│   │   ├── staging/              # Type casting, deduplication, name canonicalization
│   │   ├── intermediate/         # Business logic, drug→company attribution
│   │   └── mart/                 # Star schema: facts + dimensions
│   ├── analyses/                 # 5 showcase SQL analyses (see below)
│   └── seeds/                    # Curated drug→manufacturer mapping
├── streamlit_app/                # 5-page interactive dashboard
│   ├── app.py                    # Executive dashboard (entry point)
│   ├── pages/                    # KOL Finder, Company, Payment vs Rx, Market
│   └── utils/                    # DB + LLM helpers
├── scripts/                      # Data download + load pipeline
└── .github/workflows/            # CI: ruff + dbt parse/compile
```

---

## The 5 Showcase Analyses

Each is a standalone SQL file in `dbt_project/analyses/` written as a
demonstration of advanced SQL across a realistic business question.

| # | Analysis | Key SQL techniques | Business decision it informs |
|---|---|---|---|
| 1 | **KOL Identification** | `ROW_NUMBER() OVER`, percentile windows, cumulative density | Which physicians should the field team prioritize? |
| 2 | **Payment-to-Prescribing Correlation** | `FILTER` aggregates, `PERCENTILE_CONT`, `CORR()`, specialty controls | Are paid physicians prescribing more (controlled for specialty)? |
| 3 | **Company Spend Efficiency** | Pivot-via-FILTER, ratio metrics, null-safe division | Which companies get the highest associated prescribing per dollar paid? |
| 4 | **Geographic Market Analysis** | Cross-joins for shares-of-totals, `FULL OUTER JOIN` | Where is pharma over- or under-invested vs. prescribing demand? |
| 5 | **Physician Loyalty (HHI Scoring)** | Window functions for shares, sum-of-squared-shares (Herfindahl) | Which physicians prescribe single-source vs. multi-brand within a class? |

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| Database | **Neon** (free-tier Postgres) | Cloud Postgres, no Docker needed, generous free tier, familiar |
| Transformations | **dbt Core** + `dbt-postgres` | Industry standard for analytics engineering. Lineage, testing, docs built-in |
| App framework | **Streamlit** + Plotly | Fast to build, free Streamlit Cloud deployment |
| LLM ("Explain This Chart") | **Groq** Llama 3.3 70B | Free tier with generous limits, sub-second inference |
| CI | **GitHub Actions** | Free for public repos. Runs Ruff + `dbt parse` on every push |
| Data quality | `dbt-utils`, `dbt-expectations` | Generic + Great-Expectations-style tests |

---

## Data Sizing Strategy

The full CMS files are large (Open Payments ≈ 7GB unzipped CSV; Part D
by Drug ≈ 3.7GB). To stay well within Neon's 512 MB free tier *and*
leave room for future projects, the load script applies:

- **Open Payments:**
  - Keep only the top 10 manufacturers by 2022 spend (these alone
    represent ~60% of total industry physician spend)
  - Drop payments under **$50** — this removes ~70% of records
    (mostly $5–20 individual meal payments) while preserving all
    consulting, speaking, travel, research, and meaningful meal events
- **Part D Prescribers:** filter to ~15 specialties that drive the bulk
  of pharma commercial focus, drop providers with < 10 total claims
- **Part D by Drug:** keep only the ~60 brand-name drugs in our curated
  drug → manufacturer seed file

**Resulting Postgres footprint: ~150 MB.**

See `scripts/config.py` for the exact filter parameters.

---

## Getting Started

### Prerequisites
- Python 3.10+
- A free [Neon](https://neon.tech) Postgres database
- A free [Groq](https://console.groq.com) API key (for the LLM feature)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/your-username/physician-pharma-analytics.git
cd physician-pharma-analytics

# 2. Create a virtual env and install dependencies
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate      # macOS / Linux
pip install -r requirements.txt

# 3. Configure secrets
cp .env.example .env
# Edit .env and fill in DATABASE_URL, NEON_HOST, NEON_USER, NEON_PASSWORD,
# NEON_DBNAME, and GROQ_API_KEY

# 4. Download CMS data (~3.5 GB total; takes 10-30 min depending on bandwidth)
python scripts/download_data.py

# 5. Filter and load into Neon (~5 min)
python scripts/load_data.py

# 6. Build the dbt warehouse
cd dbt_project
dbt deps                       # install dbt packages
dbt seed --profiles-dir .      # load the drug→company mapping
dbt run --profiles-dir .       # build all models
dbt test --profiles-dir .      # run all data-quality tests
cd ..

# 7. Run the Streamlit app
streamlit run streamlit_app/app.py
```

### Running individual showcase analyses

```bash
cd dbt_project
dbt compile --profiles-dir .   # compiles SQL but doesn't run analyses
# Then copy the compiled SQL from target/compiled/.../analyses/ and run it
# against your warehouse directly using psql, DBeaver, or the VS Code
# SQLTools extension.
```

---

## Methodology & Caveats

Detailed methodology — including the NPI matching strategy, drug
attribution rules, sample-size thresholds, and what we can and *cannot*
conclude from observational data — is in [`METHODOLOGY.md`](./METHODOLOGY.md).

**Headline caveats:**
- All analyses are **descriptive, not causal**. Observational data
  cannot distinguish payment-influences-prescribing from
  prescribers-attract-payments.
- The drug → manufacturer mapping is **curated** to ~60 high-volume drugs
  across 9 therapeutic classes. Drugs outside this set are excluded.
- Company name canonicalization consolidates known subsidiaries
  (Janssen → Johnson & Johnson, etc.) but small mis-attributions are
  inevitable.
- The Part D file is restricted to the top prescribing specialties to
  fit within free-tier limits — generalist primary-care prescribers are
  underrepresented.

---

## Data Privacy & Ethics

This project uses **only publicly released federal data** and processes
**no patient information** of any kind.

| Concern | Status | Why |
|---|---|---|
| **HIPAA / PHI** | ✅ Not applicable | No patient identifiers, diagnoses, or encounter records are anywhere in this project. The Medicare Part D file is CMS's de-identified, aggregated *Public Use File* — cell counts under 11 are pre-suppressed by CMS for residual privacy |
| **Physician privacy** | ✅ Strengthened by design | Physician NPIs and names are professional identifiers (not PHI) and are intentionally published by CMS — but for this **public** portfolio demo, the mart layer surfaces only deterministic surrogate IDs (e.g., `Physician #4837`), not real names. Underlying analytics are unchanged |
| **CMS terms of use** | ✅ Compliant | CMS data is in the public domain. CMS explicitly encourages re-analysis and re-publication of these files |
| **Sunshine Act compliance** | ✅ Foundational | The Physician Payments Sunshine Act (§ 6002 of the Affordable Care Act, 2010) was passed *specifically* to make this data publicly available |

**Precedents:** ProPublica's *Dollars for Docs* (online continuously since 2014),
peer-reviewed papers in *JAMA Internal Medicine* and *NEJM*, and every
major pharma commercial analytics firm (ZS Associates, IQVIA, Komodo
Health, Veeva) all build on these same public datasets.

**What this project is:** a descriptive analytics platform demonstrating
the commercial-analytics tradecraft used across the pharmaceutical
industry. It is **not** investigative journalism, does **not** make
causal claims about individual physicians, and does **not** suggest any
specific payment-prescribing relationship is improper.

---

## Related Work

- **DeJong et al. (2016)**, *JAMA Internal Medicine*: "Pharmaceutical
  Industry-Sponsored Meals and Physician Prescribing Patterns for
  Medicare Beneficiaries" — the foundational paper.
- **Yeh et al. (2016)**, *JAMA Internal Medicine*: extends to specific
  drug classes.
- **ProPublica's Dollars for Docs**: ongoing journalistic coverage of
  CMS Open Payments at the individual-physician level.

---

## License

Code: MIT. Data: public domain (CMS).

---

*This project was built as part of a portfolio demonstrating
healthcare-domain analytics engineering. Questions, feedback, or
hiring inquiries — [LinkedIn](https://linkedin.com/in/your-handle).*

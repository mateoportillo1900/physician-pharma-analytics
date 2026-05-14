"""
About this project — portfolio context view
═══════════════════════════════════════════

Stand-alone view explaining what this dashboard is, why it was built,
what it demonstrates, and the tech behind it. Lives separately from the
analytical views so the dashboard stays focused on the data.
"""

from __future__ import annotations

import streamlit as st

from utils.styles import (
    GITHUB_URL,
    apply_global_styles,
    hero,
    portfolio_context,
    section_heading,
)

apply_global_styles()


hero(
    title="About this project",
    subtitle=("What you're looking at, why it was built, and how to find the source."),
)


# ─── Top-line portfolio context card ─────────────────────────────────────────
portfolio_context()


# ─── What it demonstrates ────────────────────────────────────────────────────
section_heading("What it demonstrates")

st.markdown(
    """
This is a **pharma commercial analytics platform** built end-to-end on
real federal data. The same join of CMS Open Payments and Medicare Part D
sits behind the work that teams at ZS Associates, IQVIA, Komodo Health,
AbbVie, and Tempus AI do every day for pharma clients. Specifically, it
exercises:

- **Analytics engineering** — a 12-model dbt project laid out in
  staging → intermediate → mart layers, with a proper star schema
  (4 dimensions, 3 facts) and 59 passing data-quality tests
- **Advanced SQL** — window functions, percentile aggregations, full
  outer joins, CTE-based ranking, cross-source NPI matching
- **Cloud data warehouse** — Neon Postgres on the free tier, with
  schema-aware storage budgeting to stay under the 512 MB cap
- **Decision-science framing** — every analytic view answers a real
  pharma commercial question: KOL identification, paid-vs-unpaid lift,
  territory over/under-investment, manufacturer-level competitive intel
- **AI augmentation** — an "Explain this chart" feature on every chart
  that ships the chart's data plus a domain-aware prompt to Groq's
  Llama 3.3 70B for plain-English commentary
- **Production-quality engineering hygiene** — GitHub Actions CI (Ruff +
  dbt parse), a pre-commit hook that auto-formats before every commit,
  privacy-by-design surrogate physician IDs, full methodology
  documentation
"""
)


# ─── Tech stack ──────────────────────────────────────────────────────────────
section_heading("Tech stack")

stack = [
    ("Database", "Neon Postgres (cloud, free tier)"),
    ("Transformations", "dbt-core + dbt-postgres + dbt-utils + dbt-expectations"),
    ("App framework", "Streamlit"),
    ("Charts", "Plotly"),
    ("LLM", "Groq · Llama 3.3 70B"),
    ("Lint / format", "Ruff (+ pre-commit hook)"),
    ("CI", "GitHub Actions"),
    ("Source data", "CMS Open Payments + Medicare Part D PUF (2022)"),
]
col1, col2 = st.columns(2)
for i, (label, value) in enumerate(stack):
    target = col1 if i % 2 == 0 else col2
    target.markdown(f"**{label}.** {value}")


# ─── Methodology summary ────────────────────────────────────────────────────
section_heading("Methodology in one breath")

st.markdown(
    """
- The dataset is **2022 reporting year** Open Payments General Payments
  joined to Medicare Part D Prescribing on physician NPI.
- Scope is filtered to the **top 10 pharma manufacturers** by 2022 spend
  and to payments ≥ $50 — keeps the database under Neon's 512 MB cap
  without distorting the headline analyses.
- Drugs are attributed to manufacturers via a **curated seed file**
  (60 brand-name drugs across 9 therapeutic classes). CMS doesn't ship
  this mapping; it's the analyst's job.
- All analyses are **descriptive, not causal**. Observational data
  cannot distinguish *payment-influences-prescribing* from
  *prescribers-attract-payments*. Treat lift ratios as association
  measures, not treatment effects.
- The mart layer exposes only **anonymized surrogate physician IDs**
  (e.g. `Physician #4837`) for the public-facing demo — see
  `METHODOLOGY.md` § 0 in the repo for the privacy design rationale.

Full methodology, including BMS reporting quirks, data filtering rules,
and statistical formulas, is documented in `METHODOLOGY.md` in the
source repo.
"""
)


# ─── Visual documentation ──────────────────────────────────────────────────
section_heading("Visual documentation")

st.markdown(
    f"""
For a deeper look at how the system works, the repo ships with
**Mermaid-diagram-driven docs** that render directly on GitHub:

- [**docs/ARCHITECTURE.md**]({GITHUB_URL}/blob/main/docs/ARCHITECTURE.md) —
  The five-layer system architecture, data pipeline (CSV → mart), dbt
  model lineage for all 12 models, user-interaction sequence diagram,
  and the LLM "Explain this chart" flow.
- [**docs/DATA_MODEL.md**]({GITHUB_URL}/blob/main/docs/DATA_MODEL.md) —
  Star-schema ER diagram, table-by-table reference, the headline
  analytical join (paid × prescribed × neither), data-quality
  enforcement, and privacy-by-design rationale.
- [**METHODOLOGY.md**]({GITHUB_URL}/blob/main/METHODOLOGY.md) —
  Analytical decisions, statistical formulas (lift ratio, HHI,
  investment ratio), the BMS reporting quirk, and what we can and
  cannot conclude from observational data.

You can also run `dbt docs generate && dbt docs serve` locally to get
the **interactive lineage explorer** for every model.
"""
)


# ─── Source ─────────────────────────────────────────────────────────────────
section_heading("Source")

st.markdown(
    f"""
The complete source code, dbt project, load scripts, and methodology
docs live at:

[**{GITHUB_URL}**]({GITHUB_URL})
"""
)

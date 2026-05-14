# Documentation

Visual guide to the *Physician × Pharma Commercial Analytics* project.
Read these in order if you're new — they assume nothing.

| Document | What it covers |
|---|---|
| [**ARCHITECTURE.md**](./ARCHITECTURE.md) | The five-layer system architecture, the data pipeline, dbt model lineage, user-interaction sequence, and the LLM "Explain this chart" flow. Start here. |
| [**DATA_MODEL.md**](./DATA_MODEL.md) | Star-schema ER diagram, what each table is for, the headline analytical join, data-quality enforcement, and privacy design |
| [**../METHODOLOGY.md**](../METHODOLOGY.md) | Analytical decisions, statistical formulas, limitations, and the BMS reporting quirk. The "what we can and cannot conclude" doc |
| [**../README.md**](../README.md) | Top-level project description and setup instructions |

All diagrams are written in [Mermaid](https://mermaid.js.org/) so they
render directly on GitHub without needing image files. To regenerate
the live dbt-generated lineage docs, run:

```bash
cd dbt_project
dbt docs generate
dbt docs serve   # opens at localhost:8080
```

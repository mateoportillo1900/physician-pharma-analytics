# Methodology

This document explains the analytical decisions, data caveats, and
limitations behind the *Physician × Pharma Commercial Analytics*
platform. It exists because a portfolio project that doesn't
document its own methodology is the analytics equivalent of a paper
without a "Limitations" section.

---

## 0. Privacy by Design

The underlying CMS data legally permits displaying individual physician
names (this is the design intent of the Sunshine Act). However, this is
a **public** portfolio demo, not an internal pharma commercial tool, so:

- The mart layer (`dim_physician`) replaces real names with deterministic
  surrogate IDs of the form `Physician #4837` — derived from a hash of
  the NPI, so the same physician maps to the same display ID across the
  app, but the ID cannot be reversed to a real name
- `physician_npi` is retained because it is a public professional
  identifier (like a business license), but no first/last name columns
  propagate beyond the staging layer
- The staging layer keeps real names because they're needed for any
  internal re-identification work, but Streamlit only ever queries the
  mart

This pattern matches how research publications using Open Payments data
typically present aggregate analyses. It strengthens the project's
defensibility for any audience.

---

## 0b. Known Data Quirks

### Why does Bristol Myers Squibb appear small?

BMS shows only ~$2.3M of 2022 spend in this dataset (combined with its
Celgene subsidiary). That is dramatically lower than peers like Pfizer
($253M) or AbbVie ($115M), and lower than you'd expect from a top-5
pharma manufacturer. **This reflects how BMS reports under the Sunshine
Act, not a bug in this project:**

- **Eliquis** (BMS's largest revenue product) is co-marketed with Pfizer.
  Most of the Eliquis-related general payments are reported by Pfizer
  as the paying entity, not BMS — so they appear under Pfizer here.
- BMS's substantial **Research Payments** (clinical trial-related)
  are reported in a separate category that this project intentionally
  excludes (we use General Payments only — see § 1.1).
- The **$50 minimum payment filter** drops small-value meal events
  which would have padded the count without changing the headline
  story (see § 1).

If you needed an accurate BMS total spend including research, you'd
load Open Payments' Research Payments file and re-aggregate. We don't,
because this project is about commercial / promotional engagement
(the General Payments bucket), where BMS legitimately is a smaller
spender than its drug revenue would suggest.

---

## 1. Data Sources

### 1.1 CMS Open Payments (General Payments) — 2022

- **What it is:** Mandated disclosure under the Physician Payments
  Sunshine Act (§ 6002 of the Affordable Care Act). Pharmaceutical and
  medical-device manufacturers must report every transfer of value
  ≥ $10 (or ≥ $100 aggregate) to a U.S. physician.
- **Scope used:** "General Payments" only — not Research Payments
  (≈ 70% of total Open Payments $) or Ownership Interests. General
  Payments capture the commercial-engagement spending most relevant
  to brand prescribing influence (speaking, consulting, meals,
  travel, education).
- **Filters applied** (see `scripts/config.py`):
  - **Top 10 manufacturers by 2022 spend.** These alone account for
    roughly 60% of total U.S. industry physician spend, cover all
    major therapeutic classes in our drug seed, and keep the database
    well under free-tier limits
  - **Minimum payment threshold: $50.** Removes the bulk of
    individual $5–20 meal records (which make up ~70% of all Open
    Payments rows) without losing meaningful commercial-engagement
    payments. The "doctor lunch" phenomenon is still represented by
    meals ≥ $50 (real meeting meals, not passing coffees)
- **Trade-off awareness:** the $50 floor means we under-count the
  *number* of meal events but preserve their *dollar value*. Analyses
  focused on dollar totals (KOL identification, spend efficiency)
  are unaffected. Analyses focused on event counts (payment frequency)
  should be interpreted with this floor in mind.

### 1.2 CMS Medicare Part D Prescriber PUF — 2022

- **What it is:** Aggregated Medicare Part D prescribing activity at
  the (physician × drug) level. Public, anonymized for low cell counts.
- **Two views loaded:**
  - **By Provider** — one row per NPI, total Part D activity across
    all drugs (used for KOL volume rankings, specialty rollups)
  - **By Provider × Drug** — one row per (NPI × brand name), used
    for the drug-level payment-to-prescribing analysis
- **Filter applied:**
  - By-Provider: top prescribing specialties only (cardiology,
    oncology, endocrinology, immunology, etc.); min 10 total claims
    to remove inactive providers
  - By-Drug: only drugs in our curated drug → manufacturer mapping
    (see `dbt_project/seeds/drug_company_seed.csv`)

### 1.3 Drug → Manufacturer Mapping

This is the analytical lift CMS doesn't do for us. Neither the
Open Payments file nor the Part D file attributes drugs to
manufacturers. We curate the mapping manually from:

- FDA Orange Book (definitive but verbose)
- Manufacturer press releases and 10-K filings
- DailyMed structured product labels

**The seed file in `dbt_project/seeds/drug_company_seed.csv` is the
authoritative source.** Adding a drug requires confirming its
labeled manufacturer.

**Edge case — co-marketed drugs:** A handful of drugs are co-marketed
by two companies under a single brand name (e.g., Eliquis: Pfizer +
Bristol-Myers Squibb; Xarelto: Johnson & Johnson + Bayer). We preserve
both rows in the mapping. The downstream analyses thus produce two
rows for these drugs in the prescribing fact table — which is the
correct attribution. The Streamlit app does not double-count claims
because aggregations happen at the (physician × company) grain.

---

## 2. Joining the Two Datasets

### 2.1 Join Key: National Provider Identifier (NPI)

The NPI is a 10-digit numeric identifier issued by CMS to every
healthcare provider. It's the de-facto primary key for U.S.
healthcare data interoperability.

**Pitfall handled:** CMS exports sometimes drop leading zeros,
turning a 10-digit NPI into a 9-digit integer. Both staging models
left-pad NPIs to 10 characters before joining.

### 2.2 What "Paid" Means

A physician is classified as "paid by Company X" in 2022 if they
received ≥ $1 from Company X in 2022, summed across all
general-payment categories.

This is a binary flag — we don't tier by payment amount in the
"paid vs. unpaid" comparisons. The Payment vs. Prescribing page's
scatter plot is where the dollar-amount dimension is restored.

### 2.3 Specialty Controls

The headline "lift ratio" (mean prescribing volume — paid vs. unpaid)
is computed *within specialty* and then can be aggregated across
specialties. This matters because:

- A cardiologist prescribes more cardiac drugs than a dermatologist
  regardless of payments
- Pharma payments aren't randomly distributed across specialties —
  cardiology and oncology see disproportionately more payments

Comparing paid cardiologists to unpaid dermatologists would confound
the effect we're trying to measure.

**Minimum cell size:** The correlation analysis requires ≥ 30 paid
and ≥ 30 unpaid physicians per (specialty × company) cell to be
included in summary tables. This is the standard
small-sample threshold from the DeJong (2016) JAMA paper.

---

## 3. Statistical Methods

### 3.1 Lift Ratio

$$
\text{Lift} = \frac{\bar{x}_{\text{paid}}}{\bar{x}_{\text{unpaid}}}
$$

where $\bar{x}$ is mean Part D claims for the company's drugs within
the specialty.

A lift ratio of 2.0 means paid physicians prescribe twice as many
of the company's drugs, on average, as unpaid peers in the same
specialty.

### 3.2 Pearson Correlation (within paid group)

Reported per (specialty × company) cell in the Payment vs. Prescribing
analysis. Both axes are log-scaled in the scatter plot because the
distributions are extremely right-skewed.

### 3.3 Herfindahl-Hirschman Index (Loyalty Scoring)

For each (physician × therapeutic class), compute each company's
share of the physician's class prescribing volume. The HHI is:

$$
\text{HHI} = \sum_{i=1}^{n} s_i^2 \times 10{,}000
$$

where $s_i$ is company $i$'s share (0–1). The scaling by 10,000 is
the antitrust-economics convention:

- 10,000 = monopoly (single company)
- 1,000 = evenly spread across 10 companies

Loyalty tiers:
- ≥ 9,000 = Loyalist (single source)
- 5,000–8,999 = Strong preference
- 2,500–4,999 = Mixed prescriber
- < 2,500 = Highly diversified

### 3.4 Geographic Investment Ratio

$$
\text{Investment Ratio}_{s} = \frac{\text{Payment Share}_{s}}{\text{Rx Share}_{s}}
$$

where shares are state $s$'s share of national totals. Ratio = 1.0
means the state's payment share matches its prescribing share —
proportionally invested. Thresholds:

- > 1.25 = Over-invested
- 0.75–1.25 = Balanced
- < 0.75 = Under-invested

The 0.75 / 1.25 thresholds are a pragmatic split, not a statistical
test. Choosing tighter thresholds (e.g., 0.9 / 1.1) classifies more
states as imbalanced; looser thresholds (0.5 / 2.0) classifies fewer.

---

## 4. What We *Cannot* Conclude

### 4.1 No Causal Claim

The observational data cannot distinguish between:

1. **"Payments → prescribing"** — the company pays a physician, who
   then prescribes more of the company's drugs
2. **"Prescribing → payments"** — the company identifies high-volume
   prescribers and recruits them as paid speakers / consultants
3. **Confounding by specialty interest** — a physician with an
   intrinsic interest in the company's therapeutic area attracts both
   payments *and* writes more of that company's drugs, with no causal
   link between the two

This is a fundamental limitation of cross-sectional observational
data. The DeJong (2016) paper, which uses the same data structure,
explicitly disclaims a causal interpretation. So do we.

To establish causation you would need either:
- A natural experiment (e.g., a sudden ban on meals in some states)
- An instrumental variable
- A longitudinal panel with payment changes preceding prescribing
  changes by enough lag to rule out simultaneity

This project does not attempt any of those.

### 4.2 Self-Selection Bias in the Specialty Filter

We restrict the Part D file to ~15 specialties. Generalists (family
medicine, internal medicine) are included but in smaller
proportional volume than they appear in the full file. Conclusions
should be read as applying to *specialist prescribing*, not to
primary care.

### 4.3 Coverage Gaps in the Drug Mapping

Our drug mapping covers ~60 high-revenue brand drugs across 9
therapeutic classes. Generic prescribing — which is the majority of
Medicare Part D volume — is not included by design. Conclusions
apply to *brand* prescribing only.

### 4.4 Single-Year Snapshot

2022 only. Year-over-year dynamics (does last year's payment lift
next year's prescribing?) require multi-year panel data, which we
don't load to keep within free-tier storage.

---

## 5. Data Quality Tests

All quality assertions are enforced via dbt tests on every `dbt test`
run. See `dbt_project/models/*/_schema.yml`. Key tests:

| Test | What it enforces |
|---|---|
| `unique` on `payment_id` | No double-counted payments |
| `unique` on `physician_npi` in `dim_physician` | NPI is a true primary key |
| `not_null` on join keys | NPI, company, drug brand never null after staging |
| `accepted_values` on `payment_category` | Only the 12 canonical categories allowed |
| `relationships` between fact and dim tables | Referential integrity |
| `dbt_expectations.expect_column_values_to_be_between` on amounts | No negative payments, no $100M+ outliers |

---

## 6. Reproducibility

Anyone with a free Neon database and a free Groq key can reproduce
every number in the Streamlit app by running:

```bash
python scripts/download_data.py
python scripts/load_data.py
cd dbt_project && dbt deps && dbt seed && dbt run && dbt test
```

The total runtime is ~30 min on a typical home connection, dominated
by the data download. The dbt build takes ~2 min on Neon free-tier
compute.

---

## 7. Updating to a New Year

When CMS releases 2023 data (expected late 2025):

1. Update the URLs in `scripts/config.py`
2. Re-run download + load
3. The dbt models are year-agnostic — no changes needed

The drug → manufacturer seed file should be reviewed for new
approvals (e.g., new oncology launches) and discontinuations.

---

*Last updated: 2026*

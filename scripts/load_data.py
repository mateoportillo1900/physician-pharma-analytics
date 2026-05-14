"""
Filter the raw CMS CSVs and load them into Neon Postgres.

Strategy to keep Neon usage under ~150 MB:
  • Open Payments      → keep only top 20 pharma companies, drop trivial columns
  • Part D Provider    → keep only selected specialties, drop tiny prescribers
  • Part D by Drug     → keep only the curated drug list (see config.py)

This script is idempotent: it drops and recreates each `raw.*` table on
every run, so it's safe to re-run after schema changes.

Run:
    python scripts/load_data.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Make project root importable regardless of how this script is invoked
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Force UTF-8 stdout so emoji/unicode print on Windows (cp1252 default)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import pandas as pd
import psycopg
from dotenv import load_dotenv
from psycopg import sql
from tqdm import tqdm

from scripts.config import (
    MIN_PAYMENT_USD,
    MIN_TOTAL_CLAIMS,
    RAW_DIR,
    TRACKED_DRUGS,
)

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit(
        "DATABASE_URL not set. Copy .env.example → .env and fill in your "
        "Neon connection string."
    )

# How many rows to read from CSV at a time (memory management)
CHUNKSIZE = 200_000


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def ensure_raw_schema(conn: psycopg.Connection) -> None:
    """Create the `raw` schema if it doesn't exist."""
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    conn.commit()


def drop_and_create_table(conn: psycopg.Connection, table: str, ddl: str) -> None:
    """Drop and recreate a raw table from a DDL string."""
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("DROP TABLE IF EXISTS raw.{} CASCADE;").format(
                sql.Identifier(table)
            )
        )
        cur.execute(ddl)
    conn.commit()


def copy_dataframe(conn: psycopg.Connection, table: str, df: pd.DataFrame) -> None:
    """Bulk-load a DataFrame into raw.<table> using COPY.

    Uses Postgres COPY in default TEXT format (tab-separated). psycopg's
    write_row() serializes Python values to TAB-separated text and handles
    NULL/None correctly. Don't switch to FORMAT CSV — write_row's output
    won't match CSV's comma-delimiter expectation.
    """
    if df.empty:
        return

    columns = list(df.columns)
    copy_sql = sql.SQL("COPY raw.{table} ({cols}) FROM STDIN").format(
        table=sql.Identifier(table),
        cols=sql.SQL(", ").join(map(sql.Identifier, columns)),
    )

    with conn.cursor() as cur, cur.copy(copy_sql) as copy:
        for _, row in df.iterrows():
            # Replace any pandas NA / NaN / NaT with native None,
            # which psycopg serializes as Postgres NULL via \N
            row_vals = [None if pd.isna(v) else v for v in row.tolist()]
            copy.write_row(row_vals)
    conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Loaders
# ─────────────────────────────────────────────────────────────────────────────


def load_open_payments(conn: psycopg.Connection) -> int:
    """Load filtered Open Payments General into raw.open_payments."""
    print("\n[1/3] Loading Open Payments...")

    # Find the extracted CSV
    extract_dir = RAW_DIR / "open_payments_unzipped"
    csv_files = list(extract_dir.glob("OP_DTL_GNRL_PGYR*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No Open Payments CSV found in {extract_dir}. "
            "Run scripts/download_data.py first."
        )
    csv_path = csv_files[0]

    ddl = """
        CREATE TABLE raw.open_payments (
            physician_npi TEXT,
            company_name TEXT,
            payment_amount_usd NUMERIC(14, 2),
            payment_date DATE,
            payment_nature TEXT,
            recipient_state TEXT
        );
    """
    drop_and_create_table(conn, "open_payments", ddl)

    # CMS Open Payments column names — verified against 2022 PGYR layout
    use_cols = {
        "Covered_Recipient_NPI": "physician_npi",
        "Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Name": "company_name",
        "Total_Amount_of_Payment_USDollars": "payment_amount_usd",
        "Date_of_Payment": "payment_date",
        "Nature_of_Payment_or_Transfer_of_Value": "payment_nature",
        "Recipient_State": "recipient_state",
    }

    total_loaded = 0

    chunks = pd.read_csv(
        csv_path,
        usecols=list(use_cols.keys()),
        dtype=str,
        chunksize=CHUNKSIZE,
        encoding="latin-1",
        on_bad_lines="skip",
    )

    pbar = tqdm(chunks, desc="    Open Payments chunks", unit="chunk")
    for chunk in pbar:
        chunk = chunk.rename(columns=use_cols)

        # Filter to top 10 tracked companies (alias matching matches the
        # SQL canonicalization in stg_open_payments.sql)
        company_upper = chunk["company_name"].fillna("").str.upper()
        keep_mask = (
            company_upper.str.startswith("PFIZER")
            | company_upper.str.startswith("ABBVIE")
            | company_upper.str.startswith("JOHNSON & JOHNSON")
            | company_upper.str.startswith("JANSSEN")
            | company_upper.str.startswith("NOVO NORDISK")
            | company_upper.str.startswith("MERCK")
            | company_upper.str.startswith("BRISTOL")
            | company_upper.str.startswith("ELI LILLY")
            | company_upper.str.startswith("LILLY")
            | company_upper.str.startswith("ASTRAZENECA")
            | company_upper.str.startswith("NOVARTIS")
            | company_upper.str.startswith("AMGEN")
        )
        chunk = chunk[keep_mask].copy()

        if chunk.empty:
            continue

        # Type coercion (loose; the dbt staging model does strict casting)
        chunk["payment_amount_usd"] = pd.to_numeric(
            chunk["payment_amount_usd"], errors="coerce"
        )
        chunk["payment_date"] = pd.to_datetime(
            chunk["payment_date"], errors="coerce"
        ).dt.date
        chunk = chunk.dropna(
            subset=["physician_npi", "company_name", "payment_amount_usd"]
        )

        # Drop payments under MIN_PAYMENT_USD — cuts most $5-$20 meal noise
        # while keeping all meaningful commercial-engagement payments
        chunk = chunk[chunk["payment_amount_usd"] >= MIN_PAYMENT_USD]

        copy_dataframe(conn, "open_payments", chunk)
        total_loaded += len(chunk)
        pbar.set_postfix(loaded=f"{total_loaded:,}")

    print(f"  ✓ Loaded {total_loaded:,} payment rows to raw.open_payments")
    return total_loaded


def load_part_d_provider(conn: psycopg.Connection) -> int:
    """Load filtered Part D Prescriber by Provider."""
    print("\n[2/3] Loading Part D Prescribers (by provider)...")

    csv_path = RAW_DIR / "part_d_provider_2022.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Run scripts/download_data.py first."
        )

    ddl = """
        CREATE TABLE raw.part_d_prescribers (
            physician_npi TEXT,
            provider_first_name TEXT,
            provider_last_name TEXT,
            specialty TEXT,
            state TEXT,
            total_claim_count INTEGER,
            total_drug_cost_usd NUMERIC(14, 2),
            total_beneficiary_count INTEGER
        );
    """
    drop_and_create_table(conn, "part_d_prescribers", ddl)

    use_cols = {
        "Prscrbr_NPI": "physician_npi",
        "Prscrbr_First_Name": "provider_first_name",
        "Prscrbr_Last_Org_Name": "provider_last_name",
        "Prscrbr_Type": "specialty",
        "Prscrbr_State_Abrvtn": "state",
        "Tot_Clms": "total_claim_count",
        "Tot_Drug_Cst": "total_drug_cost_usd",
        "Tot_Benes": "total_beneficiary_count",
    }

    total_loaded = 0
    chunks = pd.read_csv(
        csv_path,
        usecols=list(use_cols.keys()),
        dtype=str,
        chunksize=CHUNKSIZE,
        encoding="latin-1",
        on_bad_lines="skip",
    )

    pbar = tqdm(chunks, desc="    Part D Provider chunks", unit="chunk")
    for chunk in pbar:
        chunk = chunk.rename(columns=use_cols)

        # Filter to tracked specialties (loose substring match to capture
        # CMS's verbose taxonomy)
        spec_lower = chunk["specialty"].fillna("").str.lower()
        keep_mask = (
            spec_lower.str.contains("cardiolog")
            | spec_lower.str.contains("oncolog")
            | spec_lower.str.contains("hematolog")
            | spec_lower.str.contains("endocrinolog")
            | spec_lower.str.contains("rheumatolog")
            | spec_lower.str.contains("gastroenterolog")
            | spec_lower.str.contains("neurolog")
            | spec_lower.str.contains("psychiat")
            | spec_lower.str.contains("dermatolog")
            | spec_lower.str.contains("pulmonolog")
            | spec_lower.str.contains("nephrolog")
            | spec_lower.str.contains("urolog")
            | spec_lower.str.contains("infectious disease")
            | spec_lower.str.contains("family")
            | spec_lower.str.contains("internal medicine")
            | spec_lower.str.contains("general practice")
            | spec_lower.str.contains("nurse practitioner")
            | spec_lower.str.contains("physician assistant")
        )
        chunk = chunk[keep_mask].copy()

        # Drop tiny prescribers and rows with no NPI.
        # Cast counts to nullable Int64 — the source CSV uses floats like
        # "155.0" for counts which fail psycopg's COPY-to-INTEGER cast.
        chunk["total_claim_count"] = pd.to_numeric(
            chunk["total_claim_count"], errors="coerce"
        ).astype("Int64")
        chunk = chunk.dropna(subset=["physician_npi", "total_claim_count"])
        chunk = chunk[chunk["total_claim_count"] >= MIN_TOTAL_CLAIMS]

        if chunk.empty:
            continue

        chunk["total_drug_cost_usd"] = pd.to_numeric(
            chunk["total_drug_cost_usd"], errors="coerce"
        )
        chunk["total_beneficiary_count"] = pd.to_numeric(
            chunk["total_beneficiary_count"], errors="coerce"
        ).astype("Int64")

        copy_dataframe(conn, "part_d_prescribers", chunk)
        total_loaded += len(chunk)
        pbar.set_postfix(loaded=f"{total_loaded:,}")

    print(f"  ✓ Loaded {total_loaded:,} prescriber rows to raw.part_d_prescribers")
    return total_loaded


def load_part_d_by_drug(conn: psycopg.Connection) -> int:
    """Load filtered Part D Prescribers by Drug — only tracked drugs."""
    print("\n[3/3] Loading Part D by Drug (tracked drugs only)...")

    csv_path = RAW_DIR / "part_d_provider_drug_2022.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Run scripts/download_data.py first."
        )

    ddl = """
        CREATE TABLE raw.part_d_by_drug (
            physician_npi TEXT,
            drug_brand_name TEXT,
            drug_generic_name TEXT,
            total_claim_count INTEGER,
            total_drug_cost_usd NUMERIC(14, 2)
        );
    """
    drop_and_create_table(conn, "part_d_by_drug", ddl)

    use_cols = {
        "Prscrbr_NPI": "physician_npi",
        "Brnd_Name": "drug_brand_name",
        "Gnrc_Name": "drug_generic_name",
        "Tot_Clms": "total_claim_count",
        "Tot_Drug_Cst": "total_drug_cost_usd",
    }

    tracked_drugs_upper = {d.upper() for d in TRACKED_DRUGS}
    total_loaded = 0

    chunks = pd.read_csv(
        csv_path,
        usecols=list(use_cols.keys()),
        dtype=str,
        chunksize=CHUNKSIZE,
        encoding="latin-1",
        on_bad_lines="skip",
    )

    pbar = tqdm(chunks, desc="    Part D by Drug chunks", unit="chunk")
    for chunk in pbar:
        chunk = chunk.rename(columns=use_cols)

        brand_upper = chunk["drug_brand_name"].fillna("").str.upper().str.strip()
        chunk = chunk[brand_upper.isin(tracked_drugs_upper)].copy()

        if chunk.empty:
            continue

        chunk["total_claim_count"] = pd.to_numeric(
            chunk["total_claim_count"], errors="coerce"
        ).astype("Int64")
        chunk["total_drug_cost_usd"] = pd.to_numeric(
            chunk["total_drug_cost_usd"], errors="coerce"
        )
        chunk = chunk.dropna(
            subset=["physician_npi", "drug_brand_name", "total_claim_count"]
        )

        copy_dataframe(conn, "part_d_by_drug", chunk)
        total_loaded += len(chunk)
        pbar.set_postfix(loaded=f"{total_loaded:,}")

    print(f"  ✓ Loaded {total_loaded:,} drug-prescriber rows to raw.part_d_by_drug")
    return total_loaded


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main() -> int:
    import argparse  # noqa: PLC0415

    parser = argparse.ArgumentParser(description="Load CMS data into Neon")
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        choices=["open_payments", "part_d_provider", "part_d_by_drug"],
        help="Skip a load step (useful for resuming after a failure)",
    )
    args = parser.parse_args()

    print("=" * 72)
    print(" Load CMS Data → Neon Postgres")
    print("=" * 72)
    if args.skip:
        print(f" Skipping: {', '.join(args.skip)}")

    op_rows = pd_prov_rows = pd_drug_rows = -1

    with psycopg.connect(DATABASE_URL) as conn:
        ensure_raw_schema(conn)
        if "open_payments" not in args.skip:
            op_rows = load_open_payments(conn)
        if "part_d_provider" not in args.skip:
            pd_prov_rows = load_part_d_provider(conn)
        if "part_d_by_drug" not in args.skip:
            pd_drug_rows = load_part_d_by_drug(conn)

    print("\n" + "=" * 72)
    print(" ✓ Load complete")
    print("=" * 72)
    if op_rows >= 0:
        print(f"   open_payments      : {op_rows:>10,} rows")
    if pd_prov_rows >= 0:
        print(f"   part_d_prescribers : {pd_prov_rows:>10,} rows")
    if pd_drug_rows >= 0:
        print(f"   part_d_by_drug     : {pd_drug_rows:>10,} rows")
    print("\nNext step: cd dbt_project && dbt run && dbt test")
    return 0


if __name__ == "__main__":
    sys.exit(main())

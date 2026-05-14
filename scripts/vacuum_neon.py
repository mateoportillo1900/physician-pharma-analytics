"""
One-off utility: drop raw tables and reclaim space on Neon.

Useful when a partial load filled the database and Neon's 512 MB free-tier
limit needs to be reset. Run after fixing your filters.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]


def main() -> None:
    print("Connecting to Neon...")
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            print("\nDropping raw.open_payments (partial load)...")
            cur.execute("DROP TABLE IF EXISTS raw.open_payments CASCADE;")
            print("Dropped.")

            print("\nRunning VACUUM FULL to reclaim space...")
            cur.execute("VACUUM FULL;")
            print("Vacuum complete.")

            cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            size = cur.fetchone()[0]
            print(f"\nDatabase size: {size}")

            cur.execute("""
                SELECT relname, n_live_tup
                FROM pg_stat_user_tables
                WHERE schemaname IN ('raw', 'staging', 'intermediate', 'mart')
                ORDER BY n_live_tup DESC
            """)
            rows = cur.fetchall()
            if rows:
                print("\nRemaining tables:")
                for name, count in rows:
                    print(f"  {name}: {count:,} rows")
            else:
                print("\nNo tables in raw/staging/mart schemas.")


if __name__ == "__main__":
    main()

"""
Database utilities for the Streamlit app.

All database access goes through `run_query()`. Results are cached for 10
minutes to keep Neon's free-tier connection count low. Streamlit's
@st.cache_data is keyed on the query text + params, so changes to either
trigger a re-fetch.
"""

from __future__ import annotations

import os

import pandas as pd
import psycopg
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _get_database_url() -> str:
    """Resolve the database URL from Streamlit secrets or env vars."""
    # Streamlit Cloud uses st.secrets; local dev uses .env
    try:
        return st.secrets["DATABASE_URL"]
    except (FileNotFoundError, KeyError):
        url = os.environ.get("DATABASE_URL")
        if not url:
            st.error(
                "DATABASE_URL is not set. Configure it in .env (local) or "
                "Streamlit Cloud secrets (production)."
            )
            st.stop()
        return url


@st.cache_resource
def _connection_pool():
    """Lazy-initialized psycopg connection pool. One per Streamlit session."""
    from psycopg_pool import ConnectionPool       # noqa: PLC0415
    return ConnectionPool(
        conninfo=_get_database_url(),
        min_size=1,
        max_size=3,
        kwargs={"connect_timeout": 10},
    )


@st.cache_data(ttl=600, show_spinner=False)
def run_query(query: str, params: tuple | None = None) -> pd.DataFrame:
    """
    Execute a parameterized SQL query against Neon and return a DataFrame.

    Cached for 10 minutes to avoid hammering the free tier.

    Args:
        query: SQL string, with %s placeholders for any params
        params: tuple of parameter values

    Returns:
        pandas DataFrame
    """
    with psycopg.connect(_get_database_url()) as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_filter_options(table: str, column: str, limit: int = 200) -> list[str]:
    """Return distinct values for a column — used to populate dropdowns."""
    df = run_query(
        f"""
        SELECT DISTINCT {column}
        FROM raw_mart.{table}
        WHERE {column} IS NOT NULL
        ORDER BY {column}
        LIMIT %s
        """,
        params=(limit,),
    )
    return df[column].tolist()

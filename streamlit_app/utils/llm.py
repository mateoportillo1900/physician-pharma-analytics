"""
LLM-powered "Explain This Chart" feature.

Each Streamlit page renders one or more charts. Below each chart is an
"Explain This Chart" button. Clicking it sends the chart's underlying data
(summarized to ~20 rows) plus a domain-aware prompt to Groq's Llama 3.3
70B. The response is a short, business-language insight written in the
voice of a pharma commercial analytics consultant.

This pattern shows up in pretty much every "AI-augmented BI" product
shipping in 2026 (Looker AI, Tableau Pulse, Power BI Copilot, ThoughtSpot
Sage). Building it from scratch on a free LLM stack signals you
understand the architecture, not just the marketing.
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


SYSTEM_PROMPT = """You are a senior pharma commercial analytics consultant at \
ZS Associates. You're explaining a chart to a brand manager who is technical \
but time-pressed. Your job:

1. State the single most important insight in one sentence.
2. Add 2-3 short bullets of supporting detail.
3. Suggest one concrete next-step a commercial team could take.
4. Flag any caveats (small sample sizes, observational data, etc.).

Tone: confident but precise. No filler. No "I see that...". No headers \
unless you have 4+ bullets. Plain English — no jargon unless it adds meaning.

Hard rules:
- Never claim causation from observational data. Use "associated with" \
  not "caused by".
- Never invent numbers not in the data summary.
- Never moralize about pharma payments. Stay analytical."""


def _get_groq_client():
    """Lazy Groq client. Returns None if no key configured."""
    try:
        from groq import Groq  # noqa: PLC0415
    except ImportError:
        return None

    api_key = None
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except (FileNotFoundError, KeyError):
        api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        return None

    return Groq(api_key=api_key)


def _summarize_dataframe(df: pd.DataFrame, max_rows: int = 20) -> str:
    """Compress a DataFrame to a compact text block for the LLM prompt."""
    if df.empty:
        return "[empty result set]"

    # If it's bigger than max_rows, sample head + tail + key stats
    if len(df) > max_rows:
        sampled = pd.concat([df.head(max_rows // 2), df.tail(max_rows // 2)])
        summary = f"(Showing first/last {max_rows // 2} of {len(df):,} rows)\n\n"
    else:
        sampled = df
        summary = f"(All {len(df):,} rows)\n\n"

    summary += sampled.to_string(index=False, max_cols=10)

    # Add basic numeric stats if there are numeric columns
    numeric = df.select_dtypes(include="number")
    if not numeric.empty:
        summary += "\n\nKey statistics:\n"
        stats = numeric.describe().round(2)
        summary += stats.to_string()

    return summary


def explain_chart(
    chart_title: str,
    business_question: str,
    data: pd.DataFrame,
    extra_context: str | None = None,
) -> str:
    """
    Generate an LLM-written insight for a chart.

    Args:
        chart_title: short title of the chart (e.g. "Top 10 KOLs in Oncology")
        business_question: what question the chart answers
        data: the underlying DataFrame
        extra_context: optional extra detail (e.g. filter values applied)

    Returns:
        The LLM response as a markdown string. Returns a friendly placeholder
        if GROQ_API_KEY is missing.
    """
    client = _get_groq_client()
    if client is None:
        return (
            "💡 *To enable AI-powered chart explanations, set the "
            "`GROQ_API_KEY` environment variable.* "
            "[Get a free key →](https://console.groq.com/)"
        )

    data_block = _summarize_dataframe(data)

    user_prompt = f"""Chart: **{chart_title}**

Business question it answers:
{business_question}
"""
    if extra_context:
        user_prompt += f"\nContext / filters applied:\n{extra_context}\n"

    user_prompt += f"\nData:\n```\n{data_block}\n```"

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ LLM call failed: `{exc}`"


def render_explain_button(
    chart_title: str,
    business_question: str,
    data: pd.DataFrame,
    extra_context: str | None = None,
    key_suffix: str = "",
) -> None:
    """
    Render the "💡 Explain This Chart" button + collapsible insight box.

    Place this immediately below each chart in your Streamlit pages.
    Pass `key_suffix` if multiple charts on one page use this helper
    (Streamlit needs unique widget keys).
    """
    button_key = f"explain_{chart_title}_{key_suffix}".replace(" ", "_")[:60]
    state_key = f"explanation_{button_key}"

    if st.button("💡 Explain this chart", key=button_key):
        with st.spinner("Generating insight..."):
            explanation = explain_chart(
                chart_title=chart_title,
                business_question=business_question,
                data=data,
                extra_context=extra_context,
            )
            st.session_state[state_key] = explanation

    if state_key in st.session_state:
        with st.expander("🤖 AI-generated insight", expanded=True):
            st.markdown(st.session_state[state_key])
            st.caption(
                "*Generated by Llama 3.3 70B via Groq. "
                "Sample-size and observational-data caveats apply.*"
            )

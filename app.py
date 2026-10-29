"""Streamlit UI — Finance Agents (multi-agent stock research).

Run:  streamlit run app.py
Works out of the box in mock mode (no API key). Set LLM_MODE=meta and
MODEL_API_KEY in .env to run the team on Meta's Muse Spark via the
Meta Model API (the primary provider). LLM_MODE=groq + GROQ_API_KEY
selects the Groq free tier as a development stand-in only.

Settings come from environment variables; on Streamlit Cloud the same
keys can be provided as app secrets — they are copied into the
environment below (an explicit environment variable always wins).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st  # noqa: E402

_SECRET_KEYS = (
    "LLM_MODE",
    "MODEL_API_KEY",
    "META_API_BASE",
    "META_MODEL",
    "GROQ_API_KEY",
    "GROQ_API_BASE",
    "GROQ_MODEL",
    "DATA_MODE",
)
try:
    for _key in _SECRET_KEYS:
        if _key in st.secrets and _key not in os.environ:
            os.environ[_key] = str(st.secrets[_key])
except Exception:
    pass  # no secrets configured — environment / .env only

from finance_agents.config import get_settings  # noqa: E402
from finance_agents.llm import describe_llm  # noqa: E402
from finance_agents.pipeline import DISCLAIMER, run_pipeline  # noqa: E402

st.set_page_config(page_title="Finance Agents", page_icon="📈", layout="wide")
st.title("📈 Finance Agents — a research team of AI analysts")
st.caption(DISCLAIMER)

with st.sidebar:
    ticker = st.text_input("Ticker", value="AAPL").upper()
    run = st.button("Run analysis", type="primary")
    st.markdown(
        "**The team**\n"
        "1. Market Analyst\n2. Fundamentals Analyst\n3. News & Sentiment\n"
        "4. Bull vs Bear debate\n5. Risk Manager\n6. Portfolio Manager"
    )
    st.caption(f"LLM: {describe_llm(get_settings())}")

if run and ticker:
    with st.status("Agents at work...", expanded=True) as status:
        result = run_pipeline(
            ticker, progress=lambda m: status.write(f"… {m}")
        )
        status.update(label="Done", state="complete")
    d = result["decision"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Decision", d["rating"])
    col2.metric("Confidence", f"{d['confidence']:.0%}")
    col3.metric("Price", result["market"]["price"])
    st.info(d["summary"])
    tabs = st.tabs(["Report", "Debate", "Raw data"])
    with tabs[0]:
        st.markdown(result["report_md"])
    with tabs[1]:
        st.subheader("🐂 Bull case")
        st.write(result["bull_case"])
        st.subheader("🐻 Bear case")
        st.write(result["bear_case"])
        st.subheader("🛡️ Risk")
        st.write(result["risk_note"])
    with tabs[2]:
        st.json(
            {
                "market": result["market"],
                "fundamentals": result["fundamentals"],
                "news": result["news"],
            }
        )
else:
    st.write("Enter a ticker in the sidebar and press **Run analysis**.")

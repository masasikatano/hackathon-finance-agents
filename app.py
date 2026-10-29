"""Streamlit UI — Finance Agents (multi-agent stock research).

Run:  streamlit run app.py
Works out of the box in mock mode (no API key). Set LLM_MODE=meta and
MODEL_API_KEY in .env to run the team on Meta's Muse Spark via the
Meta Model API.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st  # noqa: E402

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

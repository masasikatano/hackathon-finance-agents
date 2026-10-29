# 📈 Finance Agents — a research team of AI analysts

A TradingAgents-style **multi-agent stock research app** built for the
Meta Global AI Developer Hackathon (Indie Dev Track).

Enter a ticker and a team of AI agents goes to work — market analyst,
fundamentals analyst, news/sentiment analyst, a **bull vs. bear debate**,
a risk manager, and a portfolio manager who issues the final
BUY / HOLD / SELL call with a transparent reasoning trail.

> Educational demo only — not financial advice.

## Quick start

```bash
# 1) Create the project venv and install dependencies (once)
python3 -m venv .venv
.venv/bin/pip install yfinance pandas streamlit

# 2) Run the CLI demo — REAL Yahoo Finance data + mock LLM (no API key yet)
python3 run_demo.py NVDA      # US ticker
python3 run_demo.py 7203.T    # Japanese ticker (Tokyo Stock Exchange)
python3 run_demo.py           # defaults to AAPL

# Pure offline / synthetic data:
DATA_MODE=mock python3 run_demo.py NVDA

# Smoke test (mock mode, stdlib only)
python3 tests/test_pipeline_mock.py
```

`run_demo.py` defaults to `DATA_MODE=yfinance`: it fetches the real
latest price history, fundamentals and headlines via the free
[yfinance](https://pypi.org/project/yfinance/) package. If the current
interpreter lacks yfinance, the script automatically re-runs itself
with `.venv/bin/python`. If a fetch fails (network, unknown ticker),
the data layer falls back to clearly-labelled synthetic mock data —
the report's **Data:** line and the result's `used_fallback` flag
always state which source was actually used, and the **prices as of**
date shows the last trading day in the fetched series.

The technical indicator set (EMA10 / SMA50 / SMA200, RSI14, MACD,
Bollinger Bands, ATR14, 60-day support/resistance) and fundamentals
coverage (P/E, PEG, margins, ROE, FCF, …) follow the analyst coverage
of the author's earlier TradingAgents adaptation, reimplemented here
from standard formulas during the hackathon.

## Run the UI

```bash
.venv/bin/streamlit run app.py     # http://localhost:8501
```

(Verified headless on 2026-10-29: server starts and serves HTTP 200.)

## Use the real Meta Model API (Muse Spark)

1. Get an API key at [dev.meta.ai](https://dev.meta.ai) (API keys — shown once).
2. `cp .env.example .env` and set:

```
LLM_MODE=meta
MODEL_API_KEY=<your key>
META_MODEL=muse-spark-1.3
```

The Meta Model API is OpenAI-compatible (`https://api.meta.ai/v1`,
`POST /chat/completions`, Bearer auth). The client lives behind a small
provider abstraction (`src/finance_agents/llm.py`), so the endpoint,
model and provider can be swapped without touching the agents.

## Layout

```
app.py                     Streamlit UI
run_demo.py                CLI demo (real data + MockLLM by default)
src/finance_agents/
  config.py                env-based settings (.env supported)
  llm.py                   LLM providers: MockLLM + MetaModelClient
  data.py                  data providers: mock + yfinance (+ per-call fallback)
  agents.py                the 7 agent roles (one prompt each)
  pipeline.py              orchestration + Markdown report rendering
tests/test_pipeline_mock.py
BUILDLOG.md                day-by-day build log
```

## Roadmap (hackathon week)

- [x] Mock pipeline end-to-end
- [x] Real data via yfinance (full indicators, US + JP tickers, mock fallback)
- [x] Streamlit app starts (headless check)
- [ ] Live Meta Model API run with Muse Spark 1.3 (needs MODEL_API_KEY)
- [ ] Debate round 2 (bull rebuttal) + charts in the UI
- [ ] Japanese UI toggle, PDF export of the report
- [ ] Public GitHub repo + 3-minute demo video (see BUILDLOG.md)

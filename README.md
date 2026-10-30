# 📈 Finance Agents — a research team of AI analysts

A TradingAgents-style **multi-agent stock research app** built for the
Meta Global AI Developer Hackathon (Indie Dev Track).

Enter a ticker and a team of AI agents goes to work — market analyst,
fundamentals analyst, news/sentiment analyst, a **bull vs. bear debate**,
a risk manager, and a portfolio manager who issues the final
BUY / HOLD / SELL call with a transparent reasoning trail.

> Educational demo only — not financial advice.

**▶ Live app: [hackathon-finance-agents.streamlit.app](https://hackathon-finance-agents.streamlit.app/)**
(deployed on Streamlit Community Cloud from this repo, 2026-10-30;
currently runs with real Yahoo Finance data + the mock LLM until the
Meta Model API key is configured as an app secret.)

## How this project was built — a note on provenance

This project was created **entirely through conversation with Muse,
Meta's personal AI agent, on the author's iPad**. The author never
opened an IDE or a terminal for this project. Every step — verifying
the hackathon registration on Cerebral Valley, researching the Meta
Model API, designing the agent pipeline, writing and testing all of
the code in this repository, and pushing it to GitHub — was directed
by the author in chat (in Japanese) and carried out by Muse.

The author's own hands-on actions were limited to account operations
only the account holder can perform: signing in to Cerebral Valley
with Google, answering Muse's decision prompts (build the project,
defer the API-credit claim for later, publish the code on GitHub),
and creating this empty public repository — Muse's GitHub App could
not create repositories (it returned a permission error), so the
author created the repo and Muse pushed the code into it.

We document this openly because it is part of the story: this
hackathon entry was produced from an iPad, through chat alone — a
small demonstration of what an agentic assistant makes possible.

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

## Development stand-in: Groq free tier (dev only)

While the Meta Model API credits / key are pending, the pipeline can
run against a **real** LLM via [Groq](https://console.groq.com)'s free
tier, so development and prompt tuning don't have to wait:

```
LLM_MODE=groq
GROQ_API_KEY=<your free key from console.groq.com>
GROQ_MODEL=openai/gpt-oss-120b
```

**This is a development stand-in only.** The final hackathon
submission runs on **Muse Spark via the Meta Model API**
(`LLM_MODE=meta`, above). Reports produced under Groq say so honestly:
the report header and the app sidebar print
`LLM: groq (<model>) — development stand-in, not Meta Model API`.

Notes:

- Groq's API is OpenAI-compatible (`https://api.groq.com/openai/v1`),
  so it drops into the same provider abstraction; switching back to
  Meta is an env change only.
- Default model `openai/gpt-oss-120b` (strong reasoning model).
  Alternatives verified live on the author's free account
  (2026-10-30): `openai/gpt-oss-20b`, `qwen/qwen3.8-27b` — no Llama
  chat models on this tier. **The free lineup changes often** — check
  [console.groq.com](https://console.groq.com) for the current free
  list and set `GROQ_MODEL` accordingly.
- On Streamlit Cloud, set the same keys (`LLM_MODE`, `GROQ_API_KEY`,
  `GROQ_MODEL`) as app secrets instead of a `.env` file; the app maps
  secrets into the environment at startup.
- Offline test (fake transport, no network/key):
  `python3 tests/test_groq_client.py`.

## Layout

```
app.py                     Streamlit UI
run_demo.py                CLI demo (real data + MockLLM by default)
src/finance_agents/
  config.py                env-based settings (.env supported)
  llm.py                   LLM providers: MockLLM + MetaModelClient + GroqClient (dev)
  data.py                  data providers: mock + yfinance (+ per-call fallback)
  agents.py                the 7 agent roles (one prompt each)
  pipeline.py              orchestration + Markdown report rendering
tests/test_pipeline_mock.py
tests/test_groq_client.py
BUILDLOG.md                day-by-day build log
```

## Roadmap (hackathon week)

- [x] Mock pipeline end-to-end
- [x] Real data via yfinance (full indicators, US + JP tickers, mock fallback)
- [x] Streamlit app starts (headless check)
- [x] Groq free-tier provider (development stand-in; needs GROQ_API_KEY for a live run)
- [x] Live Meta Model API run with Muse Spark 1.3 (done 2026-10-30; NVDA HOLD, confidence 65%)
- [ ] Debate round 2 (bull rebuttal) + charts in the UI
- [ ] Japanese UI toggle, PDF export of the report
- [x] Public GitHub repo (this repo, published 2026-10-29)
- [ ] 3-minute demo video (see BUILDLOG.md)

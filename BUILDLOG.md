# Build Log — Finance Agents (Meta Global AI Developer Hackathon)

Submission deadline: **Nov 5, 2026 11:00 JST**. Design doc:
`~/workspace/goals/meta-global-ai-developer-hackathon/files/project-design.md`

## Development provenance

Created entirely through conversation with **Muse** (Meta's personal
AI agent) **on the author's iPad** — direction in Japanese chat; all
research, design, coding, testing and GitHub pushes by Muse. The
author personally performed only account-holder operations: Google
sign-in to Cerebral Valley, decision choices presented by Muse, and
creating the empty public GitHub repository (Muse's GitHub App
returned a permission error on repository creation). See the README's
"How this project was built" section. Recorded at the author's
request on 2026-10-29.

## Design reference (important provenance note)

The user has an earlier, pre-hackathon project —
[masasikatano/trading-agents-plugin](https://github.com/masasikatano/trading-agents-plugin)
(public) — a TradingAgents adaptation with a 9-subagent pipeline
(Technical/News/Fundamentals/Macro → Bull → Bear rebuttal →
Aggressive/Conservative/Neutral risk debate → Research Manager →
Trader → Portfolio Manager) and fetch scripts (US via yfinance;
JP via J-Quants + yfinance fill).

This hackathon repo is **built from scratch during the hackathon**; the
plugin is used as a *design reference only* — no code is copied from it.
What was aligned with it: the analyst indicator coverage in `data.py`
(EMA10/SMA50/SMA200, RSI14, MACD, Bollinger Bands, ATR14,
support/resistance; fundamentals P/E, PEG, margins, ROE, FCF), all
reimplemented here from standard formulas. Candidate future alignment
(not yet done): a bear-rebuttal round and a 3-way risk debate
(aggressive/conservative/neutral), mirroring the reference pipeline's
structure in this repo's own 7-agent design.

## 2026-10-29 (Day 0) — scaffold

- Design doc + provider abstractions (MockLLM / MetaModelClient,
  Mock / yfinance data), 7 agents, pipeline, CLI, Streamlit UI.
- Mock pipeline test passing; Meta Model API verified on paper as
  OpenAI-compatible (`https://api.meta.ai/v1`, model `muse-spark-1.3`).

## 2026-10-29 (Day 0, evening) — real data integration ✅

- Created project venv and installed deps (no system-wide installs):
  `python3 -m venv .venv && .venv/bin/pip install yfinance pandas streamlit`
  → yfinance 1.7.0, pandas 3.1.0, streamlit 1.66.1.
- Completed the yfinance path in `data.py`:
  - Price history (1y daily): last price, 1d / 3m change, EMA10,
    SMA50/200, RSI14 (Wilder), MACD + signal + histogram, Bollinger
    Bands (20d ±2σ), ATR14, 60-day support/resistance, 30d avg volume,
    `as_of` date + currency.
  - Fundamentals from Yahoo `info`: revenue growth, gross/operating/net
    margins, trailing & forward P/E, PEG, ROE, EPS, beta, debt/equity
    (converted from Yahoo's percent-style), FCF and market cap (in
    billions of the listing currency), dividend yield (Yahoo already
    reports it in percent — not ×100).
  - News: `Ticker.get_news()` returned empty in this sandbox, so news
    uses `yfinance.Search` (same Yahoo headlines); JP tickers are
    searched by company name when the ticker query returns nothing.
  - Sandbox quirk: Yahoo's API hosts stall through the sandbox egress
    proxy with yfinance's default session, so the provider builds a
    curl_cffi session (Chrome impersonation) and passes the
    environment's HTTP(S) proxy explicitly. No proxy in a normal
    environment → behaves as a plain session.
  - `FallbackDataProvider`: per-call fallback to mock data on any
    fetch error; output dicts carry `source` + `used_fallback`, and the
    report header prints the source and the prices-as-of date.
- `run_demo.py` now defaults to real data (`DATA_MODE=yfinance`) with
  MockLLM, and auto re-execs into `.venv/bin/python` when yfinance is
  not importable in the calling interpreter (path comparison must not
  resolve symlinks — venv python points at the system interpreter).
- Verified runs (2026-10-29, ~23:15 JST, Yahoo Finance data):
  - `python3 run_demo.py NVDA` → real data, prices as of 2026-10-29,
    NVDA **$213.37**, 1d −0.94%, P/E 27.0, PEG 0.26, rev growth
    +105.9% YoY (live intraday price; earlier fetch minutes before
    showed $212.86–213.26). Report saved as
    `sample-report-nvda.md` in the goal's hidden_files.
  - `python3 run_demo.py 7203.T` → real data, prices as of 2026-10-29,
    Toyota **¥3,077.0** (+0.85% on the day, the Oct 29 TSE close),
    P/E 8.8, PEG 1.56, ROE 12.4%. Report saved as
    `sample-report-7203t.md`.
  - Reports state "LLM: mock" honestly — agent prose is still the
    MockLLM's canned text until the Meta API key lands.
  - Unknown ticker (ZZZZINVALID) → clean mock fallback,
    `used_fallback=True`, no crash.
  - `tests/test_pipeline_mock.py` passes under both the system python
    and the venv python; `py_compile` clean for all modules + app.py.
  - Streamlit: `.venv/bin/streamlit run app.py --server.headless true
    --server.port 8765` started and served **HTTP 200** on
    localhost:8765 within ~2s; stopped after the check.

## 2026-10-29 (Day 0, late) — published on GitHub + provenance note ✅

- Author created the empty public repo; Muse pushed the initial
  commit (14 files, `main`) and verified the listing on GitHub.
- At the author's request, the iPad + Muse development provenance
  was documented in the README ("How this project was built") and in
  the "Development provenance" section above.

## Remaining

- [ ] **Real Meta Model API connection** — needs `MODEL_API_KEY` from
      dev.meta.ai, which follows the $150 credit claim (user deferred
      the claim on 2026-10-29). Then: `LLM_MODE=meta` run for NVDA +
      7203.T, prompt tuning, verify structured-JSON decision parsing
      against real Muse Spark output.
- [x] **GitHub public repo** — created by the author on 2026-10-29
      (the Muse GitHub App could not create repositories); Muse
      pushed the initial commit (14 files) to
      [masasikatano/hackathon-finance-agents](https://github.com/masasikatano/hackathon-finance-agents)
      and verified the files on GitHub.
- [ ] **Demo video** (3 min) — outline in the design doc §9; record
      after the live-LLM run works; keep a mock-mode take as insurance.
- [ ] Optional stretch: bear rebuttal round, 3-way risk debate,
      price chart in the UI, Japanese UI toggle, J-Quants for JP
      fundamentals (as in the reference project) if time remains.
- [ ] Submission form on Cerebral Valley — draft texts in design doc
      §10; submit by Nov 4 JST (deadline Nov 5 11:00 JST).

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

## 2026-10-29 (Day 0, late) — demo video production pack 📹

- **Narration script written** (English, 419 spoken words, timed to the
  design doc §9 outline; includes the iPad + Muse provenance
  disclosure). Stored with the goal docs as `demo-video-script.md`.
  Final narration audio is deliberately **not** generated yet — the
  script may change once the live run's ticker/decision are known.
- **Toolchain verified on the build VM:** ffmpeg/ffprobe 8.1.2
  (libx264, AAC, libass `subtitles` filter), Playwright 1.55.1 +
  Muse Chromium 155 (needs the image's WebGL policy launch args),
  Noto Sans / DejaVu / Liberation fonts for subtitles. Playwright's
  recorder component (2.3 MiB) was installed into the user cache.
  No local TTS CLI exists — narration will be produced via Muse's
  spoken-audio capability and mixed with ffmpeg.
- **Blocker found:** the hardened Chromium build rejects all loopback
  navigation (`ERR_BLOCKED_BY_LOCAL_NETWORK_ACCESS_CHECKS`), so the
  localhost Streamlit app cannot be recorded/screenshot from the
  agent environment directly (server itself verified healthy via
  curl). `file://` rendering works. Full evidence: `CAPTURE-NOTES.md`
  in the goal's `hidden_files/demo-capture-test/`.
- **Insurance capture produced:** a real mock-mode NVDA run
  (HOLD, 62%) was rendered into 6 storyboard frames (1440×900) and
  assembled into `insurance-mock-capture.mp4` (48.0 s, H.264,
  ffprobe-verified). Clearly labelled mock/storyboard — **not** the
  final demo and not live-UI screenshots.

### Demo video production checklist (final shoot)

- [ ] Run the app **live** first (`LLM_MODE=meta`, Muse Spark) for
      the chosen ticker; freeze the script's numbers to that run.
- [ ] Record the demo segment through a route that can see the app —
      a reachable deployment (e.g. Streamlit Cloud from this public
      repo, key in platform secrets, never on screen) or the parent
      agent's live-browser capture; storyboard frames from the live
      run's outputs are the emergency fallback.
- [ ] Generate the English narration from the final script (Muse
      spoken-audio), segment by segment.
- [ ] Assemble in ffmpeg: sync narration to the five segments, burn
      in English subtitles (Noto Sans), check loudness and pacing.
- [ ] Export MP4 (H.264 + AAC) at **≤ 3:00**, verify with ffprobe and
      a full watch-through; confirm no API key or account screen is
      visible anywhere.
- [ ] Upload unlisted (e.g. YouTube), paste the link into the
      Cerebral Valley submission form, keep the MP4 as a local backup.

## 2026-10-30 (Day 1, early) — deployed to Streamlit Cloud ✅

- Live app: https://hackathon-finance-agents.streamlit.app/
  (Streamlit Community Cloud, workspace masasikatano; repo
  masasikatano/hackathon-finance-agents, branch main, app.py;
  no secrets configured — mock LLM + real yfinance data).
- The author created the Streamlit account with Google and signed in
  to GitHub in the shared browser to connect it; Muse ran the
  sign-in verification (including the emailed code challenge via the
  user's Gmail) and the deploy, and verified the Finance Agents UI
  loads at the public URL.
- This also unblocks the demo-video recording route: the final take
  can be recorded against this public URL instead of localhost.

## 2026-10-30 (Day 1) — Groq provider added (development stand-in) ✅

- User approved using Groq's free tier as a **development stand-in
  only**; the final submission still runs on Muse Spark via the Meta
  Model API.
- `llm.py`: Meta/Groq now share an `OpenAICompatibleClient` base
  (injectable `transport` for offline tests; minimal, tolerant request
  params — no `n`, temperature 0.4). New `GroqClient`
  (`LLM_MODE=groq`, `GROQ_API_KEY`, base
  `https://api.groq.com/openai/v1`, `GROQ_MODEL` default
  `openai/gpt-oss-120b`). Explicit `LLM_MODE=groq` without a key fails
  loudly instead of silently falling back to mock. `describe_llm()`
  exposes the honest label for UIs.
- Honest labelling: pipeline results carry `llm_label`; the report
  header prints e.g. `LLM: groq (openai/gpt-oss-120b) — development
  stand-in, not Meta Model API`. The Streamlit sidebar shows the same
  label, and the app now maps Streamlit secrets (`LLM_MODE`,
  `GROQ_API_KEY`, `MODEL_API_KEY`, …) into env vars at startup. The
  shared disclaimer no longer claims a mock LLM unconditionally.
- `agents.py`: decision parsing hardened for real-model output —
  prose/code-fence-wrapped JSON (already first-`{`..last-`}`), rating
  validated against BUY/HOLD/SELL, confidence clamped to 0..1.
- Tests: new `tests/test_groq_client.py` (offline, fake transport)
  verifies the request URL, `Authorization: Bearer` header, model,
  tolerant params, response parsing, the stand-in label, the
  missing-key error, and fenced-JSON decision parsing. Full suite
  passes under both system and venv Python; mock CLI run unchanged
  (HOLD 62%); Streamlit headless start still serves HTTP 200.
- `.env.example` + README updated (Groq section labelled dev-only,
  with a warning that the free lineup is volatile — check
  console.groq.com; `llama-3.3-70b-versatile` reportedly left the free
  tier in Aug 2026).

## 2026-10-30 (Day 1) — Meta Model API 実接続 ✅

- $150 の無料クレジットが dev.meta.ai の画面に表示され（ユーザー確認）、
  ユーザーが API キーを発行し、安全な入力経由で Muse のコネクタ
  （custom.meta-model-api）に接続した。キー自体はリポジトリにも
  ログにも残っていない。
- モデル一覧で muse-spark-1.3 に加えて muse-wonder-1.0 の提供を
  このアカウントで初めて確認した。
- Muse Spark 1.3 は推論トークンを消費するモデルで、初回の実パイプ
  ライン実行では `max_tokens: 2048` を推論で使い切り、内容が null に
  なる事象が発生した。`llm.py` を修正し、上限を 8192 に引き上げ、
  空の場合は 16384 で1回リトライするようにした。オフラインテストは
  合格。
- 修正後に NVDA を実データ（yfinance）で実行し、成功した。判定は
  HOLD、信頼度65パーセント、価格は2026-10-29時点で213.66ドル。
  レポート見出しに LLM: meta (muse-spark-1.3) と正しく表示される。
- 残りは最終デモ動画の本撮影と Cerebral Valley への提出（締切は
  2026年11月5日11時 JST）。

## Remaining

- [ ] **Live Groq run (dev)** — the user supplies `GROQ_API_KEY` via
      secure entry (never in chat/repo), then: `LLM_MODE=groq` runs
      for NVDA + 7203.T with real data, prompt tuning against a real
      LLM's prose, and optionally the same key as a Streamlit secret.
- [x] **Real Meta Model API connection** — 2026-10-30に完了（下記の
      「2026-10-30 (Day 1) — Meta Model API 実接続」参照）。
      `LLM_MODE=meta` で NVDA の実データ実行が成功し、構造化JSONの
      判定パースも実 Muse Spark 出力で確認済み。7203.T の実行は任意。
- [x] **GitHub public repo** — created by the author on 2026-10-29
      (the Muse GitHub App could not create repositories); Muse
      pushed the initial commit (14 files) to
      [masasikatano/hackathon-finance-agents](https://github.com/masasikatano/hackathon-finance-agents)
      and verified the files on GitHub.
- [ ] **Demo video** (3 min) — script + production pack ready (see
      "Demo video production" entry above); final shoot waits for the
      live-LLM run. Insurance mock capture already produced.
- [ ] Optional stretch: bear rebuttal round, 3-way risk debate,
      price chart in the UI, Japanese UI toggle, J-Quants for JP
      fundamentals (as in the reference project) if time remains.
- [ ] Submission form on Cerebral Valley — draft texts in design doc
      §10; submit by Nov 4 JST (deadline Nov 5 11:00 JST).

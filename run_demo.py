#!/usr/bin/env python3
"""CLI entry point — runs the full agent pipeline and prints the report.

Usage:
    python3 run_demo.py [TICKER]        # default AAPL

Defaults: REAL market data (DATA_MODE=yfinance) + MockLLM (no API key
needed yet). If yfinance cannot fetch (network down, bad ticker), the
data layer falls back to clearly-labelled synthetic mock data — the
report's "Data:" line always states which source was actually used.

If yfinance is not importable in the current interpreter but the project
venv (``.venv/``) exists, this script re-executes itself with the venv
Python. Force pure mock data with ``DATA_MODE=mock python3 run_demo.py``.

Switch to the real Meta Model API by copying .env.example to .env and
setting LLM_MODE=meta + MODEL_API_KEY (see README).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Real data by default for this CLI demo. An explicit DATA_MODE in the
# shell wins (setdefault); note the CLI default is set before .env is
# loaded, so for run_demo.py it also wins over .env. Use
# `DATA_MODE=mock python3 run_demo.py` for the pure offline run.
os.environ.setdefault("DATA_MODE", "yfinance")


def _ensure_yfinance():
    """Re-exec into the project venv when yfinance is missing here."""
    if os.environ.get("DATA_MODE", "").lower() == "mock":
        return
    try:
        import yfinance  # noqa: F401
        return
    except ImportError:
        pass
    venv_python = os.path.join(os.path.dirname(__file__), ".venv", "bin", "python")
    # NOTE: compare *unresolved* paths — a venv python is a symlink to the
    # system interpreter, so realpath() would make them look identical.
    if (
        os.path.exists(venv_python)
        and os.path.abspath(venv_python) != os.path.abspath(sys.executable)
        and not os.environ.get("FINANCE_AGENTS_REEXEC")
    ):
        os.environ["FINANCE_AGENTS_REEXEC"] = "1"
        os.execv(venv_python, [venv_python, os.path.abspath(__file__), *sys.argv[1:]])
    # No venv either: continue — the data layer will fall back to mock
    # data and the report will say so.


_ensure_yfinance()

from finance_agents.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = run_pipeline(ticker, progress=lambda m: print(f"  ... {m}"))
    print()
    print(result["report_md"])


if __name__ == "__main__":
    main()

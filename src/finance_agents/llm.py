"""LLM provider abstraction.

Two providers behind one interface (`chat(system, user) -> str`):

* ``MockLLM`` — deterministic, offline, no API key. Used for development,
  tests and the demo fallback. It inspects the agent role in the system
  prompt and returns a structured, data-aware canned answer.
* ``MetaModelClient`` — Meta Model API (https://api.meta.ai/v1).
  The API is OpenAI-compatible: POST /chat/completions with
  ``Authorization: Bearer $MODEL_API_KEY``. Implemented with the standard
  library only, so the core pipeline runs anywhere; if the ``openai``
  package is installed it can be swapped in trivially (same base_url/key).

To add another provider later (OpenAI, local model, ...), implement the
same two-method protocol and register it in ``build_llm``.
"""
from __future__ import annotations

import json
import urllib.request

from .config import Settings


class MockLLM:
    """Offline stand-in that keeps the whole pipeline runnable without a key."""

    name = "mock"

    def chat(self, system: str, user: str) -> str:
        role = system.lower()
        # Order matters: debate/risk/decision prompts *mention* the other
        # roles, so match the most specific role titles first.
        if "bear researcher" in role:
            return (
                "BEAR CASE: the bull case is priced in. Valuation is rich, growth "
                "is decelerating, and any guidance miss would hit a crowded trade. "
                "The risk/reward at this level is unattractive for new money."
            )
        if "bull researcher" in role:
            return (
                "BULL CASE: trend + growth + positive sentiment align. Earnings "
                "momentum and a strong balance sheet support further upside; "
                "dips toward the 50-day average are buying opportunities."
            )
        if "risk manager" in role:
            return (
                "RISK: position size should stay moderate. Main risks: valuation "
                "compression, macro rate sensitivity, single-name concentration. "
                "Suggested guardrail: max 5% portfolio weight, stop below the "
                "50-day average."
            )
        if "portfolio manager" in role:
            return json.dumps(
                {
                    "rating": "HOLD",
                    "confidence": 0.62,
                    "summary": (
                        "Constructive trend and solid fundamentals are offset by a "
                        "rich valuation and a credible bear case. Hold existing "
                        "positions; add only on a pullback toward support."
                    ),
                }
            )
        if "market analyst" in role:
            return (
                "Price action: the ticker trades above its 50-day average with a "
                "positive 3-month trend. Momentum is constructive but not extended; "
                "volume is near its average, so there is no climax signal either way."
            )
        if "fundamentals analyst" in role:
            return (
                "Fundamentals: revenue is still growing double-digit year over year "
                "and margins are stable. Valuation is above the sector median, which "
                "leaves little margin of safety if growth slows."
            )
        if "news" in role or "sentiment" in role:
            return (
                "Sentiment: recent headlines skew mildly positive (product/AI "
                "momentum) with one cautious analyst note. Net sentiment: +0.3 "
                "on a -1..+1 scale."
            )
        return "Analysis complete."


class MetaModelClient:
    """Meta Model API client (OpenAI-compatible Chat Completions surface)."""

    name = "meta"

    def __init__(self, settings: Settings):
        if not settings.model_api_key:
            raise ValueError("MODEL_API_KEY is not set (copy .env.example to .env).")
        self.base = settings.meta_api_base.rstrip("/")
        self.model = settings.meta_model
        self.api_key = settings.model_api_key

    def chat(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.4,
        }
        req = urllib.request.Request(
            f"{self.base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


def build_llm(settings: Settings):
    """Factory: Meta client when configured, otherwise the mock."""
    if settings.use_meta:
        return MetaModelClient(settings)
    return MockLLM()

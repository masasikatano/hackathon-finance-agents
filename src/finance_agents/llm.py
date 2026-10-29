"""LLM provider abstraction.

Providers behind one interface (`chat(system, user) -> str`):

* ``MockLLM`` — deterministic, offline, no API key. Used for development,
  tests and the demo fallback. It inspects the agent role in the system
  prompt and returns a structured, data-aware canned answer.
* ``MetaModelClient`` — Meta Model API (https://api.meta.ai/v1).
  The API is OpenAI-compatible: POST /chat/completions with
  ``Authorization: Bearer $MODEL_API_KEY``. **This is the primary
  provider: the hackathon submission runs on Muse Spark via this API.**
* ``GroqClient`` — Groq (https://api.groq.com/openai/v1), also
  OpenAI-compatible. **Development stand-in ONLY** (free tier, used to
  develop and prompt-tune against a real LLM while the Meta credits /
  API key are pending). It is never presented as the Meta Model API:
  its ``label`` says so everywhere it is printed.

The HTTP providers share ``OpenAICompatibleClient`` (standard library
only, so the core pipeline runs anywhere). A ``transport`` callable can
be injected for offline tests: ``transport(url, headers, payload) ->
parsed JSON dict``.

To add another provider later, implement the same protocol and register
it in ``build_llm``.
"""
from __future__ import annotations

import json
import urllib.request

from .config import Settings


class MockLLM:
    """Offline stand-in that keeps the whole pipeline runnable without a key."""

    name = "mock"
    label = "mock"

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


def _urllib_transport(url: str, headers: dict, payload: dict) -> dict:
    """Default transport: POST JSON via urllib, return the parsed body."""
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


class OpenAICompatibleClient:
    """Shared client for OpenAI-compatible Chat Completions endpoints.

    Request parameters are deliberately minimal and tolerant: no ``n``
    (providers like Groq require n=1, the default), temperature kept
    inside the range every provider accepts.
    """

    name = "openai-compatible"
    label = "openai-compatible"

    def __init__(self, base: str, model: str, api_key: str, transport=None):
        self.base = base.rstrip("/")
        self.model = model
        self.api_key = api_key
        self._transport = transport or _urllib_transport

    def chat(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.4,
            # Reasoning models (e.g. gpt-oss) spend completion tokens on
            # hidden reasoning before the visible answer — keep headroom
            # so the structured JSON decision is not truncated.
            "max_tokens": 2048,
        }
        data = self._transport(
            f"{self.base}/chat/completions",
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                # Groq sits behind Cloudflare, which rejects the default
                # python-urllib user agent with HTTP 403 (error 1010).
                "User-Agent": "curl/8.5.0",
            },
            payload,
        )
        return data["choices"][0]["message"]["content"]


class MetaModelClient(OpenAICompatibleClient):
    """Meta Model API client (OpenAI-compatible Chat Completions surface)."""

    name = "meta"

    def __init__(self, settings: Settings, transport=None):
        if not settings.model_api_key:
            raise ValueError("MODEL_API_KEY is not set (copy .env.example to .env).")
        super().__init__(
            settings.meta_api_base,
            settings.meta_model,
            settings.model_api_key,
            transport=transport,
        )
        self.label = f"meta ({self.model})"


class GroqClient(OpenAICompatibleClient):
    """Groq client — DEVELOPMENT stand-in only, not the Meta Model API."""

    name = "groq"

    def __init__(self, settings: Settings, transport=None):
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is not set (copy .env.example to .env).")
        super().__init__(
            settings.groq_api_base,
            settings.groq_model,
            settings.groq_api_key,
            transport=transport,
        )
        self.label = (
            f"groq ({self.model}) — development stand-in, not Meta Model API"
        )


def describe_llm(settings: Settings) -> str:
    """Human label for the provider these settings would select.

    Used by UIs to show the active mode without building a client (and
    without raising when a key is missing).
    """
    if settings.llm_mode == "meta":
        if settings.model_api_key:
            return f"meta ({settings.meta_model})"
        return "mock (LLM_MODE=meta but MODEL_API_KEY is not set)"
    if settings.llm_mode == "groq":
        if settings.groq_api_key:
            return (
                f"groq ({settings.groq_model}) — development stand-in, "
                "not Meta Model API"
            )
        return "groq — not configured (GROQ_API_KEY is not set)"
    return "mock"


def build_llm(settings: Settings):
    """Factory: Meta (primary) / Groq (dev stand-in) when configured,
    otherwise the mock."""
    if settings.use_meta:
        return MetaModelClient(settings)
    if settings.llm_mode == "groq":
        # Explicit mode with no key is a configuration error — fail
        # loudly instead of silently reporting Groq while running mock.
        return GroqClient(settings)
    return MockLLM()

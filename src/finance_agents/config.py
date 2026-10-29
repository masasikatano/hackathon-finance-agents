"""Configuration loaded from environment variables.

No real credentials live in code. Copy `.env.example` to `.env` and fill in
your own Meta Model API key locally (`.env` is git-ignored).
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    # "mock" (default, offline, no key needed) or "meta" (Meta Model API)
    llm_mode: str = "mock"
    # Meta Model API — https://dev.meta.ai (dashboard / API keys)
    model_api_key: str = ""
    meta_api_base: str = "https://api.meta.ai/v1"
    meta_model: str = "muse-spark-1.3"
    # Market-data source: "mock" (default) or "yfinance"
    data_mode: str = "mock"

    @property
    def use_meta(self) -> bool:
        return self.llm_mode == "meta" and bool(self.model_api_key)


def _load_dotenv() -> None:
    """Tiny .env loader so the core pipeline has zero hard dependencies."""
    path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_settings() -> Settings:
    _load_dotenv()
    return Settings(
        llm_mode=os.getenv("LLM_MODE", "mock").lower(),
        model_api_key=os.getenv("MODEL_API_KEY", ""),
        meta_api_base=os.getenv("META_API_BASE", "https://api.meta.ai/v1"),
        meta_model=os.getenv("META_MODEL", "muse-spark-1.3"),
        data_mode=os.getenv("DATA_MODE", "mock").lower(),
    )

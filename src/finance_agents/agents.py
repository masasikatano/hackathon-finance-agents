"""The analyst team — TradingAgents-style roles, one prompt per agent.

Each agent is a thin wrapper: a system prompt (its role) + a context
builder. The pipeline orchestrates them; the LLM provider is injected.
"""
from __future__ import annotations

import json


def _ctx(payload: dict) -> str:
    return "Context (JSON):\n" + json.dumps(payload, indent=2, ensure_ascii=False)


class BaseAgent:
    role = "analyst"

    def __init__(self, llm):
        self.llm = llm

    def run(self, payload: dict) -> str:  # pragma: no cover - overridden
        raise NotImplementedError


class MarketAgent(BaseAgent):
    role = "Market Analyst"
    SYSTEM = (
        "You are a market analyst on a stock research team. Given price/trend "
        "data, write a concise technical read (trend, momentum, key levels) "
        "in under 120 words. No buy/sell recommendation."
    )

    def run(self, payload):
        return self.llm.chat(self.SYSTEM, _ctx(payload))


class FundamentalsAgent(BaseAgent):
    role = "Fundamentals Analyst"
    SYSTEM = (
        "You are a fundamentals analyst on a stock research team. Given "
        "financial metrics, assess growth, profitability, valuation vs sector "
        "and balance-sheet health in under 120 words."
    )

    def run(self, payload):
        return self.llm.chat(self.SYSTEM, _ctx(payload))


class NewsSentimentAgent(BaseAgent):
    role = "News & Sentiment Analyst"
    SYSTEM = (
        "You are a news and sentiment analyst on a stock research team. Given "
        "recent headlines, summarise the narrative and give a net sentiment "
        "score between -1 and +1, in under 100 words."
    )

    def run(self, payload):
        return self.llm.chat(self.SYSTEM, _ctx(payload))


class BullAgent(BaseAgent):
    role = "Bull Researcher"
    SYSTEM = (
        "You are a bull researcher debating an investment case. Using the "
        "team's market, fundamentals and sentiment notes, make the strongest "
        "evidence-based case FOR buying, in under 150 words."
    )

    def run(self, payload):
        return self.llm.chat(self.SYSTEM, _ctx(payload))


class BearAgent(BaseAgent):
    role = "Bear Researcher"
    SYSTEM = (
        "You are a bear researcher debating an investment case. Using the "
        "team's notes AND the bull case, make the strongest evidence-based "
        "case AGAINST buying, in under 150 words."
    )

    def run(self, payload):
        return self.llm.chat(self.SYSTEM, _ctx(payload))


class RiskAgent(BaseAgent):
    role = "Risk Manager"
    SYSTEM = (
        "You are a risk manager. Given the bull/bear debate, list the key "
        "risks and concrete guardrails (position size, invalidation level) "
        "in under 120 words. Be specific and conservative."
    )

    def run(self, payload):
        return self.llm.chat(self.SYSTEM, _ctx(payload))


class DecisionAgent(BaseAgent):
    role = "Portfolio Manager (Decision)"
    SYSTEM = (
        "You are a portfolio manager making the final call. Weigh every "
        "note and the risk assessment, then reply with ONLY a JSON object: "
        '{"rating": "BUY|HOLD|SELL", "confidence": 0.0-1.0, "summary": "..."}'
    )

    def run(self, payload) -> dict:
        raw = self.llm.chat(self.SYSTEM, _ctx(payload))
        try:
            # Models often wrap the JSON in prose or a ```json fence —
            # take everything from the first "{" to the last "}".
            start, end = raw.index("{"), raw.rindex("}") + 1
            parsed = json.loads(raw[start:end])
            rating = str(parsed.get("rating", "HOLD")).upper()
            if rating not in {"BUY", "HOLD", "SELL"}:
                rating = "HOLD"
            confidence = float(parsed.get("confidence", 0.5))
            confidence = min(1.0, max(0.0, confidence))
            return {
                "rating": rating,
                "confidence": confidence,
                "summary": str(parsed.get("summary", "")),
            }
        except Exception:
            return {"rating": "HOLD", "confidence": 0.5, "summary": raw.strip()}

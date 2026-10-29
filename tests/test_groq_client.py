"""Offline tests for the Groq provider (development stand-in).

No network, no real key: the HTTP layer is a fake transport that
captures the request and returns a canned Chat Completions response.
Run directly (`python3 tests/test_groq_client.py`) or under pytest.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from finance_agents.agents import DecisionAgent  # noqa: E402
from finance_agents.config import Settings  # noqa: E402
from finance_agents.llm import GroqClient, build_llm, describe_llm  # noqa: E402


class FakeTransport:
    """Records (url, headers, payload) and replies with canned content."""

    def __init__(self, content: str):
        self.content = content
        self.calls = []

    def __call__(self, url, headers, payload):
        self.calls.append((url, headers, payload))
        return {"choices": [{"message": {"content": self.content}}]}


def _settings() -> Settings:
    return Settings(
        llm_mode="groq",
        groq_api_key="test-key-not-real",
        groq_model="openai/gpt-oss-120b",
    )


def test_groq_request_shape_and_parsing():
    transport = FakeTransport("BULL CASE: canned answer")
    client = GroqClient(_settings(), transport=transport)
    out = client.chat("You are a bull researcher", "Context: {}")
    assert out == "BULL CASE: canned answer"

    assert len(transport.calls) == 1
    url, headers, payload = transport.calls[0]
    assert url == "https://api.groq.com/openai/v1/chat/completions"
    assert headers["Authorization"] == "Bearer test-key-not-real"
    assert headers["Content-Type"] == "application/json"
    assert payload["model"] == "openai/gpt-oss-120b"
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"
    # Tolerant parameters: Groq requires n=1 (its default — never send
    # anything else) and a temperature within (0, 2].
    assert payload.get("n", 1) == 1
    assert 0 < payload["temperature"] <= 2


def test_groq_label_and_factory():
    settings = _settings()
    client = build_llm(settings)
    assert isinstance(client, GroqClient)
    assert client.name == "groq"
    # The label must never let Groq pass as the Meta Model API.
    assert "development stand-in" in client.label
    assert "not Meta Model API" in client.label
    assert describe_llm(settings) == client.label


def test_groq_missing_key_fails_loudly():
    settings = Settings(llm_mode="groq", groq_api_key="")
    assert "not configured" in describe_llm(settings)
    try:
        build_llm(settings)
    except ValueError as exc:
        assert "GROQ_API_KEY" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("build_llm should raise without GROQ_API_KEY")


def test_decision_parsing_with_prose_and_code_fence():
    """Real models wrap JSON in prose / ```json fences — parsing must cope."""

    class StubLLM:
        name = "stub"

        def chat(self, system, user):
            return (
                "After weighing the debate, here is my decision:\n"
                "```json\n"
                '{"rating": "buy", "confidence": 1.4, '
                '"summary": "Strong momentum with acceptable risk."}\n'
                "```\n"
                "That concludes the analysis."
            )

    decision = DecisionAgent(StubLLM()).run({"ticker": "NVDA"})
    assert decision["rating"] == "BUY"          # normalised to upper case
    assert decision["confidence"] == 1.0        # clamped into 0..1
    assert decision["summary"].startswith("Strong momentum")


if __name__ == "__main__":
    test_groq_request_shape_and_parsing()
    test_groq_label_and_factory()
    test_groq_missing_key_fails_loudly()
    test_decision_parsing_with_prose_and_code_fence()
    print("OK: groq client tests passed")

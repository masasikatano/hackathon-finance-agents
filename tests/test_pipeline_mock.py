"""Smoke test: the whole pipeline must run offline in mock mode."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from finance_agents.pipeline import run_pipeline  # noqa: E402


def test_mock_pipeline_end_to_end():
    result = run_pipeline("AAPL")
    assert result["decision"]["rating"] in {"BUY", "HOLD", "SELL"}
    assert 0.0 <= result["decision"]["confidence"] <= 1.0
    assert "AAPL" in result["report_md"]
    assert result["llm"] == "mock"


if __name__ == "__main__":
    test_mock_pipeline_end_to_end()
    print("OK: mock pipeline test passed")

import json
import logging
import uuid

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_ai_call_logs_metrics_without_request_data(client, caplog, monkeypatch):
    result = {"reply": "Hello", "action": None, "args": {}}
    usage = {"input_tokens": 10, "output_tokens": 5}
    monkeypatch.setattr(
        "app.call_llm",
        lambda prompt, api_key: (json.dumps(result), usage),
    )

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/chat",
            json={
                "customer_email": "ravi.kumar@example.com",
                "message": "My phone number is +91 98480 12345",
            },
        )

    assert response.status_code == 200
    records = [record.getMessage() for record in caplog.records if "AI call request_id=" in record.getMessage()]
    assert len(records) == 1
    fields = dict(part.split("=", 1) for part in records[0].split()[2:])
    uuid.UUID(fields["request_id"])
    assert fields["model"] == "fake-support-model"
    assert float(fields["latency_ms"]) >= 0
    assert fields["input_tokens"] == "10"
    assert fields["output_tokens"] == "5"
    assert fields["estimated_cost_inr"] == "0.007500"
    assert "ravi.kumar@example.com" not in records[0]
    assert "+91 98480 12345" not in records[0]


def test_failed_ai_call_still_logs_metrics(client, caplog, monkeypatch):
    def fail_call(prompt, api_key):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr("app.call_llm", fail_call)

    with caplog.at_level(logging.INFO):
        with pytest.raises(RuntimeError, match="model unavailable"):
            client.post("/chat", json={"customer_email": "", "message": "Hello"})

    records = [record.getMessage() for record in caplog.records if "AI call request_id=" in record.getMessage()]
    assert len(records) == 1
    assert "input_tokens=unknown" in records[0]
    assert "output_tokens=unknown" in records[0]
    assert "estimated_cost_inr=unknown" in records[0]

import json

import pytest

from app import CUSTOMERS, app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_chat_returns_a_reply(client):
    response = client.post("/chat", json={"customer_email": "ravi.kumar@example.com", "message": "Hello"})
    assert response.status_code == 200
    assert "reply" in response.get_json()


def test_order_status(client):
    response = client.post("/chat", json={"customer_email": "ravi.kumar@example.com", "message": "Where is my order 10231?"})
    assert response.get_json()["action_result"] == "Shipped"


def test_unknown_order(client):
    response = client.post("/chat", json={"customer_email": "priya.s@example.com", "message": "What is the status of order 99999?"})
    assert response.get_json()["action_result"] == "Order not found"


@pytest.mark.parametrize(
    ("action", "args"),
    [
        ("issue_refund", {"order_id": "10231", "amount": 1299}),
        ("delete_customer_account", {"customer_email": "from_request"}),
    ],
)
def test_unverified_side_effect_actions_are_rejected(client, monkeypatch, action, args):
    result = {
        "reply": "The requested change is complete.",
        "action": action,
        "args": args,
    }
    monkeypatch.setattr("app.call_llm", lambda prompt, api_key: (json.dumps(result), {}))
    customers_before = CUSTOMERS.copy()

    response = client.post(
        "/chat",
        json={"customer_email": "ravi.kumar@example.com", "message": "Please make this change."},
    )

    assert response.get_json() == {
        "reply": "This request needs a verified support agent.",
        "action_result": None,
    }
    assert CUSTOMERS == customers_before

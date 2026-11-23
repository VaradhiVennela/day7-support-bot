import logging

from app import app


def test_chat_logs_exclude_customer_personal_data(caplog):
    app.config["TESTING"] = True
    with app.test_client() as client:
        with caplog.at_level(logging.INFO):
            response = client.post(
                "/chat",
                json={
                    "customer_email": "ravi.kumar@example.com",
                    "message": "My phone number is +91 98480 12345",
                },
            )

    assert response.status_code == 200
    assert "ravi.kumar@example.com" not in caplog.text
    assert "Ravi Kumar" not in caplog.text
    assert "+91 98480 12345" not in caplog.text
    assert "My phone number" not in caplog.text

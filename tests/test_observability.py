import json
import logging

from app.observability import JsonLogFormatter, reset_request_id, set_request_id


def test_json_formatter_adds_context_and_redacts_sensitive_fields():
    formatter = JsonLogFormatter(service_name="test-service", environment="test")
    record = logging.LogRecord(
        name="tests.observability",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
        func=None,
        sinfo=None,
    )
    record.event = "unit_test"
    record.api_key = "secret-value"
    record.details = {
        "authorization": "Bearer secret-value",
        "safe_field": "safe-value",
    }

    token = set_request_id("req-test")
    try:
        payload = json.loads(formatter.format(record))
    finally:
        reset_request_id(token)

    assert payload["message"] == "hello world"
    assert payload["service"] == "test-service"
    assert payload["environment"] == "test"
    assert payload["request_id"] == "req-test"
    assert payload["event"] == "unit_test"
    assert payload["api_key"] == "[REDACTED]"
    assert payload["details"]["authorization"] == "[REDACTED]"
    assert payload["details"]["safe_field"] == "safe-value"


def test_request_id_header_is_echoed(client):
    response = client.get("/health", headers={"X-Request-ID": "req-from-client"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-from-client"

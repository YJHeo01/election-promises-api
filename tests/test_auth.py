def test_answer_context_requires_authorization(client, base_payload):
    response = client.post("/answer-context", json=base_payload)

    assert response.status_code == 401


def test_answer_context_rejects_wrong_api_key(client, base_payload):
    response = client.post(
        "/answer-context",
        headers={"Authorization": "Bearer wrong-key"},
        json=base_payload,
    )

    assert response.status_code == 401


def test_answer_context_accepts_valid_api_key(client, auth_headers, base_payload):
    response = client.post("/answer-context", headers=auth_headers, json=base_payload)

    assert response.status_code == 200
    assert response.json()["status"] == "resolved"


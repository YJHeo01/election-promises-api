def _all_promises(body):
    return [
        promise
        for candidate in body["candidates"]
        for promise in candidate["promises"]
    ]


def test_transport_topic_returns_transport_chunks_only(client, auth_headers):
    response = client.post(
        "/answer-context",
        headers=auth_headers,
        json={
            "userQuestion": "제9회 지선 인천시장 후보들의 교통 공약 비교해줘",
            "topic": "교통",
        },
    )

    body = response.json()
    assert body["status"] == "resolved"
    assert {promise["category"] for promise in _all_promises(body)} == {"교통"}

    candidate_c = next(candidate for candidate in body["candidates"] if candidate["id"] == "cand_003")
    assert candidate_c["promises"] == []
    assert candidate_c["note"] == "교통 관련 공약을 찾지 못했습니다."


def test_youth_topic_returns_youth_chunks_only(client, auth_headers):
    response = client.post(
        "/answer-context",
        headers=auth_headers,
        json={
            "userQuestion": "제9회 지선 인천시장 후보 청년 공약 비교",
            "regionQuery": "인천시장",
            "topic": "청년",
        },
    )

    body = response.json()
    assert body["status"] == "resolved"
    assert {promise["category"] for promise in _all_promises(body)} == {"청년"}


def test_no_topic_returns_core_promises(client, auth_headers):
    response = client.post(
        "/answer-context",
        headers=auth_headers,
        json={"userQuestion": "제9회 지선 인천시장 후보 공약 비교"},
    )

    body = response.json()
    assert body["status"] == "resolved"
    assert {promise["category"] for promise in _all_promises(body)} == {"핵심"}


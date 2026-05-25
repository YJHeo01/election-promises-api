import pytest


@pytest.mark.parametrize(
    "question",
    [
        "제9회 지선 인천시장 후보 교통 공약 비교",
        "제9회 전국동시지방선거 인천광역시장 공약 비교",
        "2026 지방선거 인천시장 교통 공약",
    ],
)
def test_incheon_mayor_questions_are_resolved(client, auth_headers, question):
    response = client.post(
        "/answer-context",
        headers=auth_headers,
        json={"userQuestion": question, "topic": "교통"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "resolved"
    assert body["resolvedContest"]["code"] == "incheon_mayor"
    assert body["resolvedContest"]["name"] == "인천광역시장 선거"


def test_incheon_city_region_query_resolves_to_mayor(client, auth_headers):
    response = client.post(
        "/answer-context",
        headers=auth_headers,
        json={
            "userQuestion": "제9회 전국동시지방선거 공약 비교",
            "regionQuery": "인천광역시",
        },
    )

    body = response.json()
    assert body["status"] == "resolved"
    assert body["resolvedContest"]["code"] == "incheon_mayor"


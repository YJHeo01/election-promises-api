def test_ambiguous_incheon_question_returns_options(client, auth_headers):
    response = client.post(
        "/answer-context",
        headers=auth_headers,
        json={"userQuestion": "인천 후보들 공약 비교해줘"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ambiguous"
    assert body["message"] == "인천에서 어떤 선거를 비교할지 선택이 필요합니다."
    assert body["options"] == [
        {
            "label": "인천광역시장 선거",
            "value": "incheon_mayor",
            "type": "contest",
        },
        {
            "label": "인천광역시교육감 선거",
            "value": "incheon_education_superintendent",
            "type": "contest",
        },
    ]


def test_health_is_public(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_privacy_is_public(client):
    response = client.get("/privacy")

    assert response.status_code == 200
    assert "개인정보 처리방침" in response.text
    assert "제3자" in response.text


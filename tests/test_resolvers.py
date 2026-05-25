import pytest

from app.models import Candidate, Contest, Material, PromiseChunk


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


def test_incheon_mayor_resolves_to_nec_governor_when_scraped_data_exists(client, auth_headers, db_session):
    db_session.merge(
        Contest(
            id="contest_nec_governor_3280000",
            election_id="election_9_local",
            name="인천광역시 시·도지사선거",
            region="인천광역시",
            office="광역단체장",
            code="nec_governor_3280000",
        )
    )
    db_session.merge(
        Candidate(
            id="nec_100163134",
            election_id="election_9_local",
            contest_id="contest_nec_governor_3280000",
            name="유정복",
            party="국민의힘",
            candidate_number="2",
            external_id="100163134",
        )
    )
    db_session.merge(
        Material(
            id="nec_top5_100163134",
            candidate_id="nec_100163134",
            type="official_top5_promises",
            title="유정복 5대공약",
            text_extracted=True,
        )
    )
    db_session.merge(
        PromiseChunk(
            id="nec_top5_100163134_1",
            candidate_id="nec_100163134",
            material_id="nec_top5_100163134",
            category="핵심",
            title="인천시 전역을 驛세권으로 만들겠습니다",
            text="인천시민 모두가 지하철과 철도를 이용해 빠르게 이동할 수 있도록 하겠습니다.",
            chunk_index=1,
        )
    )
    db_session.commit()

    response = client.post(
        "/answer-context",
        headers=auth_headers,
        json={
            "userQuestion": "인천시장 후보들의 부동산 공약 비교해줘",
            "regionQuery": "인천시장",
            "topic": "부동산",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "resolved"
    assert body["resolvedContest"]["code"] == "nec_governor_3280000"
    assert body["resolvedContest"]["name"] == "인천광역시 시·도지사선거"

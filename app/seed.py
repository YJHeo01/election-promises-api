from datetime import date

from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import Candidate, Contest, Election, Material, PromiseChunk


def seed_database(db: Session) -> None:
    election = Election(
        id="election_9_local",
        name="제9회 전국동시지방선거",
        type="지방선거",
        election_date=date(2026, 6, 3),
        source_code="NEC_LOCAL_9",
    )
    db.merge(election)

    contests = [
        Contest(
            id="contest_incheon_mayor",
            election_id=election.id,
            name="인천광역시장 선거",
            region="인천광역시",
            office="광역단체장",
            code="incheon_mayor",
        ),
        Contest(
            id="contest_incheon_education_superintendent",
            election_id=election.id,
            name="인천광역시교육감 선거",
            region="인천광역시",
            office="교육감",
            code="incheon_education_superintendent",
        ),
    ]
    for contest in contests:
        db.merge(contest)

    candidates = [
        Candidate(
            id="cand_001",
            election_id=election.id,
            contest_id="contest_incheon_mayor",
            name="후보 A",
            party="정당 A",
            candidate_number="1",
            external_id="sample-candidate-a",
        ),
        Candidate(
            id="cand_002",
            election_id=election.id,
            contest_id="contest_incheon_mayor",
            name="후보 B",
            party="정당 B",
            candidate_number="2",
            external_id="sample-candidate-b",
        ),
        Candidate(
            id="cand_003",
            election_id=election.id,
            contest_id="contest_incheon_mayor",
            name="후보 C",
            party="정당 C",
            candidate_number="3",
            external_id="sample-candidate-c",
        ),
    ]
    for candidate in candidates:
        db.merge(candidate)

    materials = [
        Material(
            id="mat_cand_001_booklet",
            candidate_id="cand_001",
            type="official_campaign_booklet",
            title="후보 A 책자형 선거공보",
            url="https://example.com/sample/incheon-mayor-candidate-a.pdf",
            text_extracted=True,
        ),
        Material(
            id="mat_cand_002_booklet",
            candidate_id="cand_002",
            type="official_campaign_booklet",
            title="후보 B 책자형 선거공보",
            url="https://example.com/sample/incheon-mayor-candidate-b.pdf",
            text_extracted=True,
        ),
        Material(
            id="mat_cand_003_booklet",
            candidate_id="cand_003",
            type="official_campaign_booklet",
            title="후보 C 책자형 선거공보",
            url="https://example.com/sample/incheon-mayor-candidate-c.pdf",
            text_extracted=True,
        ),
    ]
    for material in materials:
        db.merge(material)

    chunks = [
        PromiseChunk(
            id="chunk_cand_001_core_001",
            candidate_id="cand_001",
            material_id="mat_cand_001_booklet",
            category="핵심",
            title="균형발전과 도시 경쟁력",
            text="인천의 원도심 균형발전과 미래 산업 기반 강화를 핵심 과제로 추진합니다.",
            page=2,
            chunk_index=1,
        ),
        PromiseChunk(
            id="chunk_cand_001_transport_001",
            candidate_id="cand_001",
            material_id="mat_cand_001_booklet",
            category="교통",
            title="광역교통망 확충",
            text="인천의 광역교통망을 확충하고 출퇴근 시간을 단축하겠습니다. GTX 연계와 환승 체계를 개선합니다.",
            page=3,
            chunk_index=2,
        ),
        PromiseChunk(
            id="chunk_cand_001_youth_001",
            candidate_id="cand_001",
            material_id="mat_cand_001_booklet",
            category="청년",
            title="청년 주거 안정",
            text="청년 월세 부담을 낮추고 취업 준비 청년을 위한 주거 지원을 확대합니다.",
            page=5,
            chunk_index=3,
        ),
        PromiseChunk(
            id="chunk_cand_002_core_001",
            candidate_id="cand_002",
            material_id="mat_cand_002_booklet",
            category="핵심",
            title="경제와 생활 인프라 개선",
            text="기업 유치와 생활 인프라 개선을 통해 시민 삶의 질을 높이겠습니다.",
            page=2,
            chunk_index=1,
        ),
        PromiseChunk(
            id="chunk_cand_002_transport_001",
            candidate_id="cand_002",
            material_id="mat_cand_002_booklet",
            category="교통",
            title="대중교통 편의 개선",
            text="버스 노선을 개편하고 도시철도 접근성을 높여 대중교통 이용 편의를 개선합니다.",
            page=4,
            chunk_index=2,
        ),
        PromiseChunk(
            id="chunk_cand_002_youth_001",
            candidate_id="cand_002",
            material_id="mat_cand_002_booklet",
            category="청년",
            title="청년 창업과 일자리",
            text="청년 창업 공간을 확대하고 지역 기업과 연계한 청년 일자리 프로그램을 운영합니다.",
            page=6,
            chunk_index=3,
        ),
        PromiseChunk(
            id="chunk_cand_003_core_001",
            candidate_id="cand_003",
            material_id="mat_cand_003_booklet",
            category="핵심",
            title="복지와 안전 중심 시정",
            text="돌봄, 의료, 안전 정책을 강화해 시민 생활의 기본을 지키겠습니다.",
            page=2,
            chunk_index=1,
        ),
        PromiseChunk(
            id="chunk_cand_003_welfare_001",
            candidate_id="cand_003",
            material_id="mat_cand_003_booklet",
            category="복지",
            title="돌봄 서비스 확대",
            text="노인, 장애인, 아동을 위한 돌봄 서비스를 확대하고 공공의료 접근성을 높입니다.",
            page=4,
            chunk_index=2,
        ),
    ]
    for chunk in chunks:
        db.merge(chunk)

    db.commit()


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
        print("Seed data inserted.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

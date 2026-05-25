from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Candidate, PromiseChunk


TOPIC_KEYWORDS: dict[str, list[str]] = {
    "교통": [
        "교통",
        "대중교통",
        "버스",
        "지하철",
        "도시철도",
        "광역철도",
        "GTX",
        "도로",
        "주차",
        "환승",
        "출퇴근",
        "공항",
        "항만",
        "교통망",
    ],
    "청년": [
        "청년",
        "취업",
        "창업",
        "일자리",
        "주거",
        "월세",
        "대학생",
        "청년지원",
    ],
    "복지": [
        "복지",
        "돌봄",
        "노인",
        "장애인",
        "아동",
        "보육",
        "의료",
        "건강",
    ],
    "교육": [
        "교육",
        "학교",
        "학생",
        "대학",
        "평생교육",
        "돌봄교실",
    ],
    "부동산": [
        "부동산",
        "주택",
        "주거",
        "아파트",
        "전세",
        "월세",
        "재개발",
        "재건축",
    ],
    "일자리": [
        "일자리",
        "고용",
        "취업",
        "창업",
        "기업",
        "산업",
        "청년일자리",
    ],
}

CORE_CATEGORIES = {"핵심", "대표공약", "주요공약"}


class PromiseSearchService:
    def __init__(self, db: Session):
        self.db = db

    def search_for_candidate(
        self,
        candidate: Candidate,
        topic: str | None,
        limit: int = 5,
    ) -> list[PromiseChunk]:
        chunks = self._list_chunks(candidate.id)

        if topic:
            keywords = self._keywords_for_topic(topic)
            matches = [chunk for chunk in chunks if self._matches_keywords(chunk, keywords)]
            return matches[:limit]

        core_chunks = [chunk for chunk in chunks if (chunk.category or "") in CORE_CATEGORIES]
        return (core_chunks or chunks)[:limit]

    def _list_chunks(self, candidate_id: str) -> list[PromiseChunk]:
        statement = (
            select(PromiseChunk)
            .options(selectinload(PromiseChunk.material))
            .where(PromiseChunk.candidate_id == candidate_id)
            .order_by(PromiseChunk.chunk_index.asc(), PromiseChunk.id.asc())
        )
        return list(self.db.scalars(statement))

    def _keywords_for_topic(self, topic: str) -> list[str]:
        normalized_topic = topic.strip()
        if normalized_topic in TOPIC_KEYWORDS:
            return TOPIC_KEYWORDS[normalized_topic]

        for key, keywords in TOPIC_KEYWORDS.items():
            if key in normalized_topic or normalized_topic in key:
                return keywords

        return [normalized_topic]

    def _matches_keywords(self, chunk: PromiseChunk, keywords: list[str]) -> bool:
        haystack = f"{chunk.category or ''} {chunk.title} {chunk.text}".casefold()
        return any(keyword.casefold() in haystack for keyword in keywords)


from dataclasses import dataclass, field
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Contest


ResolutionStatus = Literal["resolved", "ambiguous", "not_found"]


@dataclass
class ContestResolution:
    status: ResolutionStatus
    contest: Contest | None = None
    options: list[dict[str, str]] = field(default_factory=list)
    message: str | None = None


class ContestResolver:
    """Resolve region and office wording to a canonical contest row."""

    INCHON_MAYOR_CODE = "incheon_mayor"
    INCHON_EDU_CODE = "incheon_education_superintendent"

    MAYOR_HINTS = (
        "인천시장",
        "인천광역시장",
        "인천광역시시장",
        "인천광역시 시장",
        "광역시장",
    )
    CITY_REGION_HINTS = ("인천광역시", "인천시")

    def __init__(self, db: Session):
        self.db = db

    def resolve(
        self,
        election_id: str,
        region_query: str | None,
        user_question: str,
    ) -> ContestResolution:
        region_text = region_query or ""
        question_text = user_question or ""
        normalized_region = self._normalize(region_text)
        normalized_all = self._normalize(f"{region_text} {question_text}")

        if "교육감" in normalized_all:
            contest = self._get_by_code(election_id, self.INCHON_EDU_CODE)
            if contest is None:
                return ContestResolution(status="not_found", message="인천광역시교육감 선거 정보를 찾지 못했습니다.")
            return ContestResolution(status="resolved", contest=contest)

        if self._has_mayor_hint(normalized_all) or self._is_city_region_query(normalized_region):
            contest = self._get_by_code(election_id, self.INCHON_MAYOR_CODE)
            if contest is None:
                return ContestResolution(status="not_found", message="인천광역시장 선거 정보를 찾지 못했습니다.")
            return ContestResolution(status="resolved", contest=contest)

        if "인천" in normalized_all:
            return ContestResolution(
                status="ambiguous",
                options=self._incheon_options(),
                message="인천에서 어떤 선거를 비교할지 선택이 필요합니다.",
            )

        return ContestResolution(
            status="ambiguous",
            options=self._incheon_options(),
            message="비교할 선거 단위를 확정할 수 없습니다.",
        )

    def _get_by_code(self, election_id: str, code: str) -> Contest | None:
        return self.db.scalar(
            select(Contest).where(
                Contest.election_id == election_id,
                Contest.code == code,
            )
        )

    def _has_mayor_hint(self, normalized_text: str) -> bool:
        return any(self._normalize(hint) in normalized_text for hint in self.MAYOR_HINTS)

    def _is_city_region_query(self, normalized_region: str) -> bool:
        return any(self._normalize(hint) == normalized_region for hint in self.CITY_REGION_HINTS)

    def _incheon_options(self) -> list[dict[str, str]]:
        return [
            {
                "label": "인천광역시장 선거",
                "value": self.INCHON_MAYOR_CODE,
                "type": "contest",
            },
            {
                "label": "인천광역시교육감 선거",
                "value": self.INCHON_EDU_CODE,
                "type": "contest",
            },
        ]

    @staticmethod
    def _normalize(value: str) -> str:
        return value.replace(" ", "").strip()


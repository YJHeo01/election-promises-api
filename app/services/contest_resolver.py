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

    GOVERNOR_OFFICE = "광역단체장"
    LOCAL_OFFICE = "기초단체장"

    REGION_ALIASES: dict[str, tuple[str, ...]] = {
        "서울특별시": ("서울", "서울시", "서울특별시"),
        "부산광역시": ("부산", "부산시", "부산광역시"),
        "대구광역시": ("대구", "대구시", "대구광역시"),
        "인천광역시": ("인천", "인천시", "인천광역시"),
        "광주광역시": ("광주", "광주시", "광주광역시"),
        "대전광역시": ("대전", "대전시", "대전광역시"),
        "울산광역시": ("울산", "울산시", "울산광역시"),
        "세종특별자치시": ("세종", "세종시", "세종특별자치시"),
        "경기도": ("경기", "경기도"),
        "강원특별자치도": ("강원", "강원도", "강원특별자치도"),
        "충청북도": ("충북", "충청북도"),
        "충청남도": ("충남", "충청남도"),
        "전북특별자치도": ("전북", "전라북도", "전북특별자치도"),
        "전라남도": ("전남", "전라남도"),
        "경상북도": ("경북", "경상북도"),
        "경상남도": ("경남", "경상남도"),
        "제주특별자치도": ("제주", "제주도", "제주특별자치도"),
    }

    GOVERNOR_HINTS = (
        "시도지사",
        "시·도지사",
        "도지사",
        "특별시장",
        "광역시장",
        "시장",
        "광역단체장",
    )
    LOCAL_HINTS = (
        "시장",
        "구청장",
        "군수",
        "기초단체장",
        "구시군의장",
        "구·시·군의장",
        "구시군의장선거",
        "구·시·군의장선거",
        "구시군의 장",
        "구·시·군의 장",
    )

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
                return ContestResolution(status="not_found", message="교육감 선거 정보를 찾지 못했습니다.")
            return ContestResolution(status="resolved", contest=contest)

        local_resolution = self._resolve_local_contest(election_id, normalized_all)
        if local_resolution is not None:
            return local_resolution

        if self._looks_like_governor_query(normalized_region, normalized_all):
            contest = self._resolve_governor_contest(election_id, normalized_region, normalized_all)
            if contest is not None:
                return ContestResolution(status="resolved", contest=contest)
            return ContestResolution(status="not_found", message="광역단체장 선거 정보를 찾지 못했습니다.")

        if "인천" in normalized_all:
            return ContestResolution(
                status="ambiguous",
                options=self._incheon_options(election_id),
                message="인천에서 어떤 선거를 비교할지 선택이 필요합니다.",
            )

        return ContestResolution(
            status="ambiguous",
            options=self._incheon_options(election_id),
            message="비교할 선거 단위를 확정할 수 없습니다.",
        )

    def _resolve_governor_contest(
        self,
        election_id: str,
        normalized_region: str,
        normalized_all: str,
    ) -> Contest | None:
        region_name = self._find_region_name(normalized_region) or self._find_region_name(normalized_all)
        if region_name is None:
            return None

        contest = self._find_contest_by_region_and_office(
            election_id=election_id,
            region_name=region_name,
            office=self.GOVERNOR_OFFICE,
        )
        if contest is not None:
            return contest

        if region_name == "인천광역시":
            return self._get_by_codes(election_id, ("nec_governor_3280000", self.INCHON_MAYOR_CODE))
        return None

    def _resolve_local_contest(
        self,
        election_id: str,
        normalized_all: str,
    ) -> ContestResolution | None:
        if not any(self._normalize(hint) in normalized_all for hint in self.LOCAL_HINTS):
            return None

        contests = self._list_contests_by_office(election_id, self.LOCAL_OFFICE)
        matches = [
            contest
            for contest in contests
            if self._normalize(contest.region) in normalized_all
            or self._normalize(contest.name).replace(self._normalize("구·시·군의 장선거"), "") in normalized_all
        ]
        matches = self._unique_contests(matches)

        if len(matches) == 1:
            return ContestResolution(status="resolved", contest=matches[0])
        if len(matches) > 1:
            return ContestResolution(
                status="ambiguous",
                options=[self._option_from_contest(contest) for contest in matches[:20]],
                message="비교할 구·시·군의 장 선거를 하나로 확정할 수 없습니다.",
            )
        return None

    def _find_contest_by_region_and_office(
        self,
        election_id: str,
        region_name: str,
        office: str,
    ) -> Contest | None:
        normalized_region = self._normalize(region_name)
        contests = self._list_contests_by_office(election_id, office)
        matches = [
            contest
            for contest in contests
            if self._normalize(contest.region) == normalized_region
            or normalized_region in self._normalize(contest.name)
        ]
        return self._prefer_nec_contest(matches)

    def _list_contests_by_office(self, election_id: str, office: str) -> list[Contest]:
        return list(
            self.db.scalars(
                select(Contest)
                .where(
                    Contest.election_id == election_id,
                    Contest.office == office,
                )
                .order_by(Contest.name.asc(), Contest.code.asc())
            )
        )

    def _get_by_code(self, election_id: str, code: str) -> Contest | None:
        return self.db.scalar(
            select(Contest).where(
                Contest.election_id == election_id,
                Contest.code == code,
            )
        )

    def _get_by_codes(self, election_id: str, codes: tuple[str, ...]) -> Contest | None:
        for code in codes:
            contest = self._get_by_code(election_id, code)
            if contest is not None:
                return contest
        return None

    def _looks_like_governor_query(self, normalized_region: str, normalized_all: str) -> bool:
        if normalized_region and self._find_region_name(normalized_region) is not None:
            return True
        if any(self._normalize(hint) in normalized_all for hint in self.GOVERNOR_HINTS):
            return self._find_region_name(normalized_all) is not None
        return False

    def _find_region_name(self, normalized_text: str) -> str | None:
        for region_name, aliases in self.REGION_ALIASES.items():
            if any(self._normalize(alias) in normalized_text for alias in aliases):
                return region_name
        return None

    def _incheon_options(self, election_id: str) -> list[dict[str, str]]:
        governor = self._find_contest_by_region_and_office(
            election_id=election_id,
            region_name="인천광역시",
            office=self.GOVERNOR_OFFICE,
        ) or self._get_by_codes(election_id, ("nec_governor_3280000", self.INCHON_MAYOR_CODE))
        education = self._get_by_code(election_id, self.INCHON_EDU_CODE)

        options: list[dict[str, str]] = []
        if governor is not None:
            options.append(self._option_from_contest(governor))
        else:
            options.append(
                {
                    "label": "인천광역시장 선거",
                    "value": self.INCHON_MAYOR_CODE,
                    "type": "contest",
                }
            )

        if education is not None:
            options.append(self._option_from_contest(education))
        else:
            options.append(
                {
                    "label": "인천광역시교육감 선거",
                    "value": self.INCHON_EDU_CODE,
                    "type": "contest",
                }
            )
        return options

    def _option_from_contest(self, contest: Contest) -> dict[str, str]:
        return {
            "label": contest.name,
            "value": contest.code,
            "type": "contest",
        }

    def _prefer_nec_contest(self, contests: list[Contest]) -> Contest | None:
        unique = self._unique_contests(contests)
        if not unique:
            return None
        return sorted(unique, key=lambda contest: (not contest.code.startswith("nec_"), contest.code))[0]

    @staticmethod
    def _unique_contests(contests: list[Contest]) -> list[Contest]:
        seen: set[str] = set()
        unique: list[Contest] = []
        for contest in contests:
            if contest.id in seen:
                continue
            seen.add(contest.id)
            unique.append(contest)
        return unique

    @staticmethod
    def _normalize(value: str) -> str:
        return value.replace(" ", "").strip()

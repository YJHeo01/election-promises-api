from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Election


class ElectionResolver:
    """Resolve user election wording to a canonical election row."""

    MVP_ELECTION_ID = "election_9_local"
    ALIASES = (
        "제9회",
        "9회",
        "지선",
        "전국동시지방선거",
        "2026",
        "지방선거",
    )

    def __init__(self, db: Session):
        self.db = db

    def resolve(self, election_query: str | None, user_question: str) -> Election | None:
        text = f"{election_query or ''} {user_question or ''}"
        normalized = text.replace(" ", "")

        if any(alias.replace(" ", "") in normalized for alias in self.ALIASES):
            return self._get_mvp_election()

        # MVP scope is intentionally narrow. If the user asks about Incheon
        # without naming an election, default to the ninth local election and
        # let ContestResolver decide whether the contest is ambiguous.
        if "인천" in normalized:
            return self._get_mvp_election()

        return self._get_mvp_election()

    def _get_mvp_election(self) -> Election | None:
        return self.db.scalar(select(Election).where(Election.id == self.MVP_ELECTION_ID))


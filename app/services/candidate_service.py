from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Candidate


class CandidateService:
    def __init__(self, db: Session):
        self.db = db

    def list_by_contest(self, election_id: str, contest_id: str) -> list[Candidate]:
        statement = (
            select(Candidate)
            .where(
                Candidate.election_id == election_id,
                Candidate.contest_id == contest_id,
            )
            .order_by(Candidate.candidate_number.asc().nullslast(), Candidate.name.asc())
        )
        return list(self.db.scalars(statement))


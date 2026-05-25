from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Material


class MaterialService:
    """Read stored materials and provide a future hook for official fetching."""

    def __init__(self, db: Session):
        self.db = db

    def list_for_candidate(self, candidate_id: str) -> list[Material]:
        statement = select(Material).where(Material.candidate_id == candidate_id)
        return list(self.db.scalars(statement))

    async def fetch_missing_materials(self, candidate_id: str) -> list[Material]:
        # TODO: Use MaterialFetcher to download official campaign booklets or
        # promise API responses when a candidate has no stored materials.
        return self.list_for_candidate(candidate_id)


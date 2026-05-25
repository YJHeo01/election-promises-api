from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class Election(TimestampMixin, Base):
    __tablename__ = "elections"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    election_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_code: Mapped[str | None] = mapped_column(String(128), nullable=True)

    contests: Mapped[list["Contest"]] = relationship(back_populates="election")
    candidates: Mapped[list["Candidate"]] = relationship(back_populates="election")


class Contest(TimestampMixin, Base):
    __tablename__ = "contests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    election_id: Mapped[str] = mapped_column(
        ForeignKey("elections.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str] = mapped_column(String(128), nullable=False)
    office: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(128), nullable=False)

    election: Mapped[Election] = relationship(back_populates="contests")
    candidates: Mapped[list["Candidate"]] = relationship(back_populates="contest")


class Candidate(TimestampMixin, Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    election_id: Mapped[str] = mapped_column(
        ForeignKey("elections.id"),
        nullable=False,
    )
    contest_id: Mapped[str] = mapped_column(
        ForeignKey("contests.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    party: Mapped[str] = mapped_column(String(128), nullable=False)
    candidate_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    election: Mapped[Election] = relationship(back_populates="candidates")
    contest: Mapped[Contest] = relationship(back_populates="candidates")
    materials: Mapped[list["Material"]] = relationship(back_populates="candidate")
    promise_chunks: Mapped[list["PromiseChunk"]] = relationship(back_populates="candidate")


class Material(TimestampMixin, Base):
    __tablename__ = "materials"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    local_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_extracted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    candidate: Mapped[Candidate] = relationship(back_populates="materials")
    promise_chunks: Mapped[list["PromiseChunk"]] = relationship(back_populates="material")


class PromiseChunk(TimestampMixin, Base):
    __tablename__ = "promise_chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id"),
        nullable=False,
    )
    material_id: Mapped[str] = mapped_column(
        ForeignKey("materials.id"),
        nullable=False,
    )
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    candidate: Mapped[Candidate] = relationship(back_populates="promise_chunks")
    material: Mapped[Material] = relationship(back_populates="promise_chunks")

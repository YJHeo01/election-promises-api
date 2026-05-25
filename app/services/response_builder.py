from app.models import Candidate, Contest, Election, PromiseChunk
from app.schemas import (
    AmbiguousOption,
    AnswerContextResponse,
    CandidateContext,
    PromiseContext,
    PromiseSource,
    ResolvedContest,
    ResolvedElection,
)


class ResponseBuilder:
    def build_resolved(
        self,
        election: Election,
        contest: Contest,
        topic: str | None,
        candidates: list[Candidate],
        candidate_promises: dict[str, list[PromiseChunk]],
    ) -> AnswerContextResponse:
        candidate_contexts: list[CandidateContext] = []

        for candidate in candidates:
            chunks = candidate_promises.get(candidate.id, [])
            note = None
            if topic and not chunks:
                note = f"{topic} 관련 공약을 찾지 못했습니다."
            elif not topic and not chunks:
                note = "조회 가능한 핵심 공약을 찾지 못했습니다."

            candidate_contexts.append(
                CandidateContext(
                    id=candidate.id,
                    name=candidate.name,
                    party=candidate.party,
                    promises=[self._promise_from_chunk(chunk) for chunk in chunks],
                    note=note,
                )
            )

        return AnswerContextResponse(
            status="resolved",
            message="정상적으로 조회되었습니다.",
            resolvedElection=ResolvedElection(
                id=election.id,
                name=election.name,
                type=election.type,
            ),
            resolvedContest=ResolvedContest(
                code=contest.code,
                name=contest.name,
                region=contest.region,
                office=contest.office,
            ),
            topic=topic,
            candidates=candidate_contexts,
        )

    def build_ambiguous(
        self,
        message: str,
        options: list[dict[str, str]],
        topic: str | None,
    ) -> AnswerContextResponse:
        return AnswerContextResponse(
            status="ambiguous",
            message=message,
            topic=topic,
            candidates=[],
            options=[AmbiguousOption(**option) for option in options],
        )

    def build_not_found(
        self,
        message: str,
        topic: str | None,
        election: Election | None = None,
        contest: Contest | None = None,
    ) -> AnswerContextResponse:
        return AnswerContextResponse(
            status="not_found",
            message=message,
            resolvedElection=(
                ResolvedElection(id=election.id, name=election.name, type=election.type)
                if election is not None
                else None
            ),
            resolvedContest=(
                ResolvedContest(
                    code=contest.code,
                    name=contest.name,
                    region=contest.region,
                    office=contest.office,
                )
                if contest is not None
                else None
            ),
            topic=topic,
            candidates=[],
        )

    def _promise_from_chunk(self, chunk: PromiseChunk) -> PromiseContext:
        material = chunk.material
        return PromiseContext(
            title=chunk.title,
            category=chunk.category,
            text=chunk.text,
            source=PromiseSource(
                type=material.type if material else "unknown",
                title=material.title if material else "출처 정보 없음",
                url=material.url if material else None,
                page=chunk.page,
            ),
        )


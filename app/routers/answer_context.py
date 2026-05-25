import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.auth import verify_api_key
from app.database import get_db
from app.schemas import AnswerContextRequest, AnswerContextResponse
from app.services.candidate_service import CandidateService
from app.services.contest_resolver import ContestResolver
from app.services.election_resolver import ElectionResolver
from app.services.promise_search_service import PromiseSearchService
from app.services.response_builder import ResponseBuilder


logger = logging.getLogger(__name__)
router = APIRouter(tags=["promise-context"])


@router.post(
    "/answer-context",
    response_model=AnswerContextResponse,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    operation_id="getPromiseContext",
    summary="Return official-material context for a Custom GPT answer",
    dependencies=[Depends(verify_api_key)],
    openapi_extra={"x-openai-isConsequential": False},
)
def get_promise_context(
    payload: AnswerContextRequest,
    db: Session = Depends(get_db),
) -> AnswerContextResponse | JSONResponse:
    builder = ResponseBuilder()

    try:
        election = ElectionResolver(db).resolve(payload.election_query, payload.user_question)
        if election is None:
            return builder.build_not_found("선거 정보를 찾지 못했습니다.", payload.topic)

        contest_resolution = ContestResolver(db).resolve(
            election_id=election.id,
            region_query=payload.region_query,
            user_question=payload.user_question,
        )
        if contest_resolution.status == "ambiguous":
            return builder.build_ambiguous(
                contest_resolution.message or "선거 단위 선택이 필요합니다.",
                contest_resolution.options,
                payload.topic,
            )
        if contest_resolution.status == "not_found" or contest_resolution.contest is None:
            return builder.build_not_found(
                contest_resolution.message or "선거 단위 정보를 찾지 못했습니다.",
                payload.topic,
                election=election,
            )

        contest = contest_resolution.contest
        candidates = CandidateService(db).list_by_contest(election.id, contest.id)
        if not candidates:
            return builder.build_not_found(
                "해당 선거 단위의 후보자 정보를 찾지 못했습니다.",
                payload.topic,
                election=election,
                contest=contest,
            )

        promise_search = PromiseSearchService(db)
        candidate_promises = {
            candidate.id: promise_search.search_for_candidate(candidate, payload.topic)
            for candidate in candidates
        }

        return builder.build_resolved(
            election=election,
            contest=contest,
            topic=payload.topic,
            candidates=candidates,
            candidate_promises=candidate_promises,
        )
    except Exception:
        logger.exception("Failed to build answer context.")
        response = AnswerContextResponse(
            status="error",
            message="서버 내부 오류가 발생했습니다.",
            topic=payload.topic,
            candidates=[],
        )
        return JSONResponse(
            status_code=500,
            content=response.model_dump(by_alias=True, exclude_none=True),
        )

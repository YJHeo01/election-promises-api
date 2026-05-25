from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AnswerStatus = Literal["resolved", "ambiguous", "not_found", "error"]


class AnswerContextRequest(BaseModel):
    user_question: str = Field(
        ...,
        alias="userQuestion",
        description="사용자의 원문 질문 전체입니다.",
        examples=["제9회 지선 인천시장 후보들의 교통 공약 비교해줘"],
    )
    election_query: str | None = Field(
        default=None,
        alias="electionQuery",
        description="사용자가 지정한 선거명 또는 선거 검색어입니다.",
        examples=["제9회 전국동시지방선거"],
    )
    region_query: str | None = Field(
        default=None,
        alias="regionQuery",
        description="사용자가 지정한 지역 또는 선거 단위 검색어입니다.",
        examples=["인천시장"],
    )
    topic: str | None = Field(
        default=None,
        description="비교할 공약 주제입니다.",
        examples=["교통"],
    )
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "userQuestion": "제9회 지선 인천시장 후보들의 교통 공약 비교해줘",
                    "electionQuery": "제9회 전국동시지방선거",
                    "regionQuery": "인천시장",
                    "topic": "교통",
                }
            ]
        },
    )


class ResolvedElection(BaseModel):
    id: str = Field(..., description="서버 내부 선거 ID입니다.", examples=["election_9_local"])
    name: str = Field(..., description="확정된 선거명입니다.", examples=["제9회 전국동시지방선거"])
    type: str = Field(..., description="선거 유형입니다.", examples=["지방선거"])


class ResolvedContest(BaseModel):
    code: str = Field(..., description="확정된 선거 단위 코드입니다.", examples=["incheon_mayor"])
    name: str = Field(..., description="확정된 선거 단위명입니다.", examples=["인천광역시장 선거"])
    region: str = Field(..., description="선거 지역입니다.", examples=["인천광역시"])
    office: str = Field(..., description="선출 직위 또는 선거 분류입니다.", examples=["광역단체장"])


class PromiseSource(BaseModel):
    type: str = Field(..., description="공약 자료 유형입니다.", examples=["official_campaign_booklet"])
    title: str = Field(..., description="공약 자료 제목입니다.", examples=["책자형 선거공보"])
    url: str | None = Field(default=None, description="공식 자료 URL입니다.")
    page: int | None = Field(default=None, description="공약이 확인된 페이지입니다.", examples=[3])


class PromiseContext(BaseModel):
    title: str = Field(..., description="공약 제목 또는 chunk 제목입니다.")
    category: str | None = Field(default=None, description="공약 분류입니다.", examples=["교통"])
    text: str = Field(..., description="공식 자료에서 추출한 공약 원문 또는 관련 문단입니다.")
    source: PromiseSource = Field(..., description="공약 출처 정보입니다.")


class CandidateContext(BaseModel):
    id: str = Field(..., description="서버 내부 후보자 ID입니다.")
    name: str = Field(..., description="후보자명입니다.", examples=["후보 A"])
    party: str = Field(..., description="정당명입니다.", examples=["정당 A"])
    promises: list[PromiseContext] = Field(default_factory=list, description="후보자별 관련 공약 목록입니다.")
    note: str | None = Field(default=None, description="자료 부재 또는 주제 불일치 안내입니다.")


class AmbiguousOption(BaseModel):
    label: str = Field(..., description="사용자에게 보여줄 선택지 이름입니다.")
    value: str = Field(..., description="선택지 값입니다.")
    type: str = Field(..., description="선택지 유형입니다.", examples=["contest"])


class AnswerContextResponse(BaseModel):
    status: AnswerStatus = Field(..., description="자료 조회 상태입니다.")
    message: str = Field(..., description="상태 설명 메시지입니다.")
    resolved_election: ResolvedElection | None = Field(
        default=None,
        alias="resolvedElection",
        description="확정된 선거 정보입니다.",
    )
    resolved_contest: ResolvedContest | None = Field(
        default=None,
        alias="resolvedContest",
        description="확정된 선거 단위 정보입니다.",
    )
    topic: str | None = Field(default=None, description="적용된 공약 주제 필터입니다.")
    candidates: list[CandidateContext] = Field(default_factory=list, description="후보자별 공약 context입니다.")
    options: list[AmbiguousOption] | None = Field(default=None, description="ambiguous 상태일 때 가능한 선택지입니다.")

    model_config = ConfigDict(populate_by_name=True)

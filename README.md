# 선거 공약 비교 Custom GPT 백엔드

Custom GPT Action 호출을 받아 선거, 선거 단위, 후보자, 공약 자료를 서버에서 확정하고, 답변 생성에 필요한 공식 자료 기반 context를 JSON으로 반환하는 FastAPI 서버입니다.

서버는 OpenAI API를 호출하지 않습니다. 후보자명, 정당명, 공약 내용은 DB 또는 향후 연결될 공식 자료 수집 어댑터에서만 반환하도록 설계되어 있습니다.

## MVP 범위

- 제9회 전국동시지방선거
- 인천광역시장 선거
- 샘플 후보자 및 샘플 공약 chunk
- 중앙선관위/공공데이터포털 실제 연동은 `OfficialElectionApiClient`, `MaterialFetcher`, `TextExtractor`에 TODO 인터페이스로 준비

## 설치 및 실행

### macOS/Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.seed
uvicorn app.main:app --reload
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m app.seed
uvicorn app.main:app --reload
```

기본 서버 주소는 `http://localhost:8000`입니다.

## 환경변수

`.env` 파일을 생성하고 다음 값을 설정합니다.

```env
CUSTOM_GPT_API_KEY=change-me
DATABASE_URL=sqlite:///./election_promises.db
PUBLIC_BASE_URL=https://gong-yak.sk14cj.dev
```

`CUSTOM_GPT_API_KEY`는 Custom GPT Action에서 보낼 Bearer 토큰입니다. 운영 환경에서는 충분히 긴 임의 문자열을 사용하세요.
`PUBLIC_BASE_URL`은 OpenAPI `servers`에 들어가는 공개 HTTPS 주소입니다. Custom GPT Actions가 이 주소를 기준으로 API를 호출합니다.

Windows에서 프로젝트가 OneDrive 같은 동기화 폴더 안에 있고 SQLite가 `disk I/O error`를 내면, `.env`의 DB 경로를 동기화되지 않는 로컬 경로로 바꿔 실행하세요.

```env
DATABASE_URL=sqlite:///C:/Users/Public/Documents/ESTsoft/CreatorTemp/election_promises_runtime.db
```

예시 생성 방법:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## DB 초기화 및 seed

```bash
python -m app.seed
```

이 명령은 SQLite 테이블을 생성하고 다음 샘플 데이터를 삽입합니다.

OneDrive 경로에서 SQLite I/O 문제가 나는 Windows 환경에서는 `.env`에 로컬 DB 경로를 먼저 지정한 뒤 같은 명령을 실행하면 됩니다.

- 제9회 전국동시지방선거
- 인천광역시장 선거
- 인천광역시교육감 선거 선택지
- 인천광역시장 후보 샘플 3명
- 후보자별 핵심, 교통, 청년, 복지 공약 chunk 샘플

## 주요 API

### `GET /health`

인증 없이 접근 가능합니다.

```json
{
  "status": "ok"
}
```

### `GET /privacy`

Custom GPT Action 설정의 개인정보 처리방침 URL로 사용할 수 있습니다. 수집 정보, 수집 목적, 수집하지 않는 정보, 제3자 판매 없음, 로그 보관 목적을 안내합니다.

### `POST /answer-context`

Custom GPT Action에서 호출하는 메인 API입니다. `operationId`는 `getPromiseContext`입니다.

인증 헤더:

```http
Authorization: Bearer <CUSTOM_GPT_API_KEY>
```

요청 예시:

```bash
curl -X POST "http://localhost:8000/answer-context" \
  -H "Authorization: Bearer change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "userQuestion": "제9회 지선 인천시장 후보들의 교통 공약 비교해줘",
    "electionQuery": "제9회 전국동시지방선거",
    "regionQuery": "인천시장",
    "topic": "교통"
  }'
```

응답 예시:

```json
{
  "status": "resolved",
  "message": "정상적으로 조회되었습니다.",
  "resolvedElection": {
    "id": "election_9_local",
    "name": "제9회 전국동시지방선거",
    "type": "지방선거"
  },
  "resolvedContest": {
    "code": "incheon_mayor",
    "name": "인천광역시장 선거",
    "region": "인천광역시",
    "office": "광역단체장"
  },
  "topic": "교통",
  "candidates": [
    {
      "id": "cand_001",
      "name": "후보 A",
      "party": "정당 A",
      "promises": [
        {
          "title": "광역교통망 확충",
          "category": "교통",
          "text": "인천의 광역교통망을 확충하고 출퇴근 시간을 단축하겠습니다. GTX 연계와 환승 체계를 개선합니다.",
          "source": {
            "type": "official_campaign_booklet",
            "title": "후보 A 책자형 선거공보",
            "url": "https://example.com/sample/incheon-mayor-candidate-a.pdf",
            "page": 3
          }
        }
      ],
      "note": null
    }
  ],
  "options": null
}
```

## Custom GPT Action 연동

1. 서버를 배포하고 공개 HTTPS URL을 준비합니다.
2. `.env`의 `CUSTOM_GPT_API_KEY`를 긴 임의 문자열로 설정합니다.
3. Custom GPT의 Actions 설정에서 OpenAPI schema URL에 `https://your-domain/openapi.json`을 입력합니다.
4. 인증 방식은 API Key, Auth Type은 Bearer로 설정합니다.
5. Privacy policy URL에 `https://your-domain/privacy`를 입력합니다.
6. GPT 지침에는 후보자나 공약을 추측하지 말고 `/answer-context` 응답의 JSON만 근거로 답변하라고 명시합니다.

## 테스트

```bash
pytest
```

테스트 범위:

- Authorization 헤더 누락 및 잘못된 API Key 401
- 올바른 API Key 요청 성공
- 인천시장 관련 표현 resolve
- 교통/청년 topic 검색
- topic이 없을 때 핵심 공약 반환
- "인천 후보들"처럼 선거 단위가 불분명한 요청의 ambiguous 처리

## 현재 MVP 제한사항

- 후보자명, 정당명, 공약 자료는 실제 공식 데이터가 아니라 교체 가능한 샘플 데이터입니다.
- 중앙선관위 또는 공공데이터포털 API는 아직 연결하지 않았습니다.
- PDF 다운로드와 텍스트 추출 구조는 준비되어 있지만 자동 수집 파이프라인은 구현 전입니다.
- 검색은 SQLite에 저장된 chunk에 대한 키워드 기반 필터입니다.
- 서버는 최종 답변 문장을 생성하지 않고 Custom GPT가 사용할 구조화 JSON만 반환합니다.

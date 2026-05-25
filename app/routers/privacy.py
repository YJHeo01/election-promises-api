from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter(tags=["system"])

PRIVACY_POLICY_HTML = """<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="canonical" href="https://gong-yak.sk14cj.dev/privacy">
    <title>개인정보 처리방침 | 공약 비교 AI 에이전트</title>
    <style>
      :root {
        color-scheme: light;
        font-family:
          -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans KR",
          "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
        line-height: 1.65;
        color: #18212f;
        background: #f6f8fb;
      }

      body {
        margin: 0;
      }

      main {
        box-sizing: border-box;
        width: min(860px, 100%);
        margin: 0 auto;
        padding: 56px 22px 72px;
      }

      article {
        background: #ffffff;
        border: 1px solid #d9e0ea;
        border-radius: 8px;
        padding: clamp(28px, 5vw, 52px);
        box-shadow: 0 18px 42px rgba(24, 33, 47, 0.08);
      }

      h1, h2 {
        line-height: 1.25;
        letter-spacing: 0;
      }

      h1 {
        margin: 0 0 10px;
        font-size: clamp(2rem, 4vw, 2.8rem);
      }

      h2 {
        margin: 34px 0 12px;
        font-size: 1.18rem;
      }

      p {
        margin: 0 0 14px;
      }

      ul {
        margin: 0 0 16px;
        padding-left: 1.25rem;
      }

      li + li {
        margin-top: 8px;
      }

      .meta {
        margin-bottom: 28px;
        color: #526173;
        font-size: 0.96rem;
      }

      .notice {
        padding: 16px 18px;
        border-left: 4px solid #2563eb;
        background: #eef5ff;
        color: #23354d;
      }

      a {
        color: #1d4ed8;
      }
    </style>
  </head>
  <body>
    <main>
      <article>
        <h1>개인정보 처리방침</h1>
        <p class="meta">공약 비교 AI 에이전트 | 시행일: 2026년 5월 25일</p>

        <p class="notice">
          이 페이지는 Custom GPT 배포를 위해 제공되는 개인정보 처리방침이며,
          공개 URL은 <a href="https://gong-yak.sk14cj.dev/privacy">https://gong-yak.sk14cj.dev/privacy</a>입니다.
        </p>

        <h2>1. 서비스 개요</h2>
        <p>
          공약 비교 AI 에이전트는 사용자가 Custom GPT에 입력한 선거, 지역, 후보자,
          공약 주제 관련 질문을 바탕으로 공식 자료 기반의 공약 정보를 조회해
          구조화된 참고 정보를 반환하는 API입니다. 이 서버는 최종 답변 문장을
          직접 생성하지 않으며, OpenAI API를 별도로 호출하지 않습니다.
        </p>

        <h2>2. 처리하는 정보</h2>
        <ul>
          <li>사용자가 입력한 질문 내용과 선거명, 지역명, 공약 주제 등 요청 파라미터</li>
          <li>API 요청 처리 과정에서 생성될 수 있는 접속 로그, 요청 시각, 요청 경로, 오류 로그</li>
          <li>서버 운영 환경에 따라 기록될 수 있는 IP 주소, User-Agent 등 기본 기술 정보</li>
        </ul>
        <p>
          주민등록번호, 결제 정보, 연락처, 계정 비밀번호, 정밀 위치정보 등 민감하거나
          불필요한 개인식별 정보는 의도적으로 요청하거나 수집하지 않습니다.
        </p>

        <h2>3. 이용 목적</h2>
        <ul>
          <li>사용자 질문에 맞는 선거, 선거 단위, 후보자, 공약 자료 조회</li>
          <li>Custom GPT Action API 인증, 오남용 방지, 보안 점검</li>
          <li>오류 분석, 서비스 안정성 개선, 운영 상태 확인</li>
        </ul>

        <h2>4. 보관 및 삭제</h2>
        <p>
          애플리케이션 자체는 사용자 질문 본문이나 응답 결과를 별도 회원 데이터베이스에
          저장하지 않습니다. 다만 서버 접속 로그와 오류 로그는 보안 점검, 장애 대응,
          운영 안정성 확보를 위해 호스팅 및 서버 운영 환경의 정책에 따라 제한적으로
          보관될 수 있으며, 목적 달성 후 삭제 또는 익명화됩니다.
        </p>

        <h2>5. 제3자 제공 및 외부 서비스</h2>
        <p>
          수집한 정보를 판매하지 않으며, 광고 목적의 제3자 제공을 하지 않습니다.
          Custom GPT Actions를 통한 요청 전달 과정에는 OpenAI의 서비스가 관여할 수 있고,
          서버 운영에는 호스팅, 보안, 로그 관리 인프라가 사용될 수 있습니다. 각 외부
          서비스에서 처리되는 정보는 해당 서비스의 개인정보 처리방침과 약관이 적용됩니다.
        </p>

        <h2>6. 안전성 확보 조치</h2>
        <ul>
          <li>공개 배포 환경에서 HTTPS 사용</li>
          <li>Custom GPT Action 호출을 위한 Bearer 토큰 기반 인증</li>
          <li>필요 최소한의 요청 정보 처리와 불필요한 개인정보 입력 지양</li>
          <li>오류 및 보안 점검을 위한 운영 로그 관리</li>
        </ul>

        <h2>7. 이용자 권리</h2>
        <p>
          이용자는 개인정보 처리와 관련해 열람, 정정, 삭제, 처리정지를 요청할 수 있습니다.
          이 서비스는 별도 회원 계정을 운영하지 않으므로 특정 이용자를 식별하기 어려울 수
          있으며, 요청 처리를 위해 필요한 범위의 추가 확인이 이루어질 수 있습니다.
        </p>

        <h2>8. 문의</h2>
        <p>
          개인정보 관련 문의는 Custom GPT 배포자에게 요청하거나, 배포 페이지에 표시된
          연락 수단을 이용해 주십시오. 서비스 운영자는 문의 접수 후 합리적인 범위에서
          필요한 조치를 안내합니다.
        </p>

        <h2>9. 변경</h2>
        <p>
          본 개인정보 처리방침은 서비스 구조, 운영 환경, 관련 법령 또는 정책 변경에 따라
          수정될 수 있습니다. 변경 사항은 이 페이지를 통해 공지합니다.
        </p>
      </article>
    </main>
  </body>
</html>
"""


@router.get("/privacy", response_class=HTMLResponse, summary="Privacy policy")
def privacy_policy() -> str:
    return PRIVACY_POLICY_HTML

from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter(tags=["system"])


@router.get("/privacy", response_class=HTMLResponse, summary="Privacy policy")
def privacy_policy() -> str:
    return """
    <!doctype html>
    <html lang="ko">
      <head>
        <meta charset="utf-8">
        <title>개인정보 처리방침</title>
      </head>
      <body>
        <h1>개인정보 처리방침</h1>
        <p>이 서버는 사용자가 입력한 선거, 지역, 공약 관련 질문을 처리합니다.</p>
        <p>수집 목적은 선거구 식별, 후보자 조회, 공약 자료 조회입니다.</p>
        <p>주민등록번호, 연락처, 결제 정보 등 민감한 개인식별 정보는 수집하지 않습니다.</p>
        <p>수집한 정보를 제3자에게 판매하지 않습니다.</p>
        <p>서버 로그는 오류 분석 및 보안 점검 목적으로 보관될 수 있습니다.</p>
      </body>
    </html>
    """


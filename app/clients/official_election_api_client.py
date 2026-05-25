import httpx


class OfficialElectionApiClient:
    """Future adapter for National Election Commission or public data APIs."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = base_url
        self.api_key = api_key

    async def fetch_candidates(self, election_id: str, contest_code: str):
        # TODO: 중앙선관위 또는 공공데이터포털 API 연동
        raise NotImplementedError

    async def fetch_candidate_materials(self, election_id: str, contest_code: str, candidate_id: str):
        # TODO: 후보자별 공보물, 5대 공약, 정책 자료 API 연동
        raise NotImplementedError

    async def _get_json(self, path: str, params: dict[str, str] | None = None):
        if not self.base_url:
            raise RuntimeError("Official election API base URL is not configured.")

        async with httpx.AsyncClient(base_url=self.base_url, timeout=20.0) as client:
            response = await client.get(path, params=params)
            response.raise_for_status()
            return response.json()


from pathlib import Path

import httpx


class MaterialFetcher:
    """Download official material files when official URLs are available."""

    async def fetch_bytes(self, url: str) -> bytes:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    async def fetch_to_file(self, url: str, destination: Path) -> Path:
        # TODO: Add checksum validation and source allow-listing when real
        # official endpoints are connected.
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(await self.fetch_bytes(url))
        return destination


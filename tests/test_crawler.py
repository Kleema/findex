import pytest
import httpx
import asyncio
from findex.crawler import canonicalize, RobotsCache

def test_canonicalize():
    assert canonicalize("HTTPS://Example.com/Path?b=2&a=1#fragment") == "https://example.com/Path?a=1&b=2"
    assert canonicalize("http://test.com") == "http://test.com/"

@pytest.mark.asyncio
async def test_robots_cache():
    def mock_handler(request: httpx.Request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /private\n")
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        cache = RobotsCache(client)
        assert await cache.can_fetch("Bot", "http://test.com/public") == True
        assert await cache.can_fetch("Bot", "http://test.com/private") == False
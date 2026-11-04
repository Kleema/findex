import asyncio
import logging
import random
import time
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, urljoin
from urllib.robotparser import RobotFileParser
from typing import AsyncGenerator

import httpx
from selectolax.lexbor import LexborHTMLParser

logger = logging.getLogger(__name__)


def canonicalize(url: str) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    if not path.startswith("/"):
        path = "/" + path
    query = urlencode(sorted(parse_qsl(parsed.query)))
    return urlunparse((scheme, netloc, path, "", query, ""))


class RobotsCache:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.cache: dict[str, RobotFileParser | None] = {}

    async def can_fetch(self, user_agent: str, url: str) -> bool:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        if robots_url not in self.cache:
            try:
                resp = await self.client.get(robots_url, timeout=5.0)
                if resp.status_code == 200:
                    parser = RobotFileParser()
                    parser.set_url(robots_url)
                    parser.parse(resp.text.splitlines())
                    self.cache[robots_url] = parser
                else:
                    self.cache[robots_url] = None
            except Exception:
                self.cache[robots_url] = None

        parser = self.cache[robots_url]
        if parser is None:
            return True
        return parser.can_fetch(user_agent, url)


async def fetch_with_retry(
        client: httpx.AsyncClient,
        url: str,
        global_sem: asyncio.Semaphore,
        host_sem: asyncio.Semaphore,
        host_last_req: dict[str, float]
) -> httpx.Response | None:
    max_retries = 3
    base_delay = 1.0
    netloc = urlparse(url).netloc

    for attempt in range(max_retries):
        async with global_sem:
            async with host_sem:
                now = time.monotonic()
                time_since_last = now - host_last_req.get(netloc, 0.0)
                if time_since_last < 1.0:
                    await asyncio.sleep(1.0 - time_since_last)

                try:
                    async with asyncio.timeout(10.0):
                        response = await client.get(url, follow_redirects=True)
                        host_last_req[netloc] = time.monotonic()

                    if response.status_code == 429 or response.status_code >= 500:
                        retry_after = response.headers.get("Retry-After")
                        delay = int(retry_after) if retry_after and retry_after.isdigit() else (
                                    base_delay * (2 ** attempt) + random.uniform(0, 1))
                        logger.warning(f"Status {response.status_code} for {url}. Retry in {delay:.2f}s")
                        await asyncio.sleep(delay)
                        continue

                    response.raise_for_status()
                    return response

                except (httpx.RequestError, asyncio.TimeoutError) as e:
                    logger.warning(f"Error/Timeout on {url}: {e}")
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(delay)
                    continue
                except httpx.HTTPStatusError as e:
                    if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                        logger.error(f"Client error {e.response.status_code} for {url}. Skipping.")
                        return None
    return None


async def crawl(start_url: str, max_pages: int, concurrency: int = 5) -> AsyncGenerator[dict[str, str | int], None]:
    user_agent = "FindexCrawler/1.0 (contact: admin@example.com)"
    headers = {"User-Agent": user_agent}

    url_queue: asyncio.Queue[str] = asyncio.Queue()
    results_queue: asyncio.Queue[dict[str, str | int] | Exception] = asyncio.Queue()
    seen = {canonicalize(start_url)}
    await url_queue.put(canonicalize(start_url))

    global_sem = asyncio.Semaphore(concurrency)
    host_sems: dict[str, asyncio.Semaphore] = {}
    host_last_req: dict[str, float] = {}

    active_tasks = 0
    pages_collected = 0

    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        robots = RobotsCache(client)

        async def worker():
            nonlocal active_tasks
            while True:
                url = await url_queue.get()
                active_tasks += 1
                try:
                    if not await robots.can_fetch(user_agent, url):
                        continue

                    netloc = urlparse(url).netloc
                    if netloc not in host_sems:
                        host_sems[netloc] = asyncio.Semaphore(2)

                    resp = await fetch_with_retry(client, url, global_sem, host_sems[netloc], host_last_req)

                    if resp and "text/html" in resp.headers.get("content-type", ""):
                        html = LexborHTMLParser(resp.text)
                        text = html.css_first("body").text(separator=" ", strip=True) if html.css_first("body") else ""

                        await results_queue.put({
                            "url": url,
                            "text": text,
                            "queue_size": url_queue.qsize(),
                            "active": active_tasks
                        })

                        for node in html.css("a[href]"):
                            href = node.attributes.get("href")
                            if href:
                                next_url = canonicalize(urljoin(url, href))
                                if next_url.startswith("http") and next_url not in seen:
                                    seen.add(next_url)
                                    await url_queue.put(next_url)
                except Exception as e:
                    logger.error(f"Worker error on {url}: {e}")
                finally:
                    active_tasks -= 1
                    url_queue.task_done()

        async with asyncio.TaskGroup() as tg:
            workers = [tg.create_task(worker()) for _ in range(concurrency)]

            while pages_collected < max_pages:
                if url_queue.empty() and active_tasks == 0 and results_queue.empty():
                    break

                try:
                    result = await asyncio.wait_for(results_queue.get(), timeout=1.0)
                    if isinstance(result, Exception):
                        continue
                    pages_collected += 1
                    yield result
                except asyncio.TimeoutError:
                    continue

            for w in workers:
                w.cancel()
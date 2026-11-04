import asyncio
import time
import os
import psutil
from findex.crawler import crawl


async def run_benchmark():
    start_url = "https://example.com"  # Змініть на свій дозволений сайт (наприклад uk.wikipedia.org)
    max_pages = 20
    concurrencies = [1, 5, 20]

    print("| Concurrency | Wall Time (s) | Pages/sec | RSS Peak (MB) |")
    print("|-------------|---------------|-----------|---------------|")

    for c in concurrencies:
        process = psutil.Process(os.getpid())
        t0 = time.perf_counter()

        count = 0
        async for _ in crawl(start_url, max_pages, concurrency=c):
            count += 1

        t1 = time.perf_counter()
        wall_time = t1 - t0
        rate = count / wall_time if wall_time > 0 else 0
        rss = process.memory_info().rss / (1024 * 1024)

        print(f"| {c:<11} | {wall_time:<13.2f} | {rate:<9.2f} | {rss:<13.2f} |")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
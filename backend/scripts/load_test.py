"""
Concurrent Load Testing Script for Resume Roast (Operational Readiness Section 1.3).
Simulates bursts of concurrent traffic against the roast and API endpoints to benchmark
latency, throughput, connection pooling, and error rates before launch.

Usage:
    python backend/scripts/load_test.py --concurrency 5 --requests 20 --url http://localhost:8000
    python backend/scripts/load_test.py --concurrency 10 --requests 50
"""
from __future__ import annotations

import argparse
import asyncio
import io
import time
from typing import List

import httpx

DUMMY_RESUME = """
Jane Doe
Senior Full Stack Engineer | jane@example.com | San Francisco, CA

PROFESSIONAL EXPERIENCE
Senior Software Engineer - TechCorp Inc. (2022 - Present)
- Responsible for building and maintaining microservices and web applications
- Collaborated across teams to optimize database queries and reduce bottlenecks
- Worked with modern technologies including Python, React, and PostgreSQL
- Synergized with product stakeholders to accelerate quarterly business outcomes

Software Engineer - Startup Labs (2020 - 2022)
- Built user-facing features using React, TypeScript, and Node.js
- Helped scale the core API infrastructure to handle growing customer traffic
- Fixed critical bugs and improved automated test coverage across services

EDUCATION & SKILLS
B.S. in Computer Science - State University (2020)
Skills: Python, TypeScript, React, PostgreSQL, Docker, FastAPI, Git
"""


async def _worker(
    worker_id: int,
    queue: asyncio.Queue,
    client: httpx.AsyncClient,
    base_url: str,
    results: List[dict],
):
    while not queue.empty():
        try:
            req_index = queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        start = time.perf_counter()
        status = 0
        error_msg = None
        roast_id = None

        try:
            # Build multipart/form-data upload payload
            unique_resume = DUMMY_RESUME + f"\nCandidate ID #{req_index}-{int(time.time() * 1000)}"
            files = {
                "file": (
                    f"resume_{req_index}.txt",
                    unique_resume.encode("utf-8"),
                    "text/plain",
                )
            }
            resp = await client.post(
                f"{base_url}/api/roast",
                files=files,
                headers={"Accept": "application/json"},
                timeout=30.0,
            )
            status = resp.status_code
            if resp.status_code == 200:
                body = resp.json()
                roast_id = body.get("id")
            else:
                error_msg = resp.text[:120]
        except Exception as exc:
            error_msg = str(exc)

        elapsed_ms = (time.perf_counter() - start) * 1000
        results.append({
            "req_index": req_index,
            "worker_id": worker_id,
            "status": status,
            "latency_ms": elapsed_ms,
            "roast_id": roast_id,
            "error": error_msg,
        })
        queue.task_done()


async def run_load_test(base_url: str, total_requests: int, concurrency: int):
    print("=" * 65)
    print("RESUME ROAST — CONCURRENT LOAD TEST RUNNER")
    print(f"Target URL     : {base_url}/api/roast")
    print(f"Total Requests : {total_requests}")
    print(f"Concurrency    : {concurrency} parallel workers")
    print("=" * 65)

    queue = asyncio.Queue()
    for i in range(total_requests):
        queue.put_nowait(i + 1)

    results: List[dict] = []
    start_total = time.perf_counter()

    limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency + 5)
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [
            asyncio.create_task(_worker(w, queue, client, base_url, results))
            for w in range(concurrency)
        ]
        await asyncio.gather(*tasks)

    duration_s = time.perf_counter() - start_total

    successes = [r for r in results if r["status"] == 200]
    rate_limited = [r for r in results if r["status"] == 429]
    failures = [r for r in results if r["status"] not in (200, 429)]
    latencies = sorted(r["latency_ms"] for r in results)

    def p(pct: float) -> float:
        if not latencies:
            return 0.0
        idx = int(len(latencies) * (pct / 100.0))
        return latencies[min(idx, len(latencies) - 1)]

    print("\nBENCHMARK RESULTS:")
    print(f"- Total Wall Time   : {duration_s:.2f} seconds")
    print(f"- Throughput        : {len(results) / duration_s:.1f} reqs/sec")
    print(f"- Successes (200)   : {len(successes)} ({len(successes)/len(results)*100:.1f}%)")
    print(f"- Rate Limited (429): {len(rate_limited)}")
    print(f"- Hard Failures     : {len(failures)}")
    print("\nLATENCY DISTRIBUTION (ms):")
    print(f"  Min : {min(latencies):.1f} ms" if latencies else "  N/A")
    print(f"  p50 : {p(50):.1f} ms")
    print(f"  p90 : {p(90):.1f} ms")
    print(f"  p95 : {p(95):.1f} ms")
    print(f"  Max : {max(latencies):.1f} ms" if latencies else "  N/A")

    if failures:
        print("\nSAMPLE ERRORS:")
        for f in failures[:5]:
            print(f"  [Status {f['status']}] {f['error']}")

    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="Resume Roast Load Testing Tool")
    parser.add_argument("--url", default="http://localhost:8000", help="Base backend URL")
    parser.add_argument("--requests", type=int, default=10, help="Total requests to fire")
    parser.add_argument("--concurrency", type=int, default=3, help="Concurrent workers")
    args = parser.parse_args()

    asyncio.run(run_load_test(args.url.rstrip("/"), args.requests, args.concurrency))


if __name__ == "__main__":
    main()

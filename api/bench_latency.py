#!/usr/bin/env python3
# ruff: noqa: T201
"""
Measure real p50 / p95 latency for the OpenAI LLM and Moderation APIs.
Run this ONCE before load testing to calibrate MOCK_LLM_P50_MS and
MOCK_MODERATION_P50_MS, then set those env vars on the server.

Usage:
    python bench_latency.py           # 5 calls each (default)
    python bench_latency.py 10        # 10 calls each

The script prints recommended env-var values to copy into your .env or
AWS Elastic Beanstalk environment configuration.

Requirements: OPENAI_API_KEY must be set (reads from .env automatically).
"""

import os
import statistics
import sys
import time

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5

if not OPENAI_API_KEY:
    sys.exit("ERROR: OPENAI_API_KEY not set in environment or .env file.")

try:
    from openai import OpenAI
except ImportError:
    sys.exit("ERROR: openai package not found. Run: pip install openai")

client = OpenAI(api_key=OPENAI_API_KEY)


def _pct(sorted_vals, p):
    idx = min(int(len(sorted_vals) * p / 100), len(sorted_vals) - 1)
    return sorted_vals[idx]


def bench_moderation(n):
    print(f"\n--- Moderation (omni-moderation-latest) — {n} calls ---")
    times = []
    for i in range(n):
        t0 = time.perf_counter()
        client.moderations.create(
            input="Hello, how are you doing today?",
            model="omni-moderation-latest",
        )
        ms = (time.perf_counter() - t0) * 1000
        times.append(ms)
        print(f"  [{i + 1}/{n}] {ms:.0f} ms")
    return times


def bench_llm(n):
    print(f"\n--- LLM (gpt-4o-mini, ~50 tokens) — {n} calls ---")
    times = []
    for i in range(n):
        t0 = time.perf_counter()
        client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Reply in 1-2 sentences only.",
                },
                {"role": "user", "content": "Hello! How are you today?"},
            ],
            max_tokens=60,
        )
        ms = (time.perf_counter() - t0) * 1000
        times.append(ms)
        print(f"  [{i + 1}/{n}] {ms:.0f} ms")
    return times


def report(label, times):
    s = sorted(times)
    print(
        f"  min={s[0]:.0f}  p50={_pct(s, 50):.0f}  "
        f"p95={_pct(s, 95):.0f}  max={s[-1]:.0f}  "
        f"mean={statistics.mean(s):.0f}  ms"
    )
    return int(_pct(s, 50))


print(f"Benchmarking with {N} calls each. This will cost a few cents.\n")

mod_times = bench_moderation(N)
mod_p50 = report("moderation", mod_times)

llm_times = bench_llm(N)
llm_p50 = report("llm", llm_times)

print("\n--- Recommended env vars (set on server before load test) ---")
print("MOCK_LLM=true")
print(f"MOCK_LLM_P50_MS={llm_p50}")
print(f"MOCK_MODERATION_P50_MS={mod_p50}")
print()
print("Copy the above into api/.env (local) or EB environment variables (deployed).")
print("Then restart the server and run: locust -f locustfile.py --host <url>")

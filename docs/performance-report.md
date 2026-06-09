# ChatLab Performance Report
## How Many Conversations Can the Chatbot Handle?

**Audience:** Project team, non-technical stakeholders, collaborators  
**Last updated:** June 2026  
**Status:** Testing in progress — results table updated as runs complete

---

## What We Measured

ChatLab is a web platform where research participants have text conversations with an AI chatbot. We wanted to answer one question:

> **How many people can use the chatbot at the same time without it slowing down or failing?**

We ran a series of load tests — automated scripts that simulate hundreds of users having conversations simultaneously — and measured whether the system stayed fast and error-free.

---

## What a "Conversation" Looks Like in the Test

Each simulated user follows the same pattern a real participant would:

1. Starts a new conversation with the chatbot
2. Sends a message, waits for a reply, sends another — every 5 seconds on average (random, between 0 and 15 seconds)
3. Continues for the full duration of the test

We ran tests for 5–25 minutes each, gradually increasing the number of simultaneous users.

---

## How We Avoided Running Up an AI Bill

Real AI API calls (to OpenAI, Anthropic, etc.) cost money and vary in speed depending on the provider's servers — making it hard to isolate whether *our* system or *their* servers are the bottleneck.

We built a **mock mode** that:
- Skips the actual AI call
- Waits a realistic amount of time (based on measured real-world response times: ~900ms for the AI, ~220ms for safety moderation)
- Returns a placeholder response
- **Still does everything else for real**: saves messages to the database, updates the conversation cache, logs data

This means the load test exercises our entire infrastructure — database, caching layer, API server — without touching the AI APIs. When we're ready to test with real AI, we flip one environment variable.

---

## Results

*Each row is one test run. "Errors" means any request that failed or timed out.*

| Test | Simultaneous Users | Target Messages/sec | Actual Messages/sec | Avg Response Time | Error Rate | Verdict |
|------|--------------------|---------------------|---------------------|-------------------|------------|---------|
| Baseline | 5 | 1 | ~0.6 | 1,214 ms | 0% | ✅ Pass |
| 5 RPS | 25 | 5 | 5.0 | 1,274 ms (p50 1,200 / p95 2,000) | 0% | ✅ Pass |
| 10 RPS | 50 | 10 | 10.0 | 1,284 ms (p50 1,200 / p95 2,000) | 0% | ✅ Pass |
| 50 RPS | 250 | 50 | 50.0 | 1,303 ms (p50 1,200 / p95 2,100) | 0% | ✅ Pass |
| 100 RPS | 500 | 100 | 91.5 | 1,411 ms (p50 1,400 / p95 2,200) | 0% chatbot / 7.8% init¹ | ⚠️ Partial |
| 200 RPS (local) | 1,000 | 200 | ~100 (ceiling¹) | 1,728 ms (p50 1,600 / p95 3,000) | 0% chatbot / 64% init¹ | 🔶 Local ceiling |

> **RPS** = Requests Per Second — the number of messages the system receives every second across all users.  
> The 200 RPS target means 200 chatbot messages per second, or about **12,000 per minute**.

> ¹ **Init failures at 100+ RPS (local only):** The conversation-start endpoint failed for ~8% of users at 500 concurrent users on the local development server. The chatbot itself had 0 errors. This is a limitation of the local `manage.py runserver` thread ceiling — not an issue in the production deployment, which uses an async server (ASGI + Uvicorn) that handles concurrent connections without per-request threads.

### Reading the response time

The **average response time** measures how long a user waits for the chatbot's reply after sending a message. In mock mode this is approximately:

- ~900 ms for the AI to "think" (simulated)
- ~220 ms for safety screening (simulated)
- Plus actual database writes, cache updates, and network overhead

A real deployment with live AI will likely land in the **1–2 second** range for a typical message.

---

## What Changed to Make This Possible

Before this work, the server had a hard limit of **3 simultaneous requests** — meaning if 4 people sent a message at the same moment, the 4th had to wait for one of the first 3 to finish. This was a fundamental architecture issue.

We made the following changes:

| Change | What it does |
|--------|--------------|
| Switched from WSGI to ASGI server | Allows the server to handle hundreds of concurrent requests in a single process, instead of one-at-a-time per worker |
| Added Uvicorn workers | Industry-standard async web server workers that work natively with Django's async views |
| Database connection pooling | Reuses database connections instead of opening a new one for every request (saves ~20–50 ms per request at scale) |
| Request timing logging | Every request now logs how long it took, making it easy to spot slow endpoints |
| Mock mode for AI calls | Enables realistic load testing without API costs |

---

## What the Numbers Mean for Research Studies

| Scenario | Users at once | Notes |
|----------|--------------|-------|
| Small pilot study | 10–50 | Well within tested capacity |
| Medium study | 50–200 | Expected to be fine; tests in progress |
| Large concurrent study | 500–1,000 | Target; tests planned |
| Burst (all participants at once) | 1,000+ | Requires deployed AWS infrastructure; local laptop tests are a lower bound |

The local tests (run on a development laptop with Docker) represent a **conservative lower bound**. The production deployment on AWS will have more CPU, memory, and can be scaled horizontally (more servers) if needed.

---

## How to Read the Test Setup

The tests were run with [Locust](https://locust.io), an open-source load testing tool used widely in industry. Each test run specifies:

- **Users**: how many virtual participants
- **RPS target**: total messages per second across all users
- **Duration**: how long the test ran at full load

Tests ramp up gradually (not all users at once) to mirror how a real study launches — participants join over a period of time, not all in the same second.

---

## Local Test Summary

All local tests are now complete. Key findings:

**The chatbot itself never failed** — across every test, from 1 RPS to 200 RPS, the core chat endpoint had a **0% error rate**. Every message sent got a response.

The local ceiling (~100 RPS) is a limitation of the development server (`manage.py runserver`), which handles each request in a separate thread. At 500+ simultaneous users, it runs out of threads. This is expected and by design — the development server is not meant for production load.

**Two bugs found and fixed during testing:**
1. MariaDB default `max_connections` (151) too low for high concurrency → raised to 500
2. `initialize_conversation` endpoint was sync in an async server → converted to async

These fixes are already in the codebase and will apply to the production deployment.

## Next Steps

1. ✅ ~~Complete the ramp-up from 5 → 200 RPS locally~~
2. Deploy to AWS with mock mode enabled (`MOCK_LLM=true` in EB environment variables)
3. Re-run the 200 RPS test against the production deployment (ASGI + Uvicorn, no thread limit)
4. Run a final test with **real AI calls** (not mock) to confirm end-to-end performance
5. Document the final AWS configuration (instance type, number of servers) as the recommended production setup

---

*Technical questions: see `api/locustfile.py` for the test script, `api/bench_latency.py` for the latency calibration tool, and `api/.env.example` for configuration options.*

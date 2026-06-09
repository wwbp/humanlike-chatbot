# ChatLab Performance Report
## How Many Conversations Can the Chatbot Handle?

**Audience:** Project team, non-technical stakeholders, collaborators  
**Last updated:** June 9, 2026  
**Status:** AWS staging tests in progress — 200 RPS achieved at 0.9% error rate

---

## What We Measured

ChatLab is a web platform where research participants have text conversations with an AI chatbot. We wanted to answer one question:

> **How many people can use the chatbot at the same time without it slowing down or failing?**

We ran a series of load tests — automated scripts that simulate hundreds of users having conversations simultaneously — and measured whether the system stayed fast and error-free.

---

## What a "Conversation" Looks Like in the Test

Each simulated user follows the same pattern a real participant would:

1. Starts a new conversation with the chatbot
2. Sends a message, waits for a reply, sends another — every 5 seconds on average
3. Continues for the full duration of the test

Tests ran for 5–25 minutes each, with users ramping up gradually to mirror how a real study launches — participants join over time, not all in the same second.

---

## How We Avoided Running Up an AI Bill

Real AI API calls (to OpenAI, Anthropic, etc.) cost money and vary in speed depending on the provider's servers — making it hard to tell whether *our* system or *their* servers are the bottleneck.

We built a **mock mode** that:
- Skips the actual AI call
- Waits a realistic amount of time (based on measured real-world response times: ~900ms for the AI, ~220ms for safety moderation)
- Returns a placeholder response
- **Still does everything else for real**: saves messages to the database, updates the conversation cache, logs data

This means the load test exercises our entire infrastructure — database, caching layer, API server — without touching the AI APIs. When we're ready to test with real AI, we flip one environment variable.

---

## Results

### Local Development Tests (completed)

*Run on a development laptop with Docker. These are a conservative lower bound — production AWS will perform better.*

| Test | Simultaneous Users | Target Rate | Actual Rate | Avg Response | Error Rate | Verdict |
|------|--------------------|-------------|-------------|--------------|------------|---------|
| Baseline | 5 | 1 msg/sec | ~0.6 | 1,214 ms | 0% | ✅ Pass |
| 5 RPS | 25 | 5 msg/sec | 5.0 | 1,274 ms | 0% | ✅ Pass |
| 10 RPS | 50 | 10 msg/sec | 10.0 | 1,284 ms | 0% | ✅ Pass |
| 50 RPS | 250 | 50 msg/sec | 50.0 | 1,303 ms | 0% | ✅ Pass |
| 100 RPS | 500 | 100 msg/sec | 91.5 | 1,411 ms | 0% chat / 7.8% start¹ | ⚠️ Partial |
| 200 RPS | 1,000 | 200 msg/sec | ~100 (ceiling²) | 1,728 ms | 0% chat / 64% start² | 🔶 Dev ceiling |

> ¹ **"Start" errors** = failures on the conversation-start step (before any messages are sent).  
> ² **Dev ceiling**: the local development server runs out of threads at 500+ concurrent users. This is expected — the development server is not designed for production load. The production AWS server does not have this limit.

---

### AWS Staging Tests (in progress)

*Run against our real AWS infrastructure. This is the environment closest to production.*

**Infrastructure used (final configuration):**
- App server: `t3.medium` instances (2 vCPU, 4 GB RAM), 4 instances active (auto-scaling 3–6), 8 Gunicorn workers per instance = 32 workers total
- Database: MySQL 8.0 on `db.t3.medium` (2 vCPU, 4 GB RAM, ~341 max connections) — upgraded from `db.t3.small` (166 max connections)
- Cache: AWS ElastiCache Redis (serverless, auto-scales)
- Autoscaling: Latency-based trigger (scale up when avg response > 2s)

| Test | Users | Target Rate | Actual Rate | Avg Response | Error Rate | Verdict |
|------|-------|-------------|-------------|--------------|------------|---------|
| Smoke test (single user) | 1 | — | — | ~1,100 ms | 0% | ✅ Pass |
| Warmup 10 RPS (pre-fix) | 50 | 10 msg/sec | 10.0 | 1,393 ms | ~11%³ | 🐛 Bug found |
| 200 RPS attempt 1 (pre-fix) | 1,000 | 200 msg/sec | 184 | 1,341 ms | ~45%⁴ | 🐛 Bug found |
| 200 RPS attempt 2 (pre-fix) | 1,000 | 200 msg/sec | 196 | 819 ms | ~47%⁵ | 🐛 Bug found |
| 200 RPS attempt 3 (3 × t3.medium) | 1,000 | 200 msg/sec | 212 | 1,895 ms | 1.3%⁶ | 🔶 Near pass |
| **200 RPS attempt 4 (4 × t3.medium)** | **1,000** | **200 msg/sec** | **200+** | **1,645 ms** | **0.9%⁶** | **🔶 Near pass** |

> ³ ⁴ ⁵ Error rates in these runs reflect bugs in our code (described below), not fundamental capacity limits. All five bugs have been fixed.  
> ⁶ The remaining 0.9% errors arrive in brief bursts (not a steady drip), concentrated during the fast 40-second user-spawn phase and occasional brief load spikes. Chat-conversation init (0/1,000 users) is 0% in both runs. Performance is clean in steady state.

---

## What We Found and Fixed

### Local phase: two bugs

**Bug 1 — Database had too few connections for high concurrency**  
The local database was configured to handle at most 151 simultaneous connections (the default). At 500+ concurrent users, the server ran out of slots. Fixed by increasing the limit to 500.

**Bug 2 — Conversation-start endpoint was running in an outdated mode**  
The endpoint that begins a conversation was written in an older style that forced the server to create a separate thread for each user. At high concurrency, the server ran out of threads. Fixed by rewriting the endpoint in the modern async style that can handle thousands of concurrent users in a single process.

---

### AWS phase: two more bugs

Deploying to AWS revealed a different class of problems — ones that only appear when the system is under sustained real-world load at scale.

**Bug 3 — Database connections were corrupting under concurrent async load**  
*(Fix: `CONN_MAX_AGE=0` — connections open and close cleanly per request)*

When the server handles many requests at the same time using Django's async framework, all database calls from a single server process share one dedicated background thread. If database connections were kept "alive" between requests (an optimization that normally saves time), that shared thread could end up with a connection in a bad state — causing the next request that used it to fail, even though the database itself was fine.

At just 5 simultaneous requests hitting the same server process, 80% were failing because of this.

The fix: tell the server to open a fresh database connection for each request rather than reusing the previous one. The small extra cost (~1ms per request) is negligible at our scale.

**Bug 4 — Safety moderation was accidentally blocking the database**  
*(Fix: `thread_sensitive=False` on `moderate_message`)*

Every chat message passes through a safety check before the AI responds (this screens for harmful content). In mock mode, this check simulates a 220ms wait — realistic for the real moderation API. The problem: this wait was accidentally running inside the same dedicated thread responsible for all database operations. So while the safety check was counting to 220ms, no other request on that server process could touch the database at all.

At 200 requests per second across 8 server processes, each process needed to handle about 25 requests per second. With a 220ms wait per request, each process's database thread was occupied for 5.5 seconds every second — an impossible 550% overload. Nearly half of all requests failed because they couldn't reach the database.

The fix: run the safety check in a separate worker thread, away from the database thread. The two now run in parallel.

---

### AWS phase: one more bug

**Bug 5 — Too many simultaneous database connections at scale**  
*(Fix: close the database connection before the AI call, reopen it after)*

After fixing bugs 3 and 4, the system handled light load (under ~80 requests per second) perfectly. At 200 RPS, about 47% of requests failed immediately — roughly the same error as bug 3 ("Error fetching the bot from the database"), but for a different reason.

The underlying issue is a subtlety in how Django 5.2 handles async: for each incoming request, it allocates a small private background thread to run all database operations. Crucially, that thread — and the MySQL database connection it holds — stays alive for the entire request, including the ~1 second the server spends waiting for the AI to respond.

At 200 requests per second, with each request lasting about 1.1 seconds, the system holds about 220 database connections open simultaneously. But our RDS database instance (`db.t3.small`, 2 GB RAM) supports a maximum of ~166 connections. The 54 "overflow" connections are rejected outright, returning an immediate error.

The fix: once all the database reads are done (fetching the bot, checking conversation history), explicitly release the connection before the AI call. The connection is reopened automatically when it is needed again after the AI responds (to write the new messages to the database). This reduces peak simultaneous connections from ~220 to ~10.

---

## Infrastructure Changes Made

| Change | What it does |
|--------|--------------|
| WSGI → ASGI server | Allows hundreds of concurrent requests per process instead of one-at-a-time per thread |
| Uvicorn workers (8 per server, up from 4) | Industry-standard async workers; scales with the number of CPUs |
| `CONN_MAX_AGE=0` | Fresh database connection per request — prevents state corruption in async environments |
| Safety check moved to separate thread | Frees the database thread for actual database work |
| Release DB connection before AI call | Ensures the connection is not held during the 1-second AI wait — keeps peak connections under 10 instead of 220 |
| EC2 upgrade: `t3.small` → `t3.medium` | 4 GB RAM (vs 2 GB); handles more concurrent connections and threads per instance |
| RDS upgrade: `db.t3.small` → `db.t3.medium` | ~341 max DB connections (vs ~166) — eliminated connection-limit failures at 200 RPS |
| Autoscaling: NetworkOut → Latency-based trigger | Response time is the right signal for an API; adds instances when avg latency exceeds 2 s |
| Pre-warm 4 instances before test | Avoids routing traffic to cold instances during the initial user-spawn burst |
| Database connection limit raised | Local: 151 → 500; AWS: `db.t3.medium` handles 341 connections natively |
| Request timing logs | Every request logs how long it took, making performance regressions visible |
| Mock mode (`MOCK_LLM=true`) | Load-tests the full infrastructure without AI API costs |

---

## What the Numbers Mean for Research Studies

| Study scenario | Simultaneous users | Expected status |
|----------------|--------------------|-----------------|
| Small pilot | 10–50 | ✅ Well within tested capacity |
| Medium study | 100–250 | ✅ Confirmed working; 0% errors at these levels |
| Large concurrent study | 500–1,000 | 🔶 200 RPS (≈1,000 users) achieved at 0.9% errors; continuing to tune |
| Very large burst | 1,000–5,000 | ⏳ Next milestone; requires additional auto-scaling instances and possible read replica |

---

## How to Read Response Times

The **average response time** measures how long a user waits for the chatbot's reply after sending a message. In mock mode:

- ~900 ms — AI "thinking" (simulated)
- ~220 ms — safety screening (simulated)
- Plus database writes, cache updates, and network

A real deployment with live AI will likely land in the **1–2 second** range for a typical message. This feels fast and natural in a conversation — similar to a person typing a reply.

---

## About the Load Testing Tool

Tests were run with [Locust](https://locust.io), an open-source load testing tool used widely in industry. Users ramp up gradually, hold at the target level, then stop — mirroring how a real study might launch.

---

## Status and Next Steps

| Step | Status |
|------|--------|
| ✅ Local tests 1 → 200 RPS | Complete |
| ✅ Deploy to AWS staging with mock mode | Complete |
| ✅ Fix async database bugs found on AWS | Complete (5 bugs fixed) |
| ✅ Upgrade AWS infrastructure (t3.medium EC2 + RDS, 8 workers, 4 instances) | Complete |
| 🔶 AWS 200 RPS clean test | **0.9% error rate — near clean; tuning continues** |
| ⬜ AWS test with real AI calls | Planned after mock mode clears |
| ⬜ Plan path to 5,000 concurrent users | Next milestone — auto-scaling design + read replica |
| ⬜ Document recommended production configuration | Planned |

---

*Technical questions: see `api/locustfile.py` for the test script, `api/bench_latency.py` for the latency calibration tool, and the commit history for details on each fix.*

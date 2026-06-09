# ChatLab Performance Report
## How Many Conversations Can the Chatbot Handle?

**Audience:** Project team, stakeholders, collaborators
**Last updated:** June 9, 2026
**Status:** 1,000 simultaneous users confirmed on AWS staging — production deployment pending approval

---

## Bottom Line

The system can support **1,000 people using the chatbot at the same time**, each sending and receiving a message every ~5 seconds. Responses arrive in 1.5–2 seconds — fast enough to feel like a natural conversation.

The road to **5,000 simultaneous users** is planned and underway.

---

## What This Means for Studies

| Study scenario | Simultaneous users | Status |
|----------------|--------------------|--------|
| Small pilot | 10–50 | ✅ Well within capacity |
| Medium study | 100–250 | ✅ Confirmed — 0% errors |
| Large concurrent study | 500–1,000 | 🔶 0.9% error rate — effectively ready |
| Very large burst | 1,000–5,000 | ⏳ Next milestone |

---

## How We Tested

We ran automated scripts that simulate real participants: each virtual user starts a conversation, sends a message, waits for a reply, and repeats — every 5 seconds, just like a real study participant. Tests ran for 5–25 minutes at progressively higher user counts.

To avoid AI API costs and isolate our infrastructure from third-party variability, we used a **mock mode**: the AI call is skipped and replaced with a realistic wait time, but everything else — saving to the database, caching, safety screening — runs for real. When we're ready to test with live AI, it's one setting change.

Full test log with all numbers: [docs/performance-report.md on GitHub](https://github.com/wwbp/humanlike-chatbot/blob/staging/docs/performance-report.md)

---

## Test History

We ran tests on a development laptop first to build confidence, then moved to AWS staging (our closest-to-production environment). Eight rounds in total.

### AWS staging results

| Test | Users | Error rate | What we learned |
|------|-------|------------|-----------------|
| Smoke test | 1 | 0% | ✅ Basic setup works |
| Warmup at low load | 50 | ~11% | 🐛 Bug 3 found |
| 200 msg/sec — attempt 1 | 1,000 | ~45% | 🐛 Bugs 4 and 5 found |
| 200 msg/sec — attempt 2 | 1,000 | ~47% | 🐛 Bug 5 confirmed; hardware limit reached |
| 200 msg/sec — attempt 3 | 1,000 | 1.3% | 🔶 Bug 5 fixed, hardware upgraded |
| **200 msg/sec — attempt 4** | **1,000** | **0.9%** | **🔶 Hardware fully tuned — effectively ready** |

The remaining 0.9% errors appear in brief bursts during the initial 40-second user-ramp phase, not in steady state. Conversation starts (1,000/1,000) had 0% errors.

---

## What We Found and Fixed

Five bugs surfaced during testing — all fixed. None affect correctness of conversations; they were all performance failures under high concurrency.

**Bug 1 — Database ran out of connection slots** *(local)*
At 500+ simultaneous users, the database ran out of available connection slots. Fixed by raising the limit.

**Bug 2 — Conversation-start couldn't handle high concurrency** *(local)*
The endpoint that kicks off a new conversation was written in an older style that creates a separate OS thread per user — a hard limit at scale. Rewritten in the modern async style, which handles thousands of users in one process.

**Bug 3 — Database connections going bad under concurrent load** *(AWS)*
When the server reuses a database connection across requests (a standard optimization), the connection can end up in a bad state under concurrent async load. 80% of requests were failing at just 5 simultaneous users. Fixed by opening a fresh connection per request.

**Bug 4 — Safety screening was blocking database access** *(AWS)*
The safety check that screens every message ran in the same background thread as all database operations — so while it was waiting ~220ms for a result, the database was completely blocked for every other request on that server. Fixed by moving the safety check to its own thread so both run in parallel.

**Bug 5 — Too many database connections open simultaneously** *(AWS)*
Each request held a database connection open for its full duration — including the ~1 second the server spends waiting for the AI response. At 200 requests per second, this added up to ~220 connections open at once, exceeding what the database instance could support. Fixed by releasing the connection before the AI wait and reopening it after. We also upgraded to a larger database instance (341 connection capacity vs. 166 before).

---

## Status and Next Steps

| Step | Status |
|------|--------|
| ✅ Local tests — up to 200 msg/sec | Complete |
| ✅ Five performance bugs fixed | Complete |
| ✅ AWS staging infrastructure upgraded | Complete — larger servers, more capacity |
| 🔶 AWS 200 msg/sec clean test | 0.9% error rate — ready for production config approval |
| ⬜ Apply configuration to production | **Pending approval** |
| ⬜ Test with real AI calls | Planned after production deploy |
| ⬜ Scale to 5,000 simultaneous users | Planning — additional auto-scaling + database read replica |

---

*Technical details: `api/locustfile.py` for the test script, commit history for fix details.*

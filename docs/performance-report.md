# ChatLab Performance Report

**The system handles 1,000 simultaneous users at 0.9% error rate. Five bugs found and fixed. Production config approval pending — next milestone is 5,000 users.**

*Last updated: June 9, 2026 · AWS staging environment*

---

## What This Means for Studies

| Study scenario | Simultaneous users | Status |
|----------------|--------------------|--------|
| Small pilot | 10–50 | ✅ Well within capacity |
| Medium study | 100–250 | ✅ 0% errors confirmed |
| Large concurrent study | 500–1,000 | ✅ 0.9% errors — ready for production |
| Very large burst | 1,000–5,000 | ⏳ Next milestone |

---

## Test History

We ran 12 tests in total — first on a development laptop to build confidence, then on AWS staging (our closest-to-production environment). Error rate went from 47% down to 0.9% across six AWS attempts as bugs were found and fixed.

**AWS staging tests** *(1,000 simulated users, 200 messages/second target)*

| Test | Error rate | Outcome |
|------|------------|---------|
| Smoke test — 1 user | 0% | ✅ Basic setup works |
| Warmup — 50 users | ~11% | Bug found: stale database connections |
| Attempt 1 | ~45% | Bugs found: safety check blocking database; too many connections |
| Attempt 2 | ~47% | Hardware limit confirmed — database maxed out |
| Attempt 3 — after fix + hardware upgrade | 1.3% | Near clean |
| **Attempt 4 — hardware fully tuned** | **0.9%** | ✅ **Ready for production** |

The 0.9% errors appear only during the first 40 seconds while all 1,000 users are ramping on — not in steady state. Conversation starts had 0% errors across all 1,000 users.

---

## What We Fixed

Five bugs found during testing, all resolved. None affected conversation correctness — they were all performance failures at high concurrency.

**Bug 1 — Database ran out of connection slots** *(laptop)*
At 500+ simultaneous users, the database ran out of available slots. Fixed by raising the limit.

**Bug 2 — Conversation-start couldn't handle high concurrency** *(laptop)*
The endpoint that starts a conversation created a separate OS thread per user — a hard limit at scale. Rewritten in the modern async style, which handles thousands of users in one process.

**Bug 3 — Database connections going bad under concurrent load** *(AWS)*
Reusing connections across requests caused them to corrupt under concurrent async load — 80% of requests failing at just 5 simultaneous users. Fixed by opening a fresh connection per request.

**Bug 4 — Safety screening was blocking database access** *(AWS)*
The safety check on every message ran in the same thread as all database operations, freezing database access for ~220ms per request across the whole server. Fixed by moving it to its own thread so both run in parallel.

**Bug 5 — Too many database connections open at once** *(AWS)*
Each request held a database connection open during the entire ~1-second AI wait. At 200 requests/second, this pushed the database past its connection limit. Fixed by releasing the connection before the AI wait and reopening it after. Also upgraded to a larger database instance with double the connection capacity.

---

## Next Steps

| | |
|-|-|
| ⬜ Apply config to production | Awaiting approval — unblocks current studies |
| ⬜ Test with real AI calls | One setting change from mock mode; planned after production deploy |
| ⬜ Scale to 5,000 users | Requires additional auto-scaling tiers and a database read replica |

---

*Technical details: `api/locustfile.py` (test script), commit history (fix details).*

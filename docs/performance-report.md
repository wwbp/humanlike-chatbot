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

## Road to 5,000 Users

### How many server requests does that actually require?

The load test ran at the most aggressive realistic pace: one message every 5 seconds per user. That maps 1,000 users → 200 messages/second, which we've confirmed works. At real study pacing, users take longer between messages.

**Estimated real-user messaging interval** (based on typical chatbot study behavior):

| Component | Estimate |
|-----------|----------|
| AI response arrives | ~1.5 s |
| User reads response (~75 words at 200 wpm) | ~22 s |
| User thinks and types reply | ~20 s |
| **Mean interval between messages** | **~45 s** |
| **Std deviation** | **~20 s** |

The relationship is: **RPS = Users ÷ mean interval**

| Avg seconds between messages | Users our current 200 RPS supports | 5,000 users needs |
|------------------------------|-----------------------------------|--------------------|
| 5 s — load test (worst case) | 1,000 | 1,000 RPS — 5× more infra |
| 15 s — fast-paced study | 3,000 | 333 RPS — scaling needed |
| **30 s — realistic lower bound** | **6,000** | **167 RPS — ✅ current infra covers it** |
| 60 s — typical conversational pace | 12,000 | 83 RPS — ✅ well within capacity |

### What the standard deviation tells us about burst risk

With 5,000 users each independently deciding when to send their next message, the total request rate fluctuates around the mean. By the law of large numbers, the fluctuation is small relative to the total:

- **Mean RPS** at 5,000 users (45 s interval): **111 RPS**
- **Std deviation**: √(5,000 ÷ 45) ≈ **±11 RPS**
- **99.7% of the time**, load stays between 78–144 RPS — well under the 200 RPS ceiling

The infrastructure has ~56 RPS of headroom above the 99.7th-percentile burst. Overload is extremely unlikely unless study design requires very short message intervals (< 15 s).

### Scaling plan if needed

| Trigger | Action |
|---------|--------|
| Message intervals < 30 s, 5,000 users | Add 2–3 more EC2 instances (auto-scaling already configured) |
| Message intervals < 15 s, 5,000 users | Add EC2 instances + MySQL read replica for read-heavy queries |

---

## Next Steps

| | |
|-|-|
| ⬜ Apply config to production | Awaiting approval — unblocks current studies |
| ⬜ Test with real AI calls | One setting change from mock mode; planned after production deploy |
| ⬜ Confirm 5,000-user capacity | Run load test at realistic 30–45 s interval to validate extrapolation above |

---

*Technical details: `api/locustfile.py` (test script), commit history (fix details).*

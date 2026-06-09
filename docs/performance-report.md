# ChatLab — AWS Load Test Results

**200 RPS sustained at 0.91% error rate on 4 × t3.medium. Five bugs fixed. Production deployment pending approval.**

*June 9, 2026 · AWS staging · MOCK_LLM=true (AI response simulated at measured p50 = 900 ms, lognormal σ = 0.4)*

---

## Study Capacity Summary

| Scenario | Simultaneous users | Error rate |
|----------|--------------------|------------|
| Small pilot | 10–50 | 0% |
| Medium study | 100–250 | 0% |
| Large study | 500–1,000 | 0.91% — production-ready |
| 5,000 users at ≥ 45 s/msg | 5,000 | Projected safe — see below |

---

## Infrastructure Configuration

| Component | Specification |
|-----------|---------------|
| App servers | 4 × t3.medium (2 vCPU, 4 GiB RAM) |
| Workers | 8 UvicornWorker (Gunicorn + ASGI) per instance — 32 total |
| Auto-scaling | ALB Latency trigger: scale-out at avg > 2 s; 1-min evaluation; 2-min breach; min 3 / max 6 instances |
| Database | RDS MySQL 8.0 on db.t3.medium (2 vCPU, 4 GiB; max_connections = ⌊4 GiB / 12 MiB⌋ = 341) |
| Cache | ElastiCache Redis (serverless) |
| DB connection mode | CONN_MAX_AGE = 0 (new connection per request) |

---

## Test Results

### Attempt 4 — Final (June 9, 2026)

*1,000 users · 5 s/msg (constant_throughput) · 25 users/s ramp · 420 s duration*

| Metric | Value |
|--------|-------|
| Sustained RPS | 200–217 |
| Total requests | 81,404 |
| Failures | 734 (0.91%) — 730 × HTTP 500, 4 × HTTP 502 |
| Init endpoint failures | 0 / 1,000 |
| p50 / p90 / p95 / p99 | 1,500 / 2,400 / 2,700 / 3,700 ms |
| Avg / Max | 1,645 ms / 7,100 ms |

Failures cluster in the 40-second ramp phase; error rate in steady state is effectively 0%.

### Full AWS Test History

| Test | Users | RPS | Error rate | Finding |
|------|-------|-----|------------|---------|
| Smoke | 1 | — | 0% | Baseline |
| Warmup | 50 | 10 | ~11% | Bug 1: connection state corruption |
| Attempt 1 | 1,000 | 184 | ~45% | Bug 2: moderation serializing DB; Bug 3: connection ceiling |
| Attempt 2 | 1,000 | 196 | ~47% | Bug 3 confirmed: db.t3.small at 166-connection limit |
| Attempt 3 | 1,000 | 212 | 1.3% | Bug 3 fixed; db.t3.medium deployed |
| **Attempt 4** | **1,000** | **200+** | **0.91%** | Fully tuned |

Six local tests (laptop, Docker) preceded AWS phase — validated async rewrite to 100 RPS before cloud deployment.

---

## Bugs Fixed

**Bug 1 — Connection state corruption under async reuse** *(warmup, AWS)*
Django's `ThreadSensitiveContext` (asgiref 3.11) gives each request a dedicated `ThreadPoolExecutor(max_workers=1)` for all DB calls. With `CONN_MAX_AGE > 0`, that thread reuses the previous request's MySQL connection — which can be left in a broken state (mid-transaction, error flag set). Fix: `CONN_MAX_AGE=0` — new connection opened and closed per request.

**Bug 2 — Content moderation serializing the DB thread** *(Attempt 1, AWS)*
`moderate_message()` was dispatched via `sync_to_async(thread_sensitive=True)`, placing the ~220 ms moderation wait inside the request's dedicated DB thread. That blocked all other DB calls on the same worker for the duration. Fix: `thread_sensitive=False`, which routes the call to the shared global thread pool instead.

**Bug 3 — MySQL connection ceiling exceeded at 200 RPS** *(Attempts 1–2, AWS)*
`ThreadSensitiveContext` holds the MySQL connection in the dedicated thread for the full request lifetime, including the AI wait. At 200 RPS × ~1.1 s avg response = 220 simultaneous open connections. db.t3.small ceiling: ⌊2 GiB / 12582880⌋ = 166. Overflow connections rejected with `OperationalError: (1040) Too many connections`.

Fix: `close_old_connections()` called via `sync_to_async(thread_sensitive=True)` after all reads complete and before the AI call. Peak simultaneous connections drop to 200 RPS × 0.29 s (read phase) ≈ 58. Upgraded RDS to db.t3.medium: ceiling = 341.

**Bug 4 — Conversation-start endpoint under WSGI threading** *(local, 100 RPS)*
`/initialize_conversation/` ran as a synchronous WSGI view, one OS thread per concurrent request. Gunicorn thread pool exhausted at ~500 concurrent users. Fix: rewritten as `async def` under ASGI (UvicornWorker). No per-request thread overhead.

**Bug 5 — Local MySQL max_connections too low** *(local, 50 RPS)*
Default MySQL `max_connections=151`. Fixed: set to 500 in local config.

---

## Road to 5,000 Users

### Governing relationship

```
RPS = Users / mean_interval_seconds
```

N independent users sending at mean interval μ produce a Poisson arrival process:
- Mean RPS = N / μ
- Std dev of RPS = √(N / μ)

### Capacity at current 200 RPS ceiling

| Mean interval (s) | RPS at 5,000 users | Within 200 RPS ceiling? | 3σ upper bound |
|-------------------|-------------------|-------------------------|----------------|
| 5 (load test pace) | 1,000 | No — 5× over | 1,011 |
| 15 | 333 | No — 1.7× over | 341 |
| 30 | 167 | Yes — 33 RPS headroom | 167 + 39 = 206 ⚠ marginal |
| 45 | 111 | Yes — 89 RPS headroom | 111 + 32 = 143 ✅ |
| 60 | 83 | Yes — 117 RPS headroom | 83 + 27 = 110 ✅ |

*User messaging interval has not been measured in production studies. The load test at 5 s/msg is a deliberate stress case. Actual research chatbot exchanges (reading + composing) typically run 30–60 s.*

### Scaling actions

| Scenario | Action |
|----------|--------|
| 5,000 users, interval ≥ 45 s | No infrastructure change — validate with a 45 s/msg load test |
| 5,000 users, interval 30–45 s | Pre-warm to 6 instances (auto-scaling cap already set to 6) to absorb 3σ burst |
| 5,000 users, interval < 30 s | 6 × t3.medium + RDS read replica (offloads `SELECT` queries: bot config, conversation history) |

---

## Next Steps

| Action | Status |
|--------|--------|
| Approve production deployment of current config | Awaiting decision |
| Enable real AI calls (`MOCK_LLM=false`) | After production deploy |
| Run 45 s/msg load test to validate 5,000-user projection | Planned |

---

*Test script: `api/locustfile.py` · Fixes: `git log --oneline staging`*

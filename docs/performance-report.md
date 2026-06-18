# ChatLab — Load Test Results

**The app tier scales linearly at ~50 RPS per t3.medium; the bottleneck is the database, not app
instances. 1,000 concurrent users is the validated production baseline; 5,000 users at worst-case
pace is empirically validated on a scaled-up config.**

*AWS staging, us-east-1 · load simulated with `MOCK_LLM=true` (AI response p50 = 900 ms, moderation
p50 = 220 ms, lognormal σ = 0.4) · driven by distributed Locust. Reported RPS is steady-state
(post-ramp). "Stress pace" = 5 s between messages per user, so `users = RPS × 5`.*

---

## Results

### Capacity by scenario

| Scenario | Simultaneous users | Config | Result |
|----------|-------------------|--------|--------|
| Small pilot | 10–50 | production baseline | 0% errors |
| Medium study | 100–250 | production baseline | 0% errors |
| Large study | 500–1,000 | production baseline (4 × t3.medium) | 0.91% — production-ready |
| 5,000 @ realistic ≥45 s/msg | 5,000 | production baseline | safe — only 111 RPS needed (see [Realistic pace](#realistic-pace-the-likely-real-world-case)) |
| 5,000 @ 5 s/msg stress | 5,000 | 20 × t3.medium + db.m5.2xlarge | **0.31% — empirically validated** |

### Horizontal scaling (5 s/msg stress pace)

| Config | App servers | RDS | Steady RPS | Errors | DB peak conns / CPU | Supported users |
|--------|-------------|-----|-----------|--------|---------------------|-----------------|
| A | 4 × t3.medium | db.t3.medium | ~200 | 0.13% | 300 / — | ~1,000 |
| B | 6 × t3.medium | db.t3.medium | ~290 | 6.1% | 305 (**ceiling hit**) | DB-limited |
| C | 8 × t3.medium | db.m5.2xlarge | 400 | 0.005% | 494 / 21% | 2,000 |
| D | 12 × t3.medium | db.m5.2xlarge | 600 | 0.009% | 784 / 30% | 3,000 |
| E | 16 × t3.medium | db.m5.2xlarge | 800 *(interp.)* | — | ~1,070 / ~42% | 4,000 |
| **F** | **20 × t3.medium** | **db.m5.2xlarge** | **998** | **0.31%** | 2,003 / **53%** | **5,000 ✓** |

Empirical points A, C, D, F line up at **exactly 50 RPS per t3.medium**. E is interpolated between two
measured points. At config F, p50 = 1,400 ms / p99 = 4,200 ms (baseline latency held) and RDS CPU was
only 53% — the DB is not the next wall.

### What it takes to run 5,000 users at stress pace

- **20 × t3.medium** app instances (linear scaling, 50 RPS each).
- **db.m5.2xlarge** (8 vCPU) — not a bigger connection cap on db.t3.medium (see findings).
- **`max_connections` ≥ 2,500** — at 5,000 users the ramp burst grazed a 2,000 cap (the residual 0.31%
  errors). Real users don't all initialize within 200 s, so a realistic arrival spread also avoids this.

---

## Production baseline (current, shipped June 10)

| Component | Specification |
|-----------|---------------|
| App servers | 4 × t3.medium (2 vCPU, 4 GiB); ASG min 3 / max 6 |
| Workers | 8 UvicornWorker (Gunicorn + ASGI) per instance |
| Auto-scaling | ALB Latency trigger: scale-out avg > 2.5 s, +2; scale-in < 1.2 s, −1 |
| Database | RDS MySQL 8.0, db.t3.medium — `max_connections` **measured 305** (the ⌊4 GiB/12 MiB⌋≈341 formula overstates it; RDS reserves memory) |
| Cache | ElastiCache Redis (serverless) |
| DB connections | `CONN_MAX_AGE=0` (new connection per request) |

Validated at 200–217 RPS / 0.91% errors on 1,000 users. Errors cluster in the spawn ramp; steady-state
is effectively 0%.

---

## Supporting detail

### Key finding — the database is the bottleneck, not app instances

The path to 5,000 users is gated by the DB, discovered in two steps:

1. **Connection ceiling (config B).** At 6 instances / ~300 RPS, errors hit 6.1%, concentrated in the
   ramp where the init + first-message burst pushed MySQL `Threads_connected` past the **actual 305**
   ceiling (`Connection_errors_max_connections` = 44,493).
2. **CPU saturation (config C).** Raising `max_connections` to 1,500 on the same db.t3.medium made it
   *worse* — 309 RPS, 4.6% errors, p50 collapsed 1,400 → 4,500 ms, connections ballooned to 1,503. RDS
   CPU pegged at **88–96%**: db.t3.medium's 2 vCPU saturate near 300 RPS. The old connection ceiling had
   been *accidentally shedding load*; removing it caused congestion collapse.

**Fix:** upgrade the DB by CPU — **db.m5.2xlarge** (8 vCPU, non-burstable). Configs C–F then ran clean
with the app tier scaling linearly. Connections scale ~1.3 per request.

### Method

Distributed Locust 2.34 (`--processes 8`) on a dedicated `c5.2xlarge`, driving the ALB directly with a
`Host: dev.bot.wwbp.org` header (raw ALB host → 400 from `ALLOWED_HOSTS`; `dev.bot.wwbp.org` → CloudFront).
Per config: ASG pinned `min=desired=max=N`; DB connections and RDS CPU sampled throughout. Test script:
`api/locustfile.py` (set `LOAD_TEST_HOST_HEADER` to drive the ALB directly).

### Realistic pace (the likely real-world case)

`RPS = users / mean_interval`. Research chatbot exchanges (reading + composing) typically run 30–60 s,
not 5 s. At 5,000 users:

| Mean interval | RPS needed | Covered by current 4 × t3.medium baseline? |
|---------------|-----------|--------------------------------------------|
| 45 s | 111 | ✅ yes, comfortably |
| 30 s | 167 | ✅ yes (pre-warm to 6 for burst headroom) |
| 5 s (stress) | 1,000 | needs the 20-instance + db.m5.2xlarge config above |

The 20-instance requirement is purely the 5 s stress case. **For realistic study pacing, the existing
production config already supports 5,000 users.**

### Bugs fixed (June 9 campaign, all shipped)

1. **Connection state corruption** — `CONN_MAX_AGE>0` let the async DB thread reuse a broken connection. Fix: `CONN_MAX_AGE=0`.
2. **Moderation serializing the DB thread** — `moderate_message()` ran `thread_sensitive=True`, blocking DB calls for ~220 ms. Fix: `thread_sensitive=False`.
3. **MySQL connection ceiling** — connection held for full request (incl. AI wait). Fix: `close_old_connections()` after reads / before the AI call (peak drops to RPS × 0.29 s); upgraded db.t3.small → db.t3.medium.
4. **Init endpoint under WSGI** — synchronous view exhausted the thread pool at ~500 users. Fix: rewritten `async def` under ASGI.
5. **Local MySQL `max_connections=151`** — raised to 500 in local config.

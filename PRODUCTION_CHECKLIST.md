# Go-to-Production Checklist — ChatLab Humanlike Chatbot

Stack: Django 5.1 · React 18 + Vite · MySQL (RDS) · Redis (ElastiCache) · Docker · AWS Elastic Beanstalk

---

## Legend
- ✅ Done / Fixed
- 🔲 Not started
- 🚧 In progress
- ❗ Blocked / needs decision

---

## 1 · Security

| # | Item | Status | Notes |
|---|------|--------|-------|
| S-01 | `SECRET_KEY` must come from env; no hardcoded fallback | ✅ Fixed | settings.py now raises RuntimeError if unset |
| S-02 | `ALLOWED_HOSTS` locked to explicit list in production | ✅ Fixed | Dev: localhost; Prod: wwbp.org domains |
| S-03 | `CORS_ALLOW_ALL_ORIGINS` removed; `CORS_ALLOWED_ORIGINS` explicit list | ✅ Fixed | Was set twice in settings.py |
| S-04 | `X_FRAME_OPTIONS = "SAMEORIGIN"` | ✅ Fixed | Was "ALLOWALL" — regression from April audit |
| S-05 | `REDIS_URL` required in prod; no hardcoded cluster URL fallback | ✅ Fixed | Raises RuntimeError if unset |
| S-06 | `/test-upload/` endpoint gated behind `DEBUG=True` | ✅ Fixed | Never exposed in production |
| S-07 | `/api/bots/` CRUD locked to staff-only | ✅ Fixed | `_require_staff` guard on all methods |
| S-08 | `/api/avatar/` POST and DELETE locked to staff-only | ✅ Fixed | GET still public (participants need avatars) |
| S-09 | `/api/avatar/<bot_name>/` POST and DELETE locked to staff-only | ✅ Fixed | |
| S-10 | `/api/avatar-upload/` requires staff auth + filename sanitization + content-type whitelist | ✅ Fixed | Only image MIME types accepted |
| S-11 | `/api/session/` validates `conversation_id` before calling OpenAI | ✅ Fixed | Returns 404 for unknown convo |
| S-12 | `/api/session/` returns 503 (not `Bearer None`) when `OPENAI_API_KEY` absent | ✅ Fixed | |
| S-13 | Moderation category not leaked to user | ✅ Fixed | Generic message returned; category only logged |
| S-14 | `str(e)` exception leak removed from all 500 responses | ✅ Fixed | All views return generic "unexpected error" |
| S-15 | Audio MIME-type whitelist on `/api/upload_voice_utterance/` | ✅ Fixed | voicechat.py |
| S-16 | `AvatarDetailAPIView.delete` referenced `avatar.image_path` (field doesn't exist → AttributeError) | ✅ Fixed | Uses `avatar.chatbot_avatar` |
| S-17 | `ListBotsAPIView.post` creates Bot without required `ai_model` FK → IntegrityError | ✅ Fixed | Now looks up `Model` by provider+model_id first |
| S-18 | Verify Django `SECURE_SSL_REDIRECT`, `HSTS` headers in prod | 🔲 TODO | Add to prod settings block |
| S-19 | Admin URL changed from `/api/admin/` to something non-obvious | 🔲 TODO | Low-hanging bot-scan deterrent |
| S-20 | Rate limiting on chatbot / followup endpoints | 🔲 TODO | Use `django-ratelimit` or nginx `limit_req` |
| S-21 | Dependency audit: `pipenv check` + `npm audit` | 🔲 TODO | Run before each release |

---

## 2 · Unit & Integration Tests — Backend

Target: 100% branch coverage on all service-layer logic (LLM calls mocked).

| # | Module | What to test | Status |
|---|--------|-------------|--------|
| T-01 | `post_processing.human_like_chunks` | short sentence, question at end, buffer flush | ✅ Exists |
| T-02 | `post_processing.calculate_typing_delays` | humanlike=True, humanlike=False, per-segment | ✅ Exists |
| T-03 | `runchat.generate_system_prompt` | bot only, bot+persona, exception path | 🔲 TODO |
| T-04 | `runchat.run_chat_round` | happy path (mock LLM), blocked by moderation, max_transcript_length (0, N, -1), cache miss → DB reload, followup guard | 🔲 TODO |
| T-05 | `runchat.save_chat_to_db` | conversation found, Conversation.DoesNotExist | 🔲 TODO |
| T-06 | `conversation.InitializeConversationAPIView` | new convo, existing convo resume, missing fields, bad JSON, bot not found | 🔲 TODO |
| T-07 | `conversation.randomly_select_persona` | pool empty, pool of one, pool of many (seeded random) | 🔲 TODO |
| T-08 | `moderation.moderate_message` | no API key (skip), global disabled, category blocked, all clear | 🔲 TODO |
| T-09 | `followup.generate_followup_message` | disabled on bot, no instruction prompt, user not idle, cooldown active, recurring=False second call, happy path | 🔲 TODO |
| T-10 | `followup.is_user_idle` | no messages, within threshold, past threshold | 🔲 TODO |
| T-11 | `followup.FollowupAPIView` | reset_flag, error→generic 500 | 🔲 TODO |
| T-12 | `bots.ListBotsAPIView.get` | non-staff → 403, staff → 200 list | 🔲 TODO |
| T-13 | `bots.ListBotsAPIView.post` | non-staff → 403, missing fields, model not found, success | 🔲 TODO |
| T-14 | `bots.BotDetailAPIView.get/put/delete` | non-staff → 403, bot not found → 404, happy path | 🔲 TODO |
| T-15 | `upload.get_presigned_url` | non-staff → 403, bad content-type → 415, path traversal filename → 400, success | 🔲 TODO |
| T-16 | `voicechat.get_realtime_session` | missing conversation_id, unknown conversation, no API key → 503, success | 🔲 TODO |
| T-17 | `voicechat.upload_voice_utterance` | missing convo id, bad MIME type, success text, success audio | 🔲 TODO |
| T-18 | `avatar.AvatarAPIView.post` | non-staff → 403, no bot_name → 400, success | 🔲 TODO |
| T-19 | `engine.get_or_create_engine_from_model` | OpenAI (missing key), Anthropic (missing key), Bedrock (IAM), unsupported provider | 🔲 TODO |
| T-20 | `views.health_check` | always 200 | 🔲 TODO |
| T-21 | `views.ChatbotAPIView` | missing fields → 400, happy path (mock LLM), unhandled exception → generic 500 | 🔲 TODO |
| T-22 | Existing: simple chat, transcript length, persona init, followup (basic) | Already exist | ✅ Exists |

**LLM Mocking Strategy (see Section 4)**

---

## 3 · Unit & Integration Tests — Frontend

Target: smoke tests for every route + key interaction paths.

| # | Component / hook | What to test | Status |
|---|-----------------|-------------|--------|
| F-01 | `App.js` | renders without crashing | ✅ Exists |
| F-02 | `Simulate.js` | form renders, submit navigates to /conversation | 🔲 TODO |
| F-03 | `Conversation.js` | message send → API call → message appears, delay config renders chunks sequentially | 🔲 TODO |
| F-04 | `MessageList.js` + `MessageBubble.js` | renders user vs bot messages, avatar shown when present | 🔲 TODO |
| F-05 | `TypingIndicator.js` | shown during reading phase, hidden after | 🔲 TODO |
| F-06 | `VoiceConversation.js` | WebRTC permission denied gracefully, transcript shown | 🔲 TODO |
| F-07 | API utils | axios baseURL from VITE_API_URL, error path | 🔲 TODO |

**Tool setup**: Vitest + @testing-library/react already installed. Need to wire up `msw` (Mock Service Worker) to stub API responses without hitting the backend.

---

## 4 · LLM Call Mocking — Strategy Discussion

### Problem
Tests cannot call real LLM APIs (cost, latency, nondeterminism). Every test that exercises `run_chat_round` or `run_followup_chat_round` must mock the LLM.

### Current integration point
`server/engine.py:get_or_create_engine_from_model()` returns a Kani engine. The engine is then passed to `Kani(engine, ...)` and `kani.full_round()` is awaited in a loop.

### Recommended approach: mock at the engine level

```python
# tests/conftest.py
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

@pytest.fixture
def mock_engine():
    """Fake Kani engine that returns a canned response."""
    engine = MagicMock()
    # full_round yields one ChatMessage with .text
    async def _fake_full_round(query, **kwargs):
        msg = MagicMock()
        msg.text = "Hello from mock bot."
        yield msg
    engine.full_round = _fake_full_round  # NOT how kani works — see below
    return engine
```

**Kani-specific note**: `kani.full_round()` is a method on the `Kani` instance (not the engine). The engine's job is `predict()`. Patch `kani.engines.openai.OpenAIEngine.predict` or, better, patch `server.engine.get_or_create_engine_from_model` to return a fake engine whose `predict` is an AsyncMock.

```python
@pytest.fixture
def mock_llm(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock
    fake_engine = MagicMock()
    fake_engine.predict = AsyncMock(return_value=MagicMock(text="Mocked response."))
    monkeypatch.setattr(
        "server.engine.get_or_create_engine_from_model",
        lambda *args, **kwargs: fake_engine,
    )
    return fake_engine
```

### Load testing LLM mocking (Section 5)
For Locust load tests, we need a fast deterministic response. Options:

| Option | Pros | Cons |
|--------|------|------|
| **A: Django `DEBUG_LLM=stub` env var** — `get_or_create_engine_from_model` returns a `StubEngine` that sleeps N ms and returns a fixed string | No external deps; configurable latency | Stub only used in load test env |
| **B: `httpretty` / `responses` at the HTTP level** — intercept actual OpenAI HTTP calls | Tests the real engine code path | Brittle to SDK changes |
| **C: Separate stub Django process** — run the chatbot server with `USE_STUB_LLM=true` as an env var | Closest to prod code path; reusable | Need to maintain stub |

**Recommendation**: Option A. Add a `StubEngine` class alongside `BedrockEngine`, controlled by a `STUB_LLM=true` env var. Unit tests use `monkeypatch` on `get_or_create_engine_from_model`; load tests set `STUB_LLM=true`.

---

## 5 · Load Testing

### Goals
- Baseline: sustain 50 concurrent participants in a study, each sending 1 message/minute
- Spike: handle 5× burst (250 concurrent) without 5xx responses
- Identify: Redis cache behavior under load, DB connection pooling limits, gunicorn worker count

### Tools
- **Locust** (Python, matches backend language, scriptable scenarios)

### Scenarios to script
1. **Happy path**: `initialize_conversation` → `chatbot` (10 messages) → `update_keystrokes`
2. **Idle followup**: idle for configured time → `followup` endpoint
3. **Voice session**: `GET /api/session/` → stream audio
4. **Concurrent unique conversations**: each Locust user gets a unique `conversation_id`

### Infra for load test
- Run against **staging** environment (not prod)
- `STUB_LLM=true` on the staging EB environment during load test (to isolate Django throughput from OpenAI latency)
- Monitor: EB CPU/memory, RDS `DatabaseConnections`, ElastiCache `CurrConnections`, CloudWatch `5xxError` alarm

### Metrics to collect
| Metric | Acceptable threshold |
|--------|---------------------|
| p50 latency `/api/chatbot/` (stub mode) | < 200 ms |
| p95 latency `/api/chatbot/` (stub mode) | < 500 ms |
| Error rate | < 0.1% |
| p95 latency `/api/initialize_conversation/` | < 300 ms |
| RDS max connections | < 80% of `max_connections` |

---

## 6 · Deployment Gates

### Local Development (`make start` / `make test`)
- [x] Docker Compose spins up MariaDB, Redis, Django, React, Sphinx
- [x] `make test` runs pytest inside container
- [x] `make lint` runs ruff + isort + eslint + prettier
- [ ] `make migrate` target — add `docker exec ... python manage.py migrate`
- [ ] `make test-coverage` — add `pytest --cov=chatbot --cov-report=term-missing`

### Staging (`push to staging branch`)
- [x] CI (lint + tests) now gates deployment — `needs: [ci]` added
- [x] `npm ci` (not `npm install`) for reproducible builds
- [ ] Add `python manage.py migrate --check` to CI to catch missing migrations
- [ ] Add `python manage.py migrate` step in EB deploy (via `.ebextensions/`)
- [ ] Smoke test after deploy: curl `https://dev.bot.wwbp.org/health/` and assert 200

### Production (`push to main branch`)
- [x] CI gates deployment — `needs: [ci]` added
- [x] `npm ci` for reproducible builds
- [ ] Same migration + smoke test as staging
- [ ] Require manual approval step (GitHub Environment protection rule on `main`)
- [ ] CloudWatch alarm on `HTTPCode_Target_5XX_Count > 5` in 1 min window

---

## 7 · Observability

| Item | Status |
|------|--------|
| Django rotating file logger (django.log, error.log) | ✅ Configured |
| CloudWatch log group for EB stdout | 🔲 Verify `.ebextensions/logging.config` |
| Health check endpoint `/health/` | ✅ Exists |
| Sentry (or equivalent) for exception aggregation | 🔲 Not configured |
| CloudWatch alarm: 5xx rate | 🔲 TODO |
| CloudWatch alarm: RDS CPU > 80% | 🔲 TODO |
| CloudWatch alarm: Redis memory > 80% | 🔲 TODO |

---

## 8 · Database & Migrations

| Item | Status |
|------|--------|
| All 33 migrations committed and applied on staging | 🔲 Verify |
| `python manage.py migrate --check` added to CI | 🔲 TODO |
| DB connection pool: `CONN_MAX_AGE` set for production | 🔲 TODO — default is 0 (no pooling) |
| RDS automated backups enabled, 7-day retention | 🔲 Verify |
| RDS Multi-AZ for production | 🔲 Verify |

---

## 9 · Code Quality

| Item | Status |
|------|--------|
| `DefaultBotConfiguration` duplicated in `views.py` and `followup.py` | 🔲 Refactor to shared dataclass |
| `save_chat_to_db` duplicated in `runchat.py` and `followup.py` | 🔲 Remove from followup.py, import from runchat |
| `config.py:load_config()` creates Bot without `ai_model` FK | 🔲 Fix or deprecate this codepath |
| Engine instances are module-level globals (not shared across Gunicorn workers) | 🔲 Document / decide on caching strategy |
| `import traceback; traceback.print_exc()` in `runchat.save_chat_to_db` | 🔲 Replace with `logger.exception()` |
| Inline `from django.core.serializers...` inside view method | 🔲 Move to top-level import |
| Ruff + isort passing clean | 🔲 Run before merge |
| mypy passing clean | 🔲 Run before merge |

---

## 10 · Pre-Launch Sign-off

- [ ] All S-xx items ✅
- [ ] All T-01 through T-22 ✅ (or explicitly deferred with owner)
- [ ] Load test at 50 CCU passes acceptance thresholds
- [ ] Staging smoke test passes (manual click-through of full chat flow)
- [ ] Secrets rotated from any values that existed in git history
- [ ] Admin password changed from default
- [ ] `DEBUG=False` confirmed in production EB environment variables
- [ ] `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` set in EB env vars
- [ ] `SECRET_KEY` generated fresh (`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- [ ] DNS, SSL certificate, CloudFront confirmed on production domain

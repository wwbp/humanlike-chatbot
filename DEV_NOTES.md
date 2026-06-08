# Dev Notes — TDD Audit & Main Loop Walkthrough

Working scratch pad. Edit freely. Not a formal doc.

---

## — Decision Log —

| # | Decision |
|---|----------|
| D-01 | Bot config in init response (Option A): `initialize_conversation` returns a `bot_config` dict; `Conversation.js` reads from it instead of calling `GET /api/bots/` |
| D-02 | Double bot fetch: fix BEFORE writing tests so tests reflect the clean design |
| D-03 | `/api/update_keystrokes/` is a Qualtrics integration point, not a frontend call; note in README, do not call from Conversation.js |
| D-04 | Consolidate `engine_instances` / `followup_engine_instances` into one shared module; verify no other reason for separation first |
| D-05 | `revealChunks` legacy path is dead; remove it under tests confirming no regressions |
| D-06 | `save_chat_to_db` in followup.py is a duplicate of runchat.py; import from runchat |
| D-07 | Style: no unnecessary abstraction; functional + modular; mock LLM at engine factory level via `conftest.py` fixture |

## — PR Chain —

| PR | Branch | Scope |
|----|--------|-------|
| PR-01 | `pr/init-bot-config` | `initialize_conversation` returns `bot_config` + tests; frontend drops `GET /api/bots/` call; keystroke README note |
| PR-02 | `pr/fix-double-bot-fetch` | Eliminate second `Bot.objects.get` in `ChatbotAPIView`; chatbot view tests |
| PR-03 | `pr/consolidate-engines` | Merge `followup_engine_instances` into shared `engine_instances`; remove dead `engine_instances` in views.py; engine tests |
| PR-04 | `pr/followup-dedup` | Remove duplicate `save_chat_to_db` in followup.py; followup service tests |
| PR-05 | `pr/remove-dead-delay` | Remove `revealChunks` legacy path from Conversation.js; frontend tests with Vitest |
| PR-06 | `pr/tdd-api-coverage` | Tests for all remaining view endpoints (health, bots CRUD, avatar-upload, session, voice) |
| PR-07 | `pr/frontend-tests` | Wire up `msw` + write tests for Simulate.js, Conversation.js, MessageList.js |

---

## 0 · `make test` — Current State & Gap

```
make test
  → docker exec backend: pytest
      --reuse-db          ← reuses existing test DB between local runs
      --tb=short
      --strict-markers
      --disable-warnings
      testpaths = chatbot/tests   ← only backend Python tests

make test (CI): pytest --create-db  ← creates fresh DB every time
```

**Frontend tests are completely disconnected:**
```
cd generic_chatbot_frontend && npm test -- --run
  → vitest (jsdom environment)
  → only ONE test exists: App.test.js — renders without crashing
```

**The gap:** `make test` runs 0 frontend tests. CI does run them, but locally they
are invisible. Plan: add a frontend test target to Makefile and update `make test`
to call both.

---

## 1 · Full Request Lifecycle — Text Chat (Main Loop)

### Phase 0 — Frontend Boot

```
User → browser → /
  → App.js renders <Router>
  → Route "/" → <Simulate />

Simulate.js:
  - form fields: bot_name, conversation_id, participant_id, study_name, user_group
  - handleSubmit():
      if bot_name.includes('-voice') → navigate to /voice-conversation?params
      else                           → navigate to /conversation?params
```

Nothing talks to the backend yet.

---

### Phase 1 — Conversation Initialization (two useEffects fire in parallel on mount)

```
Conversation.js mount
  │
  ├── useEffect #1: GET /api/bots/          ← ⚠️  SEE OBSERVATION #1
  │     → finds bot by name in list
  │     → setBotConfig(bot)   used for: follow_up_on_idle, idle_time_minutes,
  │                                     chunk_messages, humanlike_delay
  │
  └── useEffect #2: POST /api/initialize_conversation/
        body: { bot_name, conversation_id, participant_id,
                study_name, user_group, survey_id, survey_meta_data }
        │
        └── InitializeConversationAPIView.post()   [SYNC view]
              1. JSON parse body
              2. Validate: bot_name AND conversation_id required
              3. Bot.objects.get(name=bot_name)          → 404 if missing
              4. load_conversation_history(conversation_id)
                    → Conversation.objects.get(conversation_id=...)
                    → Utterance.objects.filter(conversation).order_by('created_time')
                    → build cache-format list + frontend-format list
                    → cache.set(f"conversation_cache_{conversation_id}", ..., 3600)
                    → return (conversation, messages)  OR  (None, []) if not found
              5a. IF existing conversation:
                    → return { conversation_id, initial_utterance (from DB),
                               existing_messages, is_existing: True }
              5b. IF new conversation:
                    → randomly_select_persona(bot)
                        → random.choice(list(bot.personas.all()))  or None
                    → bot_config = model_to_dict(bot) + personas list  → JSON
                    → Conversation.objects.create(
                          conversation_id, bot_name, bot_config,
                          participant_id, initial_utterance=bot.initial_utterance,
                          study_name, user_group, survey_id, survey_meta_data,
                          started_time=datetime.now(),
                          selected_persona=selected_persona
                       )
                    → if bot.initial_utterance:
                          async_to_sync(save_chat_to_db)(speaker_id="assistant", ...)
                          → Utterance.objects.create(...)
                    → return { conversation_id, initial_utterance, existing_messages,
                               is_existing: False }

        └── on success → fetch avatar:
              GET /api/avatar/{bot_name}/?conversation_id=...&condition=...
              → AvatarDetailAPIView.get()  [public, no auth]
              → on failure → graceful fallback (avatar_type='none', image_url=null)

        └── frontend sets state:
              if data.initial_utterance → setMessages([{sender:'AI Chatbot',content:...}])
              if data.existing_messages.length > 0 → setMessages(data.existing_messages)
              setAvatar(avatar_data)
```

---

### Phase 2 — User Sends a Message (Main Loop)

```
User types → ChatInput.js → form submit → Conversation.js handleSubmit()

  1. if botConfig?.follow_up_on_idle && !botConfig?.recurring_followup:
       POST /api/followup/  { reset_flag: true }   ← clears "sent once" Redis key
  2. setMessages(prev => [...prev, {sender:'You', content:message}])
  3. setMessage('')
  4. requestStartTime = Date.now()

  POST /api/chatbot/
    body: { message, bot_name, conversation_id, participant_id }
    │
    └── ChatbotAPIView.post()   [ASYNC view]
          1. JSON parse body
          2. Validate: message AND bot_name AND conversation_id required
          3. await run_chat_round(bot_name, conversation_id, participant_id, message)
                │
                └── run_chat_round()   [the CORE function]
                      1. Guard: if message.startswith("[FOLLOW-UP REQUEST]") → return warning
                      2. Bot.objects.prefetch_related("personas","ai_model__provider").get(name=bot_name)
                                                                              [DB QUERY #1]
                      3. await sync_to_async(moderate_message)(message, bot)
                            → if not OPENAI_API_KEY → return ""  (skip)
                            → if not ModerationSettings.objects.first().enabled → return ""
                            → OpenAI().moderations.create(input=message, model="omni-moderation-latest")
                            → for each category: if score > bot.get_moderation_threshold(cat) → return cat
                            → return ""  (clean)
                      4a. if blocked:
                            → warning_text = "Your message could not be processed..."
                            → save_chat_to_db(user)    [Utterance INSERT]
                            → save_chat_to_db(warning) [Utterance INSERT]
                            → return warning_text
                      4b. if clean:
                            → cache_key = f"conversation_cache_{conversation_id}"
                            → conversation_history = cache.get(cache_key, [])
                            → if cache empty:
                                  Conversation.objects.get(conversation_id=...)  [DB QUERY #2]
                                  Utterance.objects.filter(conversation).order_by('created_time')  [DB QUERY #3]
                                  build conversation_history list
                                  cache.set(cache_key, conversation_history, 3600)
                            → apply max_transcript_length:
                                  -1 → use all
                                   0 → clear []
                                   N → [-N:]
                            → append user message to history
                            → format as Kani ChatMessage list
                            → Conversation.objects.select_related("selected_persona").get(...)  [DB QUERY #4]
                            → generate_system_prompt(bot, selected_persona)
                                  → bot.prompt + persona instructions if any
                            → engine = get_or_create_engine_from_model(bot.ai_model, engine_instances)
                                  → if key not in engine_instances: initialize engine (network/IAM)
                                  → return cached engine
                            → kani = Kani(engine, system_prompt=..., chat_history=formatted_history)
                            → async for msg in kani.full_round(query=latest_user_message):
                                  response_text += msg.text
                            → response_text = response_text.strip()
                            → chat_history_json = JSON of history before bot response
                            → append bot response to conversation_history
                            → cache.set(cache_key, conversation_history, 3600)
                            → save_chat_to_db(user)     [Utterance INSERT]
                            → save_chat_to_db(bot, instruction_prompt=system_prompt,
                                              chat_history_used=chat_history_json)  [Utterance INSERT]
                            → return response_text

          4. await sync_to_async(Bot.objects.get)(name=bot_name)   [DB QUERY #5]  ← ⚠️ SEE OBS #2
          5. human_like_chunks(response_text) if use_chunks else [response_text]
          6. calculate_typing_delays(message, response_chunks, bot)
               → if not bot.humanlike_delay → return zero delays (instant)
               → else → compute reading_time, writing_delay per segment, inter_segment_delay
          7. return JsonResponse({
               message, response, response_chunks,
               bot_name, humanlike_delay, chunk_messages,
               delay_config: {
                 reading_time,       ← seconds to wait before showing first segment
                 min_reading_delay,  ← floor on reading_time
                 response_segments: [
                   { content, writing_delay, inter_segment_delay },
                   ...
                 ]
               }
             })

  ← Conversation.js receives response
    backendTimeMs = Date.now() - requestStartTime

    if delayConfig.response_segments:    ← always true (new system)
      executeTypingSequence(response_segments, delayConfig, backendTimeMs)
        1. effectiveReadingTime = max(min_reading_delay, reading_time - backendLatencySec)
        2. setTimeout(effectiveReadingTime * 1000) → displayResponseSegments()
              for each segment:
                setTimeout(cumulativeDelay)        → setIsTyping(true)
                setTimeout(cumulative + writing_delay) → setIsTyping(false)
                                                         setMessages([...prev, segment])
                cumulativeDelay += writing_delay + inter_segment_delay

    else:    ← legacy path (dead code — server always sends response_segments now)
      revealChunks(...)
```

---

### Phase 3 — Idle Follow-up (background timer)

```
Conversation.js
  useEffect([botConfig, botName, conversationId, participantId, apiUrl, messages.length])
  → fires every time a message arrives (messages.length changes)
  → if botConfig.follow_up_on_idle:
      setTimeout(idle_time_minutes * 60 * 1000) → POST /api/followup/
        body: { bot_name, conversation_id, participant_id }
        │
        └── FollowupAPIView.post()   [ASYNC view]
              → generate_followup_message(bot_name, conversation_id, participant_id)
                    1. bot.follow_up_on_idle check
                    2. bot.follow_up_instruction_prompt check
                    3. is_user_idle(conversation_id, bot.idle_time_minutes)
                          → Utterance.objects.filter(speaker_id='user').order_by('-created_time').first()
                          → compare created_time to now - idle_time_minutes
                    4. if not recurring: check Redis "followup_sent_once_{conversation_id}"
                    5. rate-limit: check Redis "followup_sent_{conversation_id}" (30s TTL)
                    6. followup_instruction = f"[FOLLOW-UP REQUEST] {bot.follow_up_instruction_prompt}"
                    7. run_followup_chat_round(...)
                          → same as run_chat_round BUT:
                              - uses followup_engine_instances (SEPARATE dict from runchat)  ← OBS #3
                              - does NOT save followup instruction to DB
                              - saves only bot response
              → Bot.objects.get(name=bot_name)  [another fetch for chunk/delay config]
              → return JsonResponse({ response, response_chunks, delay_config, ... })
  ← frontend: same executeTypingSequence rendering
```

---

### Phase 4 — Keystroke Logging (on unload / periodic)

```
POST /api/update_keystrokes/
  body: { conversation_id, total_time_on_page, total_time_away_from_page,
          keystroke_count, timestamp }
  → update_keystrokes()
      → Keystroke.objects.create(...)   ← no FK to Conversation, just string ID

⚠️  OBS #4: ChatInput.js or Conversation.js handles this — need to verify WHERE
            the keystroke endpoint is called from in the frontend.
```

---

## 2 · Observations & Questions (for TDD planning)

### OBS #1 — Frontend calls `/api/bots/` without auth (BREAKING)
`Conversation.js useEffect #1` does `GET /api/bots/` to get bot config. We just
locked that endpoint to staff-only. Without a logged-in staff session in the browser,
this silently 403s → `botConfig` stays null → idle follow-up never fires.

**Decision needed:** How does the frontend get bot config at conversation start?
Options:
- A) Add `bot_config` to `initialize_conversation` response (bot_config JSON is
     already snapshotted in the Conversation model — use that).
- B) Create a separate public `GET /api/bots/<name>/public/` endpoint that
     returns only non-sensitive fields (no system prompt).
- C) Keep `/api/bots/` public. Risk: anyone can enumerate all bot configs.

Leaning toward **A**: the `initialize_conversation` response already has all
the info. No new endpoint needed.

---

### OBS #2 — Double bot fetch in ChatbotAPIView (performance)
`run_chat_round` fetches Bot → `ChatbotAPIView.post` fetches Bot AGAIN.
That's 2 identical `Bot.objects.get(name=bot_name)` queries per request.

**Plan:** `run_chat_round` should return the bot object alongside the response text,
or `ChatbotAPIView` should pass the pre-fetched bot in. Needs to be thread-safe
(async context).

---

### OBS #3 — Two separate engine instance dicts
`runchat.py: engine_instances = {}`  — used for regular chat
`followup.py: followup_engine_instances = {}` — used for followup

Same engine will be initialized twice (once per Gunicorn worker, once per dict).
This doubles startup cost and doubles memory per worker for bots that use followup.

**Plan:** Consolidate into one dict, imported from a single module.

---

### OBS #4 — Keystroke logging location unclear
Can't find `POST /api/update_keystrokes/` call in Conversation.js or ChatInput.js.
Need to check the other components. Could be missing entirely (data silently lost).

---

### OBS #5 — `is_existing` resume logic is fragile
On resume: `existing_messages` contains all messages including initial utterance.
Frontend's two `if` blocks both fire → second overwrites first → correct result,
but by accident. If `initial_utterance` is populated but `existing_messages` is
empty, only the initial utterance shows (could happen on a broken DB state).

---

### OBS #6 — `messages.length` as useEffect dep for idle timer
Every time a new message arrives, the idle timer `useEffect` re-fires, clearing
the old timer and starting a new one. This means the idle clock correctly resets
after each message, including bot messages (not just user messages). That may or
may not be intended — arguably idle should only reset on USER messages.

---

### OBS #7 — Legacy delay path is dead code
`revealChunks()` in Conversation.js is the old delay system. The backend always
returns `delay_config.response_segments` now. The `else` branch in `handleSubmit`
can never be reached by a current server response. Safe to remove, but test first.

---

### OBS #8 — `generate_system_prompt` exception swallows errors
```python
except Exception as e:
    logger.error(f"Error generating system prompt: {e}")
    return bot.prompt.strip() if bot.prompt else ""
```
If the persona object is corrupted, we silently fall back to bot-only prompt.
The LLM call still proceeds. This is intentional resilience, but tests should
confirm the fallback fires correctly.

---

## 3 · TDD Test Plan — Ordered by Execution Path

The goal: trace every branch in the main loop and write a test for each one.
Mock strategy: patch `server.engine.get_or_create_engine_from_model` in a
`conftest.py` fixture. All LLM calls become sync stubs returning a canned string.

### Layer 1 — Pure functions (no DB, no async, no network)
1. `post_processing.human_like_chunks` — all branching paths      [EXISTS]
2. `post_processing.calculate_typing_delays` — delay=on, delay=off [EXISTS]
3. `post_processing.create_instant_display_response`              [EXISTS implied]
4. `runchat.generate_system_prompt`                               [MISSING]
   - bot only
   - bot + persona
   - exception in persona access → fallback
5. `moderation.is_moderation_enabled`                             [MISSING]
   - no ModerationSettings row → returns True (default enabled)
   - row exists enabled=True
   - row exists enabled=False

### Layer 2 — Service functions (DB + Redis, LLM mocked)
6. `conversation.randomly_select_persona`                         [MISSING]
   - empty pool → None
   - single persona → that one
   - multiple → one chosen (mock random.choice)
7. `conversation.load_conversation_history`                       [MISSING]
   - conversation not found → (None, [])
   - conversation found, 0 utterances → (convo, [])
   - conversation found, N utterances → correct list + cache populated
8. `InitializeConversationAPIView`                                [PARTIAL - exists test]
   - missing fields → 400
   - bad JSON → 400
   - bot not found → 404
   - new conversation → 200 + DB row + initial utterance saved
   - existing conversation → 200 + existing_messages
9. `runchat.run_chat_round`                                       [PARTIAL - mock LLM]
   - [FOLLOW-UP REQUEST] prefix guard
   - clean message + cache warm path
   - clean message + cache miss → loads from DB
   - max_transcript_length=0 (stateless)
   - max_transcript_length=N (truncation)
   - max_transcript_length=-1 (unlimited)
   - moderation blocks → warning saved, returns generic message
   - LLM call → mocked → response saved to DB
10. `moderation.moderate_message`                                 [PARTIAL - global toggle exists]
    - no API key → returns ""
    - global disabled → returns ""
    - score under threshold → returns ""
    - score over threshold → returns category name
11. `followup.is_user_idle`                                       [MISSING]
12. `followup.generate_followup_message`                          [MISSING]
    - follow_up_on_idle=False → (None, error msg)
    - no instruction prompt → (None, error msg)
    - user not idle → (None, "not idle")
    - cooldown active → (None, "recently sent")
    - recurring=False + already sent → (None, "already sent")
    - happy path → (response_text, None)

### Layer 3 — API views (HTTP request/response)
13. `GET /health/`                                                [MISSING]
14. `POST /api/chatbot/` — missing fields → 400                  [MISSING]
15. `POST /api/chatbot/` — happy path (LLM mocked)               [PARTIAL]
16. `POST /api/chatbot/` — exception → generic 500, no str(e)    [MISSING]
17. `GET /api/bots/` — non-staff → 403                           [MISSING]
18. `GET /api/bots/` — staff → 200                               [MISSING]
19. `POST /api/bots/` — non-staff → 403                          [MISSING]
20. `POST /api/bots/` — model not found → 400                    [MISSING]
21. `POST /api/bots/` — happy path → 201                         [MISSING]
22. `GET /api/session/` — missing conversation_id → 400          [MISSING]
23. `GET /api/session/` — no API key → 503                       [MISSING]
24. `POST /api/avatar-upload/` — non-staff → 403                 [MISSING]
25. `POST /api/avatar-upload/` — bad content-type → 415          [MISSING]
26. `POST /api/avatar-upload/` — path traversal filename → 400   [MISSING]
27. `POST /api/update_keystrokes/` — happy path                  [MISSING]
28. `POST /api/update_keystrokes/` — missing fields → 400        [MISSING]

### Layer 4 — Engine initialization (mocked API keys)
29. `OpenAIEngine` — missing key → ValueError                    [MISSING]
30. `AnthropicEngine` — missing key → ValueError                 [MISSING]
31. `BedrockEngine` — explicit credentials vs IAM chain          [MISSING]
32. Unsupported provider → ValueError                             [MISSING]

### Layer 5 — Frontend (Vitest + Testing Library)
33. `Simulate.js` — renders form, fill + submit → navigates       [MISSING]
34. `Simulate.js` — bot_name with '-voice' → /voice-conversation  [MISSING]
35. `Conversation.js` — initialize_conversation called on mount    [MISSING]
36. `Conversation.js` — send message → chatbot called → chunks shown [MISSING]
37. `Conversation.js` — executeTypingSequence timer behavior       [MISSING]
38. `App.js` — renders without crashing                           [EXISTS]

---

## 4 · Questions to Resolve Before Writing Tests

Q1: How does the frontend get bot config going forward (obs #1 above)?
    → Decision: include in initialize_conversation response, or new public endpoint?

Q2: Do we fix the double bot fetch (obs #2) before or after writing tests?
    → If before: tests need to cover the refactored signature
    → If after: we test the current code, then refactor under green tests (clean TDD)

Q3: Consolidate engine_instances dicts (obs #3)?
    → Same question: before or after?

Q4: Should idle follow-up reset on bot messages OR only user messages?
    → Affects whether messages.length is correct useEffect dependency

Q5: Frontend tests — do we mock the API with `msw` (mock service worker) or
    mock individual `fetch` calls? msw is more realistic but requires setup.

---

## 5 · Open Items

- [ ] Find where `/api/update_keystrokes/` is called from in the frontend
- [ ] Decide Q1 (bot config in init response vs public endpoint)
- [ ] Decide Q2 (double bot fetch — refactor before or after tests)
- [ ] Add frontend test runner to `make test`
- [ ] Add `make test-frontend` target
- [ ] Write `conftest.py` with mock LLM fixture

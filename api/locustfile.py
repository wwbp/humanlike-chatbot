"""
Load test for the ChatbotLab API.

Target scenario
---------------
- 1 000 concurrent users (configurable via LOCUST_MAX_USERS)
- Each user maintains one persistent conversation and sends messages with
  a random wait drawn from constant_throughput(), which automatically adjusts
  the inter-request pause so the *total* RPS across all users equals
  LOCUST_TARGET_RPS regardless of response latency.
- Load shape: gentle ramp over ~10 min, then hold for 15 min.

Quick start
-----------
    pip install locust
    export LOAD_TEST_BOT_NAME=<your-bot-name>
    export MOCK_LLM=true                  # set on the server, not here
    locust -f locustfile.py --host http://localhost:80

Run headless (CI / automated):
    locust -f locustfile.py --host http://localhost:80 \
           --headless --run-time 25m \
           --html load_test_report.html

Tuning RPS
----------
    LOCUST_TARGET_RPS=200  # total RPS target
    LOCUST_MAX_USERS=1000  # peak user count in the ramp shape
    Per-user rate = TARGET_RPS / MAX_USERS = 0.2 req/s = 1 req / 5 s on avg.
    With MOCK_LLM p50=900 ms the effective wait is ~4.1 s → 200 RPS at 1 000 users.
    Without mock (real LLM p50~1 200 ms) expect ~155 RPS at 1 000 users; raise
    LOCUST_MAX_USERS to ~1 300 to compensate.
"""

import logging
import os
import random
import uuid

from locust import HttpUser, LoadTestShape, constant_throughput, events, task
from locust.exception import StopUser

logger = logging.getLogger("locust.chatlab")

# ── Configuration (override via env vars) ────────────────────────────────────

# Host header override: when driving the ALB directly (bypassing CloudFront),
# set this to the app's allowed host (e.g. dev.bot.wwbp.org). The raw ALB
# hostname is rejected by Django ALLOWED_HOSTS with HTTP 400. Empty = no override.
LOAD_TEST_HOST_HEADER = os.getenv("LOAD_TEST_HOST_HEADER", "")

LOAD_TEST_BOT = os.getenv("LOAD_TEST_BOT_NAME", "")
LOAD_TEST_STUDY = os.getenv("LOAD_TEST_STUDY", "load_test")
LOAD_TEST_USER_GROUP = os.getenv("LOAD_TEST_USER_GROUP", "perf")
LOCUST_TARGET_RPS = float(os.getenv("LOCUST_TARGET_RPS", "200"))
LOCUST_MAX_USERS = int(os.getenv("LOCUST_MAX_USERS", "1000"))

# LOCUST_QUICK=true: ramp to full users in 30 s then hold — for iteration/local tests.
# LOCUST_RUN_TIME_S: hard stop after N seconds (the shape itself returns None).
#   LoadTestShape ignores --run-time, so this is the only reliable way to end a run.
LOCUST_QUICK = os.getenv("LOCUST_QUICK", "false").lower() == "true"
LOCUST_RUN_TIME_S = int(os.getenv("LOCUST_RUN_TIME_S", "0"))  # 0 = use shape default

_PER_USER_RPS = LOCUST_TARGET_RPS / LOCUST_MAX_USERS  # e.g. 0.2 req/s

# Representative user messages — varied to exercise cache/history paths.
_MESSAGES = [
    "How are you doing today?",
    "Tell me something interesting.",
    "What do you think about that?",
    "Can you elaborate on that a bit more?",
    "I see. Go on.",
    "That makes a lot of sense to me.",
    "What else can you tell me?",
    "I'm curious — how does that work?",
    "Thanks for sharing that.",
    "What would you recommend I do next?",
    "Can you give me an example?",
    "Why do you think that is?",
    "Interesting perspective. Tell me more.",
    "I hadn't thought of it that way before.",
    "What are your thoughts on the topic?",
]


# ── Virtual user ─────────────────────────────────────────────────────────────


class ConversationUser(HttpUser):
    """
    Simulates one participant in a chat study.

    Lifecycle:
      on_start  → POST /api/initialize_conversation/  (once per user)
      @task     → POST /api/chatbot/                  (repeated, rate-limited)
    """

    wait_time = constant_throughput(_PER_USER_RPS)

    def on_start(self):
        if not LOAD_TEST_BOT:
            logger.error("LOAD_TEST_BOT_NAME env var is not set — aborting user.")
            raise StopUser

        if LOAD_TEST_HOST_HEADER:
            self.client.headers["Host"] = LOAD_TEST_HOST_HEADER

        self.bot_name = LOAD_TEST_BOT
        self.participant_id = f"lt_{uuid.uuid4().hex[:12]}"
        self.conversation_id = f"lt_{uuid.uuid4().hex}"
        self._ready = False

        with self.client.post(
            "/api/initialize_conversation/",
            json={
                "conversation_id": self.conversation_id,
                "bot_name": self.bot_name,
                "participant_id": self.participant_id,
                "study_name": LOAD_TEST_STUDY,
                "user_group": LOAD_TEST_USER_GROUP,
                "survey_id": "lt_survey",
                "survey_meta_data": "{}",
            },
            name="POST /api/initialize_conversation/",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                self._ready = True
            else:
                resp.failure(f"init failed {resp.status_code}: {resp.text[:120]}")
                raise StopUser

    @task
    def send_message(self):
        if not self._ready:
            return

        with self.client.post(
            "/api/chatbot/",
            json={
                "message": random.choice(_MESSAGES),
                "bot_name": self.bot_name,
                "conversation_id": self.conversation_id,
                "participant_id": self.participant_id,
            },
            name="POST /api/chatbot/",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"{resp.status_code}: {resp.text[:120]}")


# ── Load shape ────────────────────────────────────────────────────────────────


class ChatLabLoadShape(LoadTestShape):
    """
    Two modes controlled by env vars:

    Normal (LOCUST_QUICK=false, default):
      Gradual ramp to LOCUST_MAX_USERS over ~10 min, hold for 15 min, then stop.
      Elapsed   Users    Spawn rate
        0-60s    10%       2/s
       60-180s   30%       3/s
      180-360s   60%       5/s
      360-600s  100%      10/s
      600-1500s 100%      (hold)

    Quick (LOCUST_QUICK=true):
      Ramp to full users in 30 s, hold until LOCUST_RUN_TIME_S (default 330 s).
      Designed for local iteration — reaches target RPS immediately so every
      minute of run time is steady-state signal.

    LOCUST_RUN_TIME_S:
      Hard stop at this many seconds. Required when LOCUST_QUICK=true.
      LoadTestShape ignores --run-time, so this is the only reliable end signal.
    """

    _MAX = LOCUST_MAX_USERS

    def _stages(self):
        if LOCUST_QUICK:
            end = LOCUST_RUN_TIME_S if LOCUST_RUN_TIME_S > 0 else 330
            # Cap spawn rate at 25/s — avoids a DB connection burst at startup
            # while still ramping to full load in ~10s for small MAX_USERS values.
            return [
                {
                    "duration": max(30, self._MAX // 25),
                    "users": self._MAX,
                    "spawn_rate": 25,
                },
                {"duration": end, "users": self._MAX, "spawn_rate": 25},
            ]
        return [
            {"duration": 60, "users": max(1, self._MAX // 10), "spawn_rate": 2},
            {"duration": 180, "users": max(1, self._MAX * 3 // 10), "spawn_rate": 3},
            {"duration": 360, "users": max(1, self._MAX * 6 // 10), "spawn_rate": 5},
            {"duration": 600, "users": self._MAX, "spawn_rate": 10},
            {"duration": 1500, "users": self._MAX, "spawn_rate": 10},
        ]

    def tick(self):
        run_time = self.get_run_time()
        if LOCUST_RUN_TIME_S > 0 and run_time >= LOCUST_RUN_TIME_S:
            return None  # hard stop
        for stage in self._stages():
            if run_time <= stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None  # end of shape


# ── Startup validation ────────────────────────────────────────────────────────


@events.init.add_listener
def on_locust_init(environment, **_kw):
    if not LOAD_TEST_BOT:
        logger.warning(
            "LOAD_TEST_BOT_NAME is not set. Every user will abort on start.\n"
            "  export LOAD_TEST_BOT_NAME=<your-bot-name>"
        )
    logger.info(
        "Load test config: bot=%r target_rps=%.0f max_users=%d per_user_rps=%.3f",
        LOAD_TEST_BOT,
        LOCUST_TARGET_RPS,
        LOCUST_MAX_USERS,
        _PER_USER_RPS,
    )

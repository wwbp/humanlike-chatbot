"""
Tests for the MOCK_LLM load-testing infrastructure.

Covers:
- MOCK_LLM=true in moderation: skips OpenAI, sleeps realistic latency, returns ""
- MOCK_LLM=true in runchat: skips Kani, still writes user + bot utterances to DB
- RequestTimingMiddleware: logs timing on both sync and async paths
- Settings: CONN_MAX_AGE is set, timing middleware is registered
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from asgiref.sync import sync_to_async
from django.conf import settings
from django.test import RequestFactory, TestCase

from chatbot.models import Bot, Conversation, Model, Utterance
from chatbot.services.runchat import run_chat_round

# ── Moderation mock ───────────────────────────────────────────────────────────


class TestMockModeration(TestCase):
    def setUp(self):
        Model.get_or_create_default_models()
        self.model = Model.objects.filter(provider__name="OpenAI").first()
        self.bot = Bot.objects.create(
            name=f"mod_bot_{uuid.uuid4().hex[:8]}",
            prompt="Test.",
            ai_model=self.model,
        )

    def tearDown(self):
        self.bot.delete()

    @patch("chatbot.services.moderation._MOCK_LLM", True)
    @patch("chatbot.services.moderation.time.sleep")
    def test_mock_skips_openai_call(self, mock_sleep):
        from chatbot.services.moderation import moderate_message

        result = moderate_message("hello world", self.bot)
        assert result == ""
        mock_sleep.assert_called_once()

    @patch("chatbot.services.moderation._MOCK_LLM", True)
    @patch("chatbot.services.moderation.time.sleep")
    def test_mock_sleep_is_positive_and_bounded(self, mock_sleep):
        """lognormal(p50=220ms, sigma=0.4) should stay in a sane range."""
        from chatbot.services.moderation import moderate_message

        moderate_message("test", self.bot)
        elapsed = mock_sleep.call_args[0][0]
        assert 0 < elapsed < 5.0

    @patch("chatbot.services.moderation._MOCK_LLM", True)
    @patch("chatbot.services.moderation.OpenAI")
    @patch("chatbot.services.moderation.time.sleep")
    def test_mock_never_calls_openai(self, mock_sleep, mock_openai_cls):
        from chatbot.services.moderation import moderate_message

        moderate_message("some message", self.bot)
        mock_openai_cls.assert_not_called()

    @patch("chatbot.services.moderation._MOCK_LLM", False)
    def test_real_path_skips_when_no_api_key(self):
        """Without an API key the real path should still return '' gracefully."""
        from chatbot.services.moderation import moderate_message

        with patch("chatbot.services.moderation.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            result = moderate_message("hello", self.bot)
        assert result == ""


# ── Runchat mock ──────────────────────────────────────────────────────────────


@pytest.fixture
def bot_and_conv(db):
    Model.get_or_create_default_models()
    model = Model.objects.filter(provider__name="OpenAI").first()
    bot = Bot.objects.create(
        name=f"rc_bot_{uuid.uuid4().hex[:8]}",
        prompt="You are a test assistant.",
        ai_model=model,
    )
    conv = Conversation.objects.create(
        conversation_id=f"conv_{uuid.uuid4().hex}",
        bot_name=bot.name,
        participant_id="p_mock",
    )
    yield bot, conv
    Utterance.objects.filter(conversation=conv).delete()
    conv.delete()
    bot.delete()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_mock_llm_skips_kani(bot_and_conv):
    """MOCK_LLM=true must not instantiate or call Kani."""
    bot, conv = bot_and_conv

    with (
        patch("chatbot.services.runchat._MOCK_LLM", True),
        patch(
            "chatbot.services.runchat.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep,
        patch("chatbot.services.runchat.Kani") as mock_kani_cls,
        patch("chatbot.services.runchat.moderate_message", return_value=""),
    ):
        response, returned_bot = await run_chat_round(
            bot_name=bot.name,
            conversation_id=conv.conversation_id,
            participant_id="p_mock",
            message="Hello",
        )

    assert response == "This is a mock response for load testing."
    mock_sleep.assert_called_once()
    mock_kani_cls.assert_not_called()
    assert returned_bot.name == bot.name


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_mock_llm_writes_both_utterances_to_db(bot_and_conv):
    """DB writes must still happen in mock mode — they are part of what we load-test."""
    bot, conv = bot_and_conv

    with (
        patch("chatbot.services.runchat._MOCK_LLM", True),
        patch("chatbot.services.runchat.asyncio.sleep", new_callable=AsyncMock),
        patch("chatbot.services.runchat.moderate_message", return_value=""),
    ):
        await run_chat_round(
            bot_name=bot.name,
            conversation_id=conv.conversation_id,
            participant_id="p_mock",
            message="How are you?",
        )

    utterances = await sync_to_async(list)(
        Utterance.objects.filter(conversation=conv).order_by("created_time")
    )
    assert len(utterances) == 2
    speakers = {u.speaker_id for u in utterances}
    assert speakers == {"user", "assistant"}
    bot_msg = next(u for u in utterances if u.speaker_id == "assistant")
    assert bot_msg.text == "This is a mock response for load testing."


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_mock_llm_updates_redis_cache(bot_and_conv):
    """Redis cache must be populated in mock mode."""
    from django.core.cache import cache

    bot, conv = bot_and_conv

    with (
        patch("chatbot.services.runchat._MOCK_LLM", True),
        patch("chatbot.services.runchat.asyncio.sleep", new_callable=AsyncMock),
        patch("chatbot.services.runchat.moderate_message", return_value=""),
    ):
        await run_chat_round(
            bot_name=bot.name,
            conversation_id=conv.conversation_id,
            participant_id="p_mock",
            message="Test cache",
        )

    cached = cache.get(f"conversation_cache_{conv.conversation_id}")
    assert cached is not None
    assert len(cached) == 2  # user message + bot response
    assert cached[-1]["role"] == "assistant"
    assert cached[-1]["content"] == "This is a mock response for load testing."


# ── RequestTimingMiddleware ───────────────────────────────────────────────────


class TestRequestTimingMiddleware(TestCase):
    def test_sync_path_logs_and_returns_response(self):
        from chatbot.middleware import RequestTimingMiddleware

        fake_response = MagicMock(status_code=200)
        get_response = MagicMock(return_value=fake_response)

        mw = RequestTimingMiddleware(get_response)
        factory = RequestFactory()
        request = factory.get("/health/")

        with self.assertLogs("chatbot.middleware", level="INFO") as logs:
            response = mw(request)

        assert response is fake_response
        assert any("perf" in line and "200" in line for line in logs.output)

    @pytest.mark.asyncio
    async def test_async_path_logs_and_returns_response(self):
        from chatbot.middleware import RequestTimingMiddleware

        fake_response = MagicMock(status_code=200)

        async def async_get_response(request):
            return fake_response

        mw = RequestTimingMiddleware(async_get_response)
        factory = RequestFactory()
        request = factory.get("/api/chatbot/")

        with self.assertLogs("chatbot.middleware", level="INFO") as logs:
            response = await mw.__acall__(request)

        assert response is fake_response
        assert any("perf" in line and "200" in line for line in logs.output)


# ── Settings sanity ───────────────────────────────────────────────────────────


class TestSettings(TestCase):
    def test_conn_max_age_is_set(self):
        db_cfg = settings.DATABASES["default"]
        assert "CONN_MAX_AGE" in db_cfg
        assert isinstance(db_cfg["CONN_MAX_AGE"], int)
        assert db_cfg["CONN_MAX_AGE"] >= 0

    def test_timing_middleware_registered(self):
        assert "chatbot.middleware.RequestTimingMiddleware" in settings.MIDDLEWARE

    def test_conn_health_checks_enabled(self):
        assert settings.DATABASES["default"].get("CONN_HEALTH_CHECKS") is True

"""
Tests for FollowupAPIView  (POST /api/followup/)

Coverage:
  - Input validation (missing fields → 400)
  - reset_flag path (clears once-flag, returns 200)
  - follow_up_on_idle=False → 400
  - User not idle → 400
  - Rate limiting: second call within 30 s cooldown → 400
  - Dedup: recurring_followup=False, flag already set → 400
  - Happy path: response shape, is_followup=True, delay_config present
  - DB write: only bot response saved, not the [FOLLOW-UP REQUEST] message
"""

import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.test import AsyncClient

from chatbot.models import Bot, Conversation, Model, Utterance

URL = "/api/followup/"


def _async_full_round(text="Followup reply."):
    async def _inner(*args, **kwargs):
        msg = MagicMock()
        msg.text = text
        yield msg

    return _inner


def _mock_kani(text="Followup reply."):
    k = MagicMock()
    k.full_round = _async_full_round(text)
    return k


LLM_PATCHES = (
    "chatbot.services.followup.get_or_create_engine_from_model",
    "chatbot.services.followup.Kani",
)


class TestFollowupView:
    """HTTP-layer tests for POST /api/followup/.

    setUp creates a bot with follow_up_on_idle=True and a backdated user
    utterance so the user appears idle. All LLM calls are mocked.
    """

    def setUp(self, bot_kwargs=None):
        Model.get_or_create_default_models()
        self.model = Model.objects.get(provider__name="OpenAI", model_id="gpt-4o-mini")
        kwargs = {
            "name": f"bot_{uuid.uuid4().hex[:8]}",
            "prompt": "You are a test assistant.",
            "ai_model": self.model,
            "follow_up_on_idle": True,
            "idle_time_minutes": 1,
            "follow_up_instruction_prompt": "Check in with the user.",
            "recurring_followup": True,
        }
        if bot_kwargs:
            kwargs.update(bot_kwargs)
        self.bot = Bot.objects.create(**kwargs)
        self.conv = Conversation.objects.create(
            conversation_id=f"conv_{uuid.uuid4().hex[:8]}",
            bot_name=self.bot.name,
            participant_id="p_test",
        )
        # Backdate the user utterance so the user appears idle (> idle_time_minutes ago)
        utt = Utterance.objects.create(
            conversation=self.conv,
            speaker_id="user",
            text="Hello",
            participant_id="p_test",
        )
        utt.created_time = datetime.now() - timedelta(minutes=2)
        utt.save()

    def tearDown(self):
        cache.clear()
        Utterance.objects.filter(conversation=self.conv).delete()
        Conversation.objects.filter(pk=self.conv.pk).delete()
        Bot.objects.filter(pk=self.bot.pk).delete()

    async def _post(self, client, **extra):
        payload = {
            "bot_name": self.bot.name,
            "conversation_id": self.conv.conversation_id,
            **extra,
        }
        return await client.post(
            URL, data=json.dumps(payload), content_type="application/json"
        )

    # ── Input validation ──────────────────────────────────────────────────────

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_missing_bot_name_returns_400(self):
        await sync_to_async(self.setUp)()
        try:
            client = AsyncClient()
            r = await client.post(
                URL,
                data=json.dumps({"conversation_id": self.conv.conversation_id}),
                content_type="application/json",
            )
            assert r.status_code == 400
            assert "error" in r.json()
        finally:
            await sync_to_async(self.tearDown)()

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_missing_conversation_id_returns_400(self):
        await sync_to_async(self.setUp)()
        try:
            client = AsyncClient()
            r = await client.post(
                URL,
                data=json.dumps({"bot_name": self.bot.name}),
                content_type="application/json",
            )
            assert r.status_code == 400
        finally:
            await sync_to_async(self.tearDown)()

    # ── reset_flag ────────────────────────────────────────────────────────────

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_reset_flag_clears_once_flag_and_returns_200(self):
        await sync_to_async(self.setUp)()
        try:
            key = f"followup_sent_once_{self.conv.conversation_id}"
            await sync_to_async(cache.set)(key, True, 3600)
            assert await sync_to_async(cache.get)(key) is True

            client = AsyncClient()
            r = await self._post(client, reset_flag=True)

            assert r.status_code == 200
            assert r.json() == {"status": "Followup flag reset"}
            assert await sync_to_async(cache.get)(key) is None
        finally:
            await sync_to_async(self.tearDown)()

    # ── Idle gating ───────────────────────────────────────────────────────────

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_follow_up_disabled_returns_400(self):
        await sync_to_async(self.setUp)(bot_kwargs={"follow_up_on_idle": False})
        try:
            client = AsyncClient()
            r = await self._post(client)
            assert r.status_code == 400
            assert "not enabled" in r.json()["error"]
        finally:
            await sync_to_async(self.tearDown)()

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_user_not_idle_returns_400(self):
        await sync_to_async(self.setUp)()
        try:
            # Override the utterance timestamp to NOW so user is not idle
            await sync_to_async(
                Utterance.objects.filter(
                    conversation=self.conv, speaker_id="user"
                ).update
            )(created_time=datetime.now())

            client = AsyncClient()
            r = await self._post(client)
            assert r.status_code == 400
            assert "not idle" in r.json()["error"]
        finally:
            await sync_to_async(self.tearDown)()

    # ── Rate limiting ─────────────────────────────────────────────────────────

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_rate_limiting_blocks_second_call(self):
        """Second POST within the 30 s cooldown is rejected."""
        await sync_to_async(self.setUp)()
        try:
            client = AsyncClient()
            with (
                patch(LLM_PATCHES[0], return_value=MagicMock()),
                patch(LLM_PATCHES[1], return_value=_mock_kani()),
            ):
                r1 = await self._post(client)
            assert r1.status_code == 200

            # Second call — cooldown key is now set in cache
            r2 = await self._post(client)
            assert r2.status_code == 400
            assert "recently sent" in r2.json()["error"]
        finally:
            await sync_to_async(self.tearDown)()

    # ── Dedup (recurring_followup=False) ──────────────────────────────────────

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_dedup_once_flag_blocks_repeat(self):
        """When recurring_followup=False, setting the once-flag blocks further followups."""
        await sync_to_async(self.setUp)(bot_kwargs={"recurring_followup": False})
        try:
            key = f"followup_sent_once_{self.conv.conversation_id}"
            await sync_to_async(cache.set)(key, True, 3600)

            client = AsyncClient()
            r = await self._post(client)
            assert r.status_code == 400
            assert "already sent" in r.json()["error"]
        finally:
            await sync_to_async(self.tearDown)()

    # ── Happy path ────────────────────────────────────────────────────────────

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_followup_returns_200_with_expected_fields(self):
        await sync_to_async(self.setUp)()
        try:
            client = AsyncClient()
            with (
                patch(LLM_PATCHES[0], return_value=MagicMock()),
                patch(LLM_PATCHES[1], return_value=_mock_kani("Hey there!")),
            ):
                r = await self._post(client)

            assert r.status_code == 200
            data = r.json()
            for field in (
                "response",
                "response_chunks",
                "is_followup",
                "humanlike_delay",
                "chunk_messages",
                "delay_config",
            ):
                assert field in data, f"missing field: {field}"
            assert data["is_followup"] is True
        finally:
            await sync_to_async(self.tearDown)()

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_response_text_matches_llm_output(self):
        await sync_to_async(self.setUp)()
        try:
            client = AsyncClient()
            with (
                patch(LLM_PATCHES[0], return_value=MagicMock()),
                patch(LLM_PATCHES[1], return_value=_mock_kani("Just checking in!")),
            ):
                r = await self._post(client)
            assert r.json()["response"] == "Just checking in!"
        finally:
            await sync_to_async(self.tearDown)()

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_delay_config_has_required_keys(self):
        await sync_to_async(self.setUp)()
        try:
            client = AsyncClient()
            with (
                patch(LLM_PATCHES[0], return_value=MagicMock()),
                patch(LLM_PATCHES[1], return_value=_mock_kani()),
            ):
                r = await self._post(client)
            dc = r.json()["delay_config"]
            assert "reading_time" in dc
            assert "min_reading_delay" in dc
            assert isinstance(dc["response_segments"], list)
        finally:
            await sync_to_async(self.tearDown)()

    # ── DB write correctness ──────────────────────────────────────────────────

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_only_bot_response_saved_not_followup_request(self):
        """Only the bot's reply is written to DB; [FOLLOW-UP REQUEST] is not."""
        await sync_to_async(self.setUp)()
        try:
            client = AsyncClient()
            with (
                patch(LLM_PATCHES[0], return_value=MagicMock()),
                patch(LLM_PATCHES[1], return_value=_mock_kani("Bot says hi.")),
            ):
                await self._post(client)

            utterances = await sync_to_async(list)(
                Utterance.objects.filter(conversation=self.conv).order_by(
                    "created_time"
                )
            )
            # setUp adds 1 user utterance; followup adds 1 bot utterance
            assert len(utterances) == 2
            assert utterances[0].speaker_id == "user"
            assert utterances[1].speaker_id == "assistant"
            assert utterances[1].text == "Bot says hi."
            assert not any(u.text.startswith("[FOLLOW-UP REQUEST]") for u in utterances)
        finally:
            await sync_to_async(self.tearDown)()

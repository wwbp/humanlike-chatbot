"""
Live integration test for the full followup flow.

Requires a valid ANTHROPIC_API_KEY (the test bot uses claude-3-haiku-20240307).
Skipped automatically in CI via the -m "not integration" default filter in pytest.ini.
Run explicitly with: pytest -m integration
"""

import json
import uuid
from datetime import datetime, timedelta

import pytest
from django.test import Client


@pytest.mark.integration
@pytest.mark.django_db
class TestFollowupIntegration:
    def setUp(self):
        from chatbot.models import Bot, Model, ModelProvider

        ModelProvider.objects.get_or_create(name="Anthropic")
        provider = ModelProvider.objects.get(name="Anthropic")
        model, _ = Model.objects.get_or_create(
            provider=provider,
            model_id="claude-3-haiku-20240307",
            defaults={"name": "claude-3-haiku-20240307"},
        )

        self.bot_name = f"integration_bot_{uuid.uuid4().hex[:8]}"
        self.conversation_id = f"integration_conv_{uuid.uuid4().hex[:8]}"
        self.participant_id = "integration_participant"

        self.bot = Bot.objects.create(
            name=self.bot_name,
            prompt="You are a helpful assistant.",
            ai_model=model,
            follow_up_on_idle=True,
            idle_time_minutes=1,
            follow_up_instruction_prompt="Send a friendly follow-up to keep the conversation going.",
        )
        self.client = Client()

    def tearDown(self):
        from chatbot.models import Bot, Conversation

        Conversation.objects.filter(conversation_id=self.conversation_id).delete()
        Bot.objects.filter(name=self.bot_name).delete()

    def test_initialize_chat_and_followup(self):
        import os

        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set — skipping live integration test")

        # 1. Initialize conversation
        r = self.client.post(
            "/api/initialize_conversation/",
            data=json.dumps(
                {
                    "bot_name": self.bot_name,
                    "conversation_id": self.conversation_id,
                    "participant_id": self.participant_id,
                    "study_name": "integration_test",
                    "user_group": "test",
                    "survey_id": "test_survey",
                }
            ),
            content_type="application/json",
        )
        assert r.status_code == 200, f"initialize_conversation failed: {r.content}"

        # 2. Send a user message (makes a real LLM call)
        r = self.client.post(
            "/api/chatbot/",
            data=json.dumps(
                {
                    "message": "Hello, how are you?",
                    "bot_name": self.bot_name,
                    "conversation_id": self.conversation_id,
                    "participant_id": self.participant_id,
                }
            ),
            content_type="application/json",
        )
        assert r.status_code == 200, f"chatbot POST failed: {r.content}"

        # 3. Backdate the user utterance so the user appears idle
        from chatbot.models import Utterance

        last_msg = (
            Utterance.objects.filter(
                conversation__conversation_id=self.conversation_id,
                speaker_id="user",
            )
            .order_by("-created_time")
            .first()
        )
        assert last_msg is not None, "No user utterance found after chat round"
        last_msg.created_time = datetime.now() - timedelta(minutes=2)
        last_msg.save()

        # 4. Followup endpoint should now fire
        r = self.client.post(
            "/api/followup/",
            data=json.dumps(
                {
                    "bot_name": self.bot_name,
                    "conversation_id": self.conversation_id,
                    "participant_id": self.participant_id,
                }
            ),
            content_type="application/json",
        )
        assert r.status_code == 200, f"followup POST failed: {r.content}"
        data = r.json()
        assert "response" in data
        assert data["is_followup"] is True

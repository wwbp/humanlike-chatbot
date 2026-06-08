"""
Test that initializing a conversation works when a bot has personas assigned.
"""

import json
import uuid

import pytest
from django.test import Client

from chatbot.models import Bot, Conversation, Model, Persona


@pytest.mark.django_db
def test_initialize_conversation_with_persona():
    Model.get_or_create_default_models()
    model = Model.objects.first()

    bot_name = f"test_bot_persona_{uuid.uuid4().hex}"
    conversation_id = f"test_conv_persona_{uuid.uuid4().hex}"

    persona = Persona.objects.create(
        name=f"Test Persona {uuid.uuid4().hex}",
        instructions="You are a helpful persona for testing.",
    )
    bot = Bot.objects.create(
        name=bot_name,
        prompt="You are a helpful assistant.",
        ai_model=model,
    )
    bot.personas.add(persona)

    client = Client()
    response = client.post(
        "/api/initialize_conversation/",
        data=json.dumps(
            {
                "bot_name": bot_name,
                "conversation_id": conversation_id,
                "participant_id": "test_participant",
                "study_name": "persona_test",
                "user_group": "test_group",
                "survey_id": "test_survey",
            },
        ),
        content_type="application/json",
    )

    assert response.status_code == 200, (
        f"Failed to initialize conversation with personas: {response.content}"
    )

    conversation = Conversation.objects.get(conversation_id=conversation_id)
    assert conversation.bot_config, "Expected bot_config to be populated."

    bot_config = json.loads(conversation.bot_config)
    assert isinstance(bot_config.get("personas"), list)
    assert any(
        persona_entry.get("id") == persona.id
        for persona_entry in bot_config["personas"]
    )

"""
Tests for InitializeConversationAPIView  (POST /api/initialize_conversation/)

Coverage:
  - Input validation (missing fields, bad JSON)
  - Bot not found
  - New conversation: DB record created, initial utterance saved
  - Existing conversation: messages returned, is_existing flag set
  - bot_config included in response for both new and existing paths
  - Persona randomly assigned on new conversation
"""
import json
import uuid

import pytest
from django.test import Client

from chatbot.models import Bot, Conversation, Persona, Utterance

URL = "/api/initialize_conversation/"


def post_init(client, bot_name, conversation_id, **extra):
    payload = {"bot_name": bot_name, "conversation_id": conversation_id, "participant_id": "p_test", **extra}
    return client.post(URL, data=json.dumps(payload), content_type="application/json")


@pytest.fixture
def client():
    return Client()


# ── Input validation ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_missing_bot_name_returns_400(client):
    r = client.post(
        URL,
        data=json.dumps({"conversation_id": "c1", "participant_id": "p1"}),
        content_type="application/json",
    )
    assert r.status_code == 400
    assert "error" in r.json()


@pytest.mark.django_db
def test_missing_conversation_id_returns_400(client):
    r = client.post(
        URL,
        data=json.dumps({"bot_name": "somebot", "participant_id": "p1"}),
        content_type="application/json",
    )
    assert r.status_code == 400
    assert "error" in r.json()


@pytest.mark.django_db
def test_bad_json_returns_400(client):
    r = client.post(URL, data="not valid json", content_type="application/json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_bot_not_found_returns_404(client):
    r = post_init(client, "no_such_bot", "c1")
    assert r.status_code == 404


# ── New conversation ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_new_conversation_returns_200(client, make_bot):
    bot = make_bot()
    r = post_init(client, bot.name, f"cid_{uuid.uuid4().hex}")
    assert r.status_code == 200
    data = r.json()
    assert data["is_existing"] is False


@pytest.mark.django_db
def test_new_conversation_creates_db_record(client, make_bot):
    bot = make_bot()
    cid = f"cid_{uuid.uuid4().hex}"
    post_init(client, bot.name, cid)
    assert Conversation.objects.filter(conversation_id=cid).exists()


@pytest.mark.django_db
def test_new_conversation_no_initial_utterance_returns_empty_messages(client, make_bot):
    bot = make_bot(initial_utterance="")
    cid = f"cid_{uuid.uuid4().hex}"
    r = post_init(client, bot.name, cid)
    assert r.status_code == 200
    assert r.json()["existing_messages"] == []


@pytest.mark.django_db
def test_new_conversation_saves_initial_utterance_to_db(client, make_bot):
    bot = make_bot(initial_utterance="Hello! I am ready.")
    cid = f"cid_{uuid.uuid4().hex}"
    post_init(client, bot.name, cid)
    conv = Conversation.objects.get(conversation_id=cid)
    assert Utterance.objects.filter(
        conversation=conv, speaker_id="assistant", text="Hello! I am ready."
    ).exists()


@pytest.mark.django_db
def test_new_conversation_initial_utterance_in_response_messages(client, make_bot):
    bot = make_bot(initial_utterance="Greetings.")
    cid = f"cid_{uuid.uuid4().hex}"
    r = post_init(client, bot.name, cid)
    msgs = r.json()["existing_messages"]
    assert len(msgs) == 1
    assert msgs[0]["sender"] == "AI Chatbot"
    assert msgs[0]["content"] == "Greetings."


@pytest.mark.django_db
def test_new_conversation_assigns_persona_when_available(client, make_bot, openai_model):
    bot = make_bot()
    persona = Persona.objects.create(
        name=f"p_{uuid.uuid4().hex[:6]}", instructions="Be friendly."
    )
    bot.personas.add(persona)
    cid = f"cid_{uuid.uuid4().hex}"
    post_init(client, bot.name, cid)
    conv = Conversation.objects.get(conversation_id=cid)
    assert conv.selected_persona == persona


@pytest.mark.django_db
def test_new_conversation_no_persona_assigned_when_pool_empty(client, make_bot):
    bot = make_bot()
    cid = f"cid_{uuid.uuid4().hex}"
    post_init(client, bot.name, cid)
    conv = Conversation.objects.get(conversation_id=cid)
    assert conv.selected_persona is None


# ── Existing conversation ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_existing_conversation_returns_is_existing_true(client, make_bot):
    bot = make_bot()
    cid = f"cid_{uuid.uuid4().hex}"
    post_init(client, bot.name, cid)  # create
    r = post_init(client, bot.name, cid)  # resume
    assert r.status_code == 200
    assert r.json()["is_existing"] is True


@pytest.mark.django_db
def test_existing_conversation_returns_stored_messages(client, make_bot):
    bot = make_bot()
    cid = f"cid_{uuid.uuid4().hex}"
    post_init(client, bot.name, cid)
    conv = Conversation.objects.get(conversation_id=cid)
    Utterance.objects.create(conversation=conv, speaker_id="user", text="Hey there")
    r = post_init(client, bot.name, cid)
    msgs = r.json()["existing_messages"]
    assert any(m["content"] == "Hey there" for m in msgs)


@pytest.mark.django_db
def test_existing_conversation_does_not_create_duplicate(client, make_bot):
    bot = make_bot()
    cid = f"cid_{uuid.uuid4().hex}"
    post_init(client, bot.name, cid)
    post_init(client, bot.name, cid)
    assert Conversation.objects.filter(conversation_id=cid).count() == 1


# ── bot_config in response ────────────────────────────────────────────────────
# These tests define the NEW expected shape. They will be RED until the
# implementation adds bot_config to the response.


@pytest.mark.django_db
def test_new_conversation_response_includes_bot_config(client, make_bot):
    bot = make_bot(
        follow_up_on_idle=True,
        idle_time_minutes=5,
        recurring_followup=False,
        chunk_messages=True,
        humanlike_delay=True,
        avatar_type="none",
    )
    cid = f"cid_{uuid.uuid4().hex}"
    r = post_init(client, bot.name, cid)
    assert r.status_code == 200
    data = r.json()
    assert "bot_config" in data, "bot_config missing from initialize_conversation response"
    cfg = data["bot_config"]
    assert cfg["follow_up_on_idle"] is True
    assert cfg["idle_time_minutes"] == 5
    assert cfg["recurring_followup"] is False
    assert cfg["chunk_messages"] is True
    assert cfg["humanlike_delay"] is True
    assert cfg["avatar_type"] == "none"


@pytest.mark.django_db
def test_existing_conversation_response_includes_bot_config(client, make_bot):
    bot = make_bot(follow_up_on_idle=False, idle_time_minutes=2)
    cid = f"cid_{uuid.uuid4().hex}"
    post_init(client, bot.name, cid)
    r = post_init(client, bot.name, cid)  # resume
    assert r.status_code == 200
    data = r.json()
    assert "bot_config" in data, "bot_config missing from resume response"
    cfg = data["bot_config"]
    assert cfg["follow_up_on_idle"] is False
    assert cfg["idle_time_minutes"] == 2


@pytest.mark.django_db
def test_bot_config_contains_delay_parameters(client, make_bot):
    bot = make_bot(
        reading_words_per_minute=300.0,
        writing_words_per_minute=180.0,
        min_reading_delay=0.5,
    )
    cid = f"cid_{uuid.uuid4().hex}"
    r = post_init(client, bot.name, cid)
    cfg = r.json()["bot_config"]
    assert cfg["reading_words_per_minute"] == 300.0
    assert cfg["writing_words_per_minute"] == 180.0
    assert cfg["min_reading_delay"] == 0.5


@pytest.mark.django_db
def test_bot_config_reflects_live_bot_values_not_snapshot(client, make_bot):
    """bot_config in response comes from the live Bot row, not the stored snapshot."""
    bot = make_bot(follow_up_on_idle=False)
    cid = f"cid_{uuid.uuid4().hex}"
    post_init(client, bot.name, cid)

    # Update bot after conversation was created
    bot.follow_up_on_idle = True
    bot.save()

    r = post_init(client, bot.name, cid)  # resume
    cfg = r.json()["bot_config"]
    assert cfg["follow_up_on_idle"] is True  # must reflect current bot, not old snapshot

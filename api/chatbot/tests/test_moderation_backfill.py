"""
Tests for the 0036 data migration that labels historical blocked exchanges.

The migration is the only way to identify blocks that happened before
moderation_category existed. It has no category to recover, so it stamps the
sentinel "unknown" on the canned warning and on the user message that provoked
it, pairing them by position within the conversation.

Coverage:
  - a blocked pair gets both rows stamped
  - two blocks in one conversation pair with the right user rows, not each other's
  - ordinary exchanges are left alone
  - a warning with no preceding user message doesn't crash or over-claim
  - reverse clears only the sentinel, never a real category
"""

import importlib
from datetime import timedelta

import pytest
from django.apps import apps as global_apps
from django.utils import timezone

from chatbot.models import Bot, Conversation, Model, Utterance

_migration = importlib.import_module(
    "chatbot.migrations.0036_backfill_moderation_category"
)
backfill = _migration.backfill_moderation_category
reverse = _migration.reverse_backfill_moderation_category
WARNING_TEXT = _migration.WARNING_TEXT
SENTINEL = _migration.SENTINEL


@pytest.fixture
def conv(db):
    Model.get_or_create_default_models()
    model = Model.objects.get(provider__name="OpenAI", model_id="gpt-4o-mini")
    bot = Bot.objects.create(name="backfill_bot", prompt="p", ai_model=model)
    conversation = Conversation.objects.create(
        conversation_id="conv_backfill",
        bot_name=bot.name,
        participant_id="p001",
    )
    yield conversation
    conversation.delete()
    bot.delete()


def _utterance(conversation, speaker_id, text, offset_seconds):
    """created_time is auto_now_add, so stamp it with an UPDATE afterwards."""
    u = Utterance.objects.create(
        conversation=conversation, speaker_id=speaker_id, text=text
    )
    Utterance.objects.filter(pk=u.pk).update(
        created_time=timezone.now() + timedelta(seconds=offset_seconds)
    )
    u.refresh_from_db()
    return u


def test_blocked_pair_is_stamped_on_both_rows(conv):
    user = _utterance(conv, "user", "something nasty", 0)
    warning = _utterance(conv, "assistant", WARNING_TEXT, 1)

    backfill(global_apps, None)

    user.refresh_from_db()
    warning.refresh_from_db()
    assert user.moderation_category == SENTINEL
    assert warning.moderation_category == SENTINEL


def test_two_blocks_pair_with_their_own_user_rows(conv):
    """The second warning must not re-claim the first block's user message."""
    user1 = _utterance(conv, "user", "first bad message", 0)
    warning1 = _utterance(conv, "assistant", WARNING_TEXT, 1)
    normal_user = _utterance(conv, "user", "a fine message", 2)
    normal_bot = _utterance(conv, "assistant", "A fine reply.", 3)
    user2 = _utterance(conv, "user", "second bad message", 4)
    warning2 = _utterance(conv, "assistant", WARNING_TEXT, 5)

    backfill(global_apps, None)

    for row in (user1, warning1, user2, warning2):
        row.refresh_from_db()
        assert row.moderation_category == SENTINEL, f"{row.text!r} not stamped"

    for row in (normal_user, normal_bot):
        row.refresh_from_db()
        assert row.moderation_category is None, f"{row.text!r} wrongly stamped"


def test_ordinary_exchange_is_untouched(conv):
    user = _utterance(conv, "user", "hello", 0)
    bot_reply = _utterance(conv, "assistant", "Hi there!", 1)

    backfill(global_apps, None)

    user.refresh_from_db()
    bot_reply.refresh_from_db()
    assert user.moderation_category is None
    assert bot_reply.moderation_category is None


def test_warning_without_preceding_user_row(conv):
    """A truncated transcript must not crash or steal a later user message."""
    warning = _utterance(conv, "assistant", WARNING_TEXT, 0)
    later_user = _utterance(conv, "user", "sent afterwards", 1)

    backfill(global_apps, None)

    warning.refresh_from_db()
    later_user.refresh_from_db()
    assert warning.moderation_category == SENTINEL
    assert later_user.moderation_category is None


def test_rows_with_a_real_category_are_not_overwritten(conv):
    """Rows written after the feature shipped already carry a true category."""
    user = _utterance(conv, "user", "nasty", 0)
    warning = _utterance(conv, "assistant", WARNING_TEXT, 1)
    Utterance.objects.filter(pk__in=[user.pk, warning.pk]).update(
        moderation_category="harassment"
    )

    backfill(global_apps, None)

    user.refresh_from_db()
    warning.refresh_from_db()
    assert user.moderation_category == "harassment"
    assert warning.moderation_category == "harassment"


def test_reverse_clears_only_the_sentinel(conv):
    backfilled = _utterance(conv, "assistant", WARNING_TEXT, 0)
    real = _utterance(conv, "user", "nasty", 1)
    Utterance.objects.filter(pk=backfilled.pk).update(moderation_category=SENTINEL)
    Utterance.objects.filter(pk=real.pk).update(moderation_category="hate")

    reverse(global_apps, None)

    backfilled.refresh_from_db()
    real.refresh_from_db()
    assert backfilled.moderation_category is None
    assert real.moderation_category == "hate"

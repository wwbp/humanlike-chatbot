from django.db import migrations

# The literal the blocked path has always replied with (see
# chatbot/services/runchat.py). Matching it in full is the only handle we have on
# blocks that predate the moderation_category column.
WARNING_TEXT = "Your message could not be processed. Please keep conversations respectful and constructive."

# Historical rows have no recoverable category — the API response was never
# stored — so they are labelled as blocked without claiming to know why.
SENTINEL = "unknown"


def backfill_moderation_category(apps, schema_editor):
    """Label pre-existing blocked exchanges.

    Each canned warning is paired with the nearest preceding user message in the
    same conversation. Ordering is ("-created_time", "-id") rather than
    created_time alone: the two rows of a block are written back-to-back, so
    their auto_now_add timestamps can tie at the DB's resolution. Rows already
    carrying a real category (written after the feature shipped) are skipped.
    """
    Utterance = apps.get_model("chatbot", "Utterance")

    warnings = (
        Utterance.objects.filter(
            speaker_id="assistant",
            text=WARNING_TEXT,
            moderation_category__isnull=True,
        )
        .order_by("conversation_id", "created_time", "id")
        .iterator()
    )

    claimed_user_rows = set()
    to_update = []

    for warning in warnings:
        warning.moderation_category = SENTINEL
        to_update.append(warning)

        # A warning with no preceding user row (truncated transcript) simply
        # goes unpaired — it must not reach forward and claim a later message.
        provoking_message = (
            Utterance.objects.filter(
                conversation_id=warning.conversation_id,
                speaker_id="user",
                created_time__lte=warning.created_time,
                moderation_category__isnull=True,
            )
            .exclude(id__in=claimed_user_rows)
            .order_by("-created_time", "-id")
            .first()
        )
        if provoking_message is not None:
            claimed_user_rows.add(provoking_message.id)
            provoking_message.moderation_category = SENTINEL
            to_update.append(provoking_message)

    if to_update:
        Utterance.objects.bulk_update(
            to_update, ["moderation_category"], batch_size=500
        )


def reverse_backfill_moderation_category(apps, schema_editor):
    """Clear only the sentinel — never a category recorded by the live code."""
    Utterance = apps.get_model("chatbot", "Utterance")
    Utterance.objects.filter(moderation_category=SENTINEL).update(
        moderation_category=None
    )


class Migration(migrations.Migration):

    dependencies = [
        ("chatbot", "0035_utterance_moderation_scores"),
    ]

    operations = [
        migrations.RunPython(
            backfill_moderation_category,
            reverse_backfill_moderation_category,
        ),
    ]

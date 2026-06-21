import math
import os
import random
import time

from django.conf import settings
from openai import OpenAI
from openai._compat import model_dump

# When MOCK_LLM=true, skip all external API calls and simulate latency locally.
_MOCK_LLM = os.getenv("MOCK_LLM", "false").lower() == "true"
_MOCK_MOD_P50_MS = int(os.getenv("MOCK_MODERATION_P50_MS", "220"))


def is_moderation_enabled():
    """Check if global moderation is enabled.

    Runs on the thread_sensitive=False moderation thread, whose pooled DB
    connection nothing else recycles — so route the query through db_retry to
    survive a stale connection (was the source of recurring first-query 500s).
    """
    from ..models import ModerationSettings
    from .db import db_retry

    try:
        return db_retry(ModerationSettings.objects.first).enabled
    except AttributeError:
        return True  # Default to enabled if no settings exist


def moderate_message(message: str, bot=None) -> str:
    """
    Send the user's message through OpenAI's moderation endpoint and
    return a non-empty string if the message should be blocked.

    Args:
        message: The message to moderate
        bot: Bot instance with optional custom moderation thresholds

    Returns:
        A string with the category if blocked, or an empty string if acceptable.
    """
    if _MOCK_LLM:
        # Simulate realistic moderation latency (lognormal around p50).
        time.sleep(random.lognormvariate(math.log(_MOCK_MOD_P50_MS), 0.4) / 1000)
        return ""

    # Skip moderation when no API key is configured (e.g. CI or local dev without key)
    if not getattr(settings, "OPENAI_API_KEY", None):
        return ""

    # Check global moderation setting first
    if not is_moderation_enabled():
        return ""  # Bypass all moderation

    # Call OpenAI moderation API
    moderation_response = OpenAI(api_key=settings.OPENAI_API_KEY).moderations.create(
        input=message,
        model="omni-moderation-latest",
    )

    # Extract category scores
    category_scores = moderation_response.results[0].category_scores or {}
    scores = model_dump(category_scores)

    # Determine if any score exceeds the configured threshold
    for category, score in scores.items():
        if score is None:
            continue
        if bot:
            threshold = bot.get_moderation_threshold(category)
        else:
            # Fallback to global defaults if no bot provided
            defaults = {
                "harassment": 0.5,
                "harassment/threatening": 0.1,
                "hate": 0.5,
                "hate/threatening": 0.1,
                "self-harm": 0.2,
                "self-harm/instructions": 0.5,
                "self-harm/intent": 0.7,
                "sexual": 0.5,
                "sexual/minors": 0.2,
                "violence": 0.7,
                "violence/graphic": 0.8,
            }
            threshold = defaults.get(category, 1.0)

        if score > threshold:
            return category

    return ""

import logging
import math
import os
import random
import time
from dataclasses import dataclass

from django.conf import settings
from openai import OpenAI
from openai._compat import model_dump

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModerationResult:
    """Outcome of one moderation check.

    `category` is the first category whose score exceeded its threshold, or None
    if the message is allowed — so `if result.category:` is the "was it blocked"
    test. `scores` is the full category→score map the API returned, kept in full
    (not just the tripping category) because the passing scores are what make
    thresholds re-tunable after the fact. It is None when no API call was made:
    mock mode, no API key, or moderation globally disabled.
    """

    category: str | None = None
    scores: dict | None = None


# The SDK hands back each multi-word category under two spellings. OpenAI's wire
# format uses "harassment/threatening"; the SDK's CategoryScores model declares
# `harassment_threatening` with the slash as a pydantic alias, and because
# responses are built with construct() rather than model_validate() the raw key
# survives as an extra field — so model_dump() emits both. Collapsing them onto
# the canonical spelling keeps the persisted scores unambiguous and, more
# importantly, keeps thresholds working if a future SDK version stops preserving
# the raw keys (an underscore-only payload would otherwise match no threshold).
_ALIAS_TO_CANONICAL = {
    "harassment_threatening": "harassment/threatening",
    "hate_threatening": "hate/threatening",
    "illicit_violent": "illicit/violent",
    "self_harm": "self-harm",
    "self_harm_instructions": "self-harm/instructions",
    "self_harm_intent": "self-harm/intent",
    "sexual_minors": "sexual/minors",
    "violence_graphic": "violence/graphic",
}


def _canonical_scores(raw_scores):
    """Collapse the SDK's duplicate spellings onto OpenAI's canonical names."""
    canonical = {}
    for category, score in raw_scores.items():
        name = _ALIAS_TO_CANONICAL.get(category, category)
        # Duplicates carry identical values; prefer whichever is not None.
        if canonical.get(name) is None:
            canonical[name] = score
    return canonical


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


def moderate_message(message: str, bot=None) -> ModerationResult:
    """
    Send the user's message through OpenAI's moderation endpoint.

    Args:
        message: The message to moderate
        bot: Bot instance with optional custom moderation thresholds

    Returns:
        A ModerationResult. `category` is set only when the message should be
        blocked; `scores` carries the full score map whenever the API was called.
    """
    if _MOCK_LLM:
        # Simulate realistic moderation latency (lognormal around p50).
        time.sleep(random.lognormvariate(math.log(_MOCK_MOD_P50_MS), 0.4) / 1000)
        return ModerationResult()

    # Skip moderation when no API key is configured (e.g. CI or local dev without key)
    if not getattr(settings, "OPENAI_API_KEY", None):
        return ModerationResult()

    # Check global moderation setting first
    if not is_moderation_enabled():
        return ModerationResult()  # Bypass all moderation

    # Call OpenAI moderation API
    moderation_response = OpenAI(api_key=settings.OPENAI_API_KEY).moderations.create(
        input=message,
        model="omni-moderation-latest",
    )

    from ..models import MODERATION_CATEGORIES, Bot

    # Extract category scores
    category_scores = moderation_response.results[0].category_scores or {}
    scores = _canonical_scores(model_dump(category_scores))

    # A category we have no threshold for can never block. That silence is how
    # `illicit` stayed unenforced, so say so rather than dropping it.
    unrecognized = sorted(set(scores) - set(MODERATION_CATEGORIES))
    if unrecognized:
        logger.warning(
            "Moderation returned categories with no configured threshold — "
            "they cannot block until a Bot field is added for them: %s",
            ", ".join(unrecognized),
        )

    # Determine if any score exceeds the configured threshold
    for category, score in scores.items():
        if score is None:
            continue
        if bot:
            threshold = bot.get_moderation_threshold(category)
        else:
            # No bot: fall back to the Bot field defaults rather than a second
            # hardcoded copy of them, which would drift out of sync.
            threshold = Bot.default_moderation_threshold(category)

        if score > threshold:
            # Operational visibility: the message text is deliberately omitted,
            # the persisted Utterance row carries that.
            logger.warning(
                "Moderation blocked a message [bot=%s category=%s score=%.4f threshold=%.2f]",
                getattr(bot, "name", None),
                category,
                score,
                threshold,
            )
            return ModerationResult(category=category, scores=scores)

    return ModerationResult(scores=scores)

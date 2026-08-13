"""
Tests for moderation category handling.

Two defects motivated these, both silent — nothing errored, blocks simply did
not happen:

  1. `illicit` and `illicit/violent` were never enforced. omni-moderation
     returns them, but the threshold lookup was a hardcoded map that predated
     those categories, so both fell through to the 1.0 default and no score
     could ever exceed them.

  2. The score map arrives with each multi-word category under two spellings.
     OpenAI's wire format uses "harassment/threatening"; the SDK model declares
     `harassment_threatening` with the slash as a pydantic alias, and because
     responses are built with construct() the raw key survives as an extra
     field. model_dump() therefore emits both. Enforcement happened to work
     because the canonical key was present — but only by luck, and it left
     duplicate keys in the persisted scores.
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from ..models import (
    Bot,
    Model,
    ModelProvider,
    ModerationSettings,
    moderation_field_name,
)
from ..services.moderation import moderate_message

# Every category omni-moderation-latest returns, in OpenAI's own spelling.
CANONICAL_CATEGORIES = [
    "harassment",
    "harassment/threatening",
    "hate",
    "hate/threatening",
    "illicit",
    "illicit/violent",
    "self-harm",
    "self-harm/instructions",
    "self-harm/intent",
    "sexual",
    "sexual/minors",
    "violence",
    "violence/graphic",
]

# What the SDK actually hands back: canonical keys plus underscore duplicates.
SDK_DUPLICATE_KEYS = {
    "harassment_threatening": "harassment/threatening",
    "hate_threatening": "hate/threatening",
    "illicit_violent": "illicit/violent",
    "self_harm": "self-harm",
    "self_harm_instructions": "self-harm/instructions",
    "self_harm_intent": "self-harm/intent",
    "sexual_minors": "sexual/minors",
    "violence_graphic": "violence/graphic",
}


def _sdk_shaped_scores(**overrides):
    """Build a score map shaped like a real model_dump(): canonical keys plus
    the underscore duplicates, every category present."""
    scores = dict.fromkeys(CANONICAL_CATEGORIES, 0.0)
    scores.update(overrides)
    for underscore, canonical in SDK_DUPLICATE_KEYS.items():
        scores[underscore] = scores[canonical]
    return scores


class ModerationCategoryTestCase(TestCase):
    def setUp(self):
        Model.get_or_create_default_models()
        provider = ModelProvider.objects.get(name="OpenAI")
        self.bot = Bot.objects.create(
            name="category_test_bot",
            prompt="Test bot",
            ai_model=Model.objects.filter(provider=provider).first(),
        )
        ModerationSettings.objects.create(enabled=True)

    def tearDown(self):
        ModerationSettings.objects.all().delete()

    def _moderate(self, scores):
        """Run moderate_message against a fixed score map."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_result = MagicMock()
        mock_result.category_scores = None
        mock_response.results = [mock_result]
        mock_client.moderations.create.return_value = mock_response

        with (
            patch("chatbot.services.moderation.OpenAI", return_value=mock_client),
            patch("chatbot.services.moderation.model_dump", return_value=scores),
        ):
            return moderate_message("a message", self.bot)


@override_settings(OPENAI_API_KEY="test-key")
@patch("chatbot.services.moderation._MOCK_LLM", False)
class TestThresholdCoverage(ModerationCategoryTestCase):
    """Every category the API returns must be enforceable."""

    def test_every_canonical_category_has_a_reachable_threshold(self):
        unreachable = [
            c
            for c in CANONICAL_CATEGORIES
            if self.bot.get_moderation_threshold(c) >= 1.0
        ]
        assert not unreachable, (
            f"these categories can never block: {unreachable} — "
            "the API scores them but no threshold is configured"
        )

    def test_illicit_blocks_when_over_threshold(self):
        result = self._moderate(_sdk_shaped_scores(illicit=0.95))
        assert result.category == "illicit"

    def test_illicit_violent_blocks_when_over_threshold(self):
        result = self._moderate(_sdk_shaped_scores(**{"illicit/violent": 0.95}))
        assert result.category == "illicit/violent"

    def test_illicit_below_threshold_is_allowed(self):
        result = self._moderate(_sdk_shaped_scores(illicit=0.0))
        assert result.category is None


@override_settings(OPENAI_API_KEY="test-key")
@patch("chatbot.services.moderation._MOCK_LLM", False)
class TestScoreNormalization(ModerationCategoryTestCase):
    """The persisted score map is research data — duplicate spellings of the
    same category make it ambiguous to analyse."""

    def test_duplicate_spellings_are_collapsed(self):
        result = self._moderate(_sdk_shaped_scores(harassment=0.9))

        assert set(result.scores) == set(CANONICAL_CATEGORIES), (
            "scores should hold exactly the canonical categories, "
            f"got {sorted(set(result.scores) - set(CANONICAL_CATEGORIES))} extra"
        )
        assert len(result.scores) == 13

    def test_normalization_preserves_values(self):
        raw = _sdk_shaped_scores(harassment=0.9, violence=0.42)
        result = self._moderate(raw)
        assert result.scores["harassment"] == 0.9
        assert result.scores["violence"] == 0.42
        assert result.scores["harassment/threatening"] == raw["harassment/threatening"]

    def test_underscore_only_payload_still_enforces(self):
        """Guards the latent failure: enforcement currently relies on the SDK
        preserving raw alias keys. If a future SDK version drops them, every
        multi-word threshold must keep working."""
        underscore_only = {
            "harassment": 0.0,
            "harassment_threatening": 0.95,  # default threshold 0.10
            "hate": 0.0,
            "violence": 0.0,
        }
        result = self._moderate(underscore_only)
        assert result.category == "harassment/threatening", (
            "an underscore-spelled payload silently stopped blocking"
        )

    def test_unknown_category_is_logged_not_silently_ignored(self):
        """A category OpenAI adds later must surface, not vanish — that silence
        is how `illicit` went unenforced."""
        scores = _sdk_shaped_scores()
        scores["brand_new_category"] = 0.99

        with self.assertLogs("chatbot.services.moderation", level="WARNING") as logs:
            result = self._moderate(scores)

        assert result.category is None  # unknown categories still never block
        assert any("brand_new_category" in line for line in logs.output), (
            f"expected a warning naming the category, got {logs.output}"
        )


class TestBotAdminExposesEveryThreshold(TestCase):
    """A threshold nobody can edit in the admin is a threshold nobody will
    tune — the same practical invisibility that hid the missing categories."""

    def test_every_category_has_an_editable_field(self):
        from ..admin import BotAdmin

        editable = {
            field
            for _, options in BotAdmin.fieldsets
            for row in options["fields"]
            for field in ((row,) if isinstance(row, str) else row)
        }
        missing = [
            moderation_field_name(c)
            for c in CANONICAL_CATEGORIES
            if moderation_field_name(c) not in editable
        ]
        assert not missing, f"not editable in the Bot admin: {missing}"

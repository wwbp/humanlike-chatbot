"""
Tests for voicechat endpoints:
  GET  /api/session/               (get_realtime_session)
  POST /api/upload_voice_utterance/ (upload_voice_utterance)

Coverage:
  get_realtime_session:
    - 400 when conversation_id is missing
    - 404 when conversation does not exist
    - 503 when OPENAI_API_KEY is not set
    - 200 when OpenAI request succeeds (proxied response)
    - 500 when requests.post raises

  upload_voice_utterance:
    - 400 when conversation_id is missing
    - 400 when neither transcript nor audio is provided
    - 415 when audio file has unsupported MIME type
    - 404 when conversation does not exist
    - 200 saves transcript-only utterance; speaker_id = "participant"
    - 200 saves bot utterance when bot_name is provided; speaker_id = "assistant"
    - 200 saves utterance with is_voice flag
"""

import uuid
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from django.test import Client, TestCase

from chatbot.models import Bot, Conversation, Model, Utterance

SESSION_URL = "/api/session/"
UPLOAD_URL = "/api/upload_voice_utterance/"


class TestGetRealtimeSession(TestCase):
    def setUp(self):
        Model.get_or_create_default_models()
        model = Model.objects.get(provider__name="OpenAI", model_id="gpt-4o-mini")
        self.bot = Bot.objects.create(
            name=f"bot_{uuid.uuid4().hex[:8]}",
            prompt="Test.",
            ai_model=model,
        )
        self.conv = Conversation.objects.create(
            conversation_id=f"conv_{uuid.uuid4().hex[:8]}",
            bot_name=self.bot.name,
            participant_id="p_test",
        )

    def test_missing_conversation_id_returns_400(self):
        r = Client().get(SESSION_URL)
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", r.json())

    def test_nonexistent_conversation_returns_404(self):
        r = Client().get(SESSION_URL, {"conversation_id": "does_not_exist"})
        self.assertEqual(r.status_code, 404)

    @patch.dict("os.environ", {}, clear=False)
    def test_missing_api_key_returns_503(self):
        with patch("chatbot.services.voicechat.os.getenv", return_value=None):
            r = Client().get(SESSION_URL, {"conversation_id": self.conv.conversation_id})
        self.assertEqual(r.status_code, 503)

    def test_success_proxies_openai_response(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "sess_123", "token": "tok_abc"}
        mock_resp.status_code = 200
        with (
            patch("chatbot.services.voicechat.os.getenv", return_value="sk-test"),
            patch("chatbot.services.voicechat.requests.post", return_value=mock_resp),
        ):
            r = Client().get(SESSION_URL, {"conversation_id": self.conv.conversation_id})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], "sess_123")

    def test_openai_request_failure_returns_500(self):
        with (
            patch("chatbot.services.voicechat.os.getenv", return_value="sk-test"),
            patch("chatbot.services.voicechat.requests.post", side_effect=Exception("timeout")),
        ):
            r = Client().get(SESSION_URL, {"conversation_id": self.conv.conversation_id})
        self.assertEqual(r.status_code, 500)


class TestUploadVoiceUtterance(TestCase):
    def setUp(self):
        Model.get_or_create_default_models()
        model = Model.objects.get(provider__name="OpenAI", model_id="gpt-4o-mini")
        self.bot = Bot.objects.create(
            name=f"bot_{uuid.uuid4().hex[:8]}",
            prompt="Test.",
            ai_model=model,
        )
        self.conv = Conversation.objects.create(
            conversation_id=f"conv_{uuid.uuid4().hex[:8]}",
            bot_name=self.bot.name,
            participant_id="p_test",
        )

    def _post(self, data, files=None):
        if files:
            return Client().post(UPLOAD_URL, {**data, **files})
        return Client().post(UPLOAD_URL, data)

    def test_missing_conversation_id_returns_400(self):
        r = self._post({"transcript": "hello"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", r.json())

    def test_no_transcript_no_audio_returns_400(self):
        r = self._post({"conversation_id": self.conv.conversation_id})
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", r.json())

    def test_unsupported_audio_mime_returns_415(self):
        audio = BytesIO(b"fake audio data")
        audio.name = "clip.mp3"
        audio.content_type = "video/mp4"
        fake_file = MagicMock()
        fake_file.content_type = "video/mp4"
        with patch("django.test.client.encode_multipart"):
            r = Client().post(
                UPLOAD_URL,
                {
                    "conversation_id": self.conv.conversation_id,
                    "audio": BytesIO(b"data"),
                },
            )
        # BytesIO has no content_type — simulate by patching FILES
        from django.core.files.uploadedfile import InMemoryUploadedFile

        bad_audio = InMemoryUploadedFile(
            BytesIO(b"data"), "audio", "clip.mp4", "video/mp4", 4, None
        )
        r = Client().post(
            UPLOAD_URL,
            {"conversation_id": self.conv.conversation_id, "audio": bad_audio},
        )
        self.assertEqual(r.status_code, 415)

    def test_nonexistent_conversation_returns_404(self):
        r = self._post({"conversation_id": "no_such_conv", "transcript": "hi"})
        self.assertEqual(r.status_code, 404)

    def test_transcript_only_saves_participant_utterance(self):
        r = self._post(
            {
                "conversation_id": self.conv.conversation_id,
                "transcript": "Hello there",
                "participant_id": "p_test",
            }
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("id", body)
        utt = Utterance.objects.get(pk=body["id"])
        self.assertEqual(utt.text, "Hello there")
        self.assertEqual(utt.speaker_id, "participant")

    def test_bot_name_sets_assistant_speaker(self):
        r = self._post(
            {
                "conversation_id": self.conv.conversation_id,
                "transcript": "Bot reply",
                "bot_name": self.bot.name,
            }
        )
        self.assertEqual(r.status_code, 200)
        utt = Utterance.objects.get(pk=r.json()["id"])
        self.assertEqual(utt.speaker_id, "assistant")
        self.assertEqual(utt.bot_name, self.bot.name)

    def test_is_voice_flag_stored(self):
        r = self._post(
            {
                "conversation_id": self.conv.conversation_id,
                "transcript": "voice input",
                "is_voice": "true",
            }
        )
        self.assertEqual(r.status_code, 200)
        utt = Utterance.objects.get(pk=r.json()["id"])
        self.assertTrue(utt.is_voice)

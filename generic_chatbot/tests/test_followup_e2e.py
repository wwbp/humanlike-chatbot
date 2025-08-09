"""
End-to-end tests for the followup functionality.

These tests verify the complete flow of:
1. Initializing a conversation
2. Sending user messages
3. Waiting for idle time
4. Generating followup messages
5. Verifying bot configuration

Also includes unit tests for individual followup functions and components.
"""

import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

from asgiref.sync import sync_to_async
from django.test import TestCase
from django.utils import timezone

from chatbot.models import Conversation, Utterance
from chatbot.services.followup import (
    FollowupAPIView,
    generate_followup_message,
    get_last_user_message_time,
    is_user_idle,
)
from tests.factories import (
    BotFactory,
    ConversationFactory,
    PersonaFactory,
)


class TestFollowupFunctions(TestCase):
    """Test individual followup functions."""

    def setUp(self):
        """Set up test data."""
        self.bot = BotFactory(
            name="TestBot",
            follow_up_on_idle=True,
            idle_time_minutes=5,
            follow_up_instruction_prompt="Check in with the user.",
        )
        
        self.conversation = ConversationFactory(
            conversation_id="test-conv-123",
            bot_name="TestBot",
        )
        
        self.participant_id = "test-user-456"

    async def test_get_last_user_message_time_with_messages(self):
        """Test getting last user message time when messages exist."""
        # Create user messages with different timestamps
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Old message",
            participant_id=self.participant_id,
            created_time=timezone.now() - timedelta(hours=2),
        )
        
        recent_message = await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Recent message",
            participant_id=self.participant_id,
            created_time=timezone.now() - timedelta(minutes=30),
        )
        
        # Should return the most recent user message time
        last_time = await get_last_user_message_time("test-conv-123")
        assert last_time == recent_message.created_time

    async def test_get_last_user_message_time_no_messages(self):
        """Test getting last user message time when no messages exist."""
        last_time = await get_last_user_message_time("test-conv-123")
        assert last_time is None

    async def test_get_last_user_message_time_only_bot_messages(self):
        """Test getting last user message time when only bot messages exist."""
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="bot",
            text="Bot message",
            participant_id=self.participant_id,
        )
        
        last_time = await get_last_user_message_time("test-conv-123")
        assert last_time is None

    async def test_get_last_user_message_time_error_handling(self):
        """Test error handling in get_last_user_message_time."""
        # This should handle database errors gracefully
        with patch("chatbot.services.followup.Utterance.objects.filter") as mock_filter:
            mock_filter.side_effect = Exception("Database error")
            
            last_time = await get_last_user_message_time("test-conv-123")
            assert last_time is None

    async def test_is_user_idle_true(self):
        """Test is_user_idle when user is actually idle."""
        # Create a user message that's older than idle threshold
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Old message",
            participant_id=self.participant_id,
            created_time=timezone.now() - timedelta(minutes=10),  # 10 minutes ago
        )
        
        is_idle = await is_user_idle("test-conv-123", 5)  # 5 minute threshold
        assert is_idle

    async def test_is_user_idle_false(self):
        """Test is_user_idle when user is not idle."""
        # Create a recent user message
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Recent message",
            participant_id=self.participant_id,
            created_time=timezone.now() - timedelta(minutes=2),  # 2 minutes ago
        )
        
        is_idle = await is_user_idle("test-conv-123", 5)  # 5 minute threshold
        assert not is_idle

    async def test_is_user_idle_no_messages(self):
        """Test is_user_idle when no user messages exist."""
        is_idle = await is_user_idle("test-conv-123", 5)
        assert not is_idle

    async def test_generate_followup_message_success(self):
        """Test successful followup message generation."""
        # Create a user message that's idle
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Idle message",
            participant_id=self.participant_id,
            created_time=timezone.now() - timedelta(minutes=10),
        )
        
        with patch("chatbot.services.followup.run_chat_round") as mock_run_chat:
            mock_run_chat.return_value = "Hey! Are you still there? Need any help?"
            
            response_text, error = await generate_followup_message(
                "TestBot", "test-conv-123", self.participant_id,
            )
        
        assert error is None
        assert response_text == "Hey! Are you still there? Need any help?"

    async def test_generate_followup_message_bot_not_found(self):
        """Test followup generation with non-existent bot."""
        response_text, error = await generate_followup_message(
            "NonExistentBot", "test-conv-123", self.participant_id,
        )
        
        assert response_text is None
        assert "not found" in error

    async def test_generate_followup_message_followup_disabled(self):
        """Test followup generation when followup is disabled."""
        self.bot.follow_up_on_idle = False
        await sync_to_async(self.bot.save)()
        
        response_text, error = await generate_followup_message(
            "TestBot", "test-conv-123", self.participant_id,
        )
        
        assert response_text is None
        assert "Follow-up not enabled" in error

    async def test_generate_followup_message_no_instruction_prompt(self):
        """Test followup generation without instruction prompt."""
        self.bot.follow_up_instruction_prompt = ""
        await sync_to_async(self.bot.save)()
        
        response_text, error = await generate_followup_message(
            "TestBot", "test-conv-123", self.participant_id,
        )
        
        assert response_text is None
        assert "No follow-up instruction prompt configured" in error

    async def test_generate_followup_message_user_not_idle(self):
        """Test followup generation when user is not idle."""
        # Create a recent user message
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Recent message",
            participant_id=self.participant_id,
            created_time=timezone.now() - timedelta(minutes=2),
        )
        
        response_text, error = await generate_followup_message(
            "TestBot", "test-conv-123", self.participant_id,
        )
        
        assert response_text is None
        assert "User is not idle" in error

    async def test_generate_followup_message_exception_handling(self):
        """Test exception handling in followup generation."""
        with patch("chatbot.services.followup.Bot.objects.get") as mock_get:
            mock_get.side_effect = Exception("Unexpected error")
            
            response_text, error = await generate_followup_message(
                "TestBot", "test-conv-123", self.participant_id,
            )
        
        assert response_text is None
        assert "Unexpected error" in error


class TestFollowupAPIView(TestCase):
    """Test the FollowupAPIView."""

    def setUp(self):
        """Set up test data."""
        self.bot = BotFactory(
            name="APITestBot",
            follow_up_on_idle=True,
            idle_time_minutes=3,
            follow_up_instruction_prompt="Check in with the user.",
            chunk_messages=True,
        )
        
        self.conversation = ConversationFactory(
            conversation_id="api-test-conv-456",
            bot_name="APITestBot",
        )
        
        self.participant_id = "api-test-user-789"

    async def test_followup_api_success(self):
        """Test successful followup API request."""
        # Create idle user message
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Idle message",
            participant_id=self.participant_id,
            created_time=timezone.now() - timedelta(minutes=5),
        )
        
        with patch("chatbot.services.followup.generate_followup_message") as mock_generate:
            mock_generate.return_value = ("Followup response", None)
            
            with patch("chatbot.services.followup.human_like_chunks") as mock_chunks:
                mock_chunks.return_value = ["Followup", "response"]
                
                view = FollowupAPIView()
                request = MagicMock()
                request.body = json.dumps({
                    "bot_name": "APITestBot",
                    "conversation_id": "api-test-conv-456",
                    "participant_id": self.participant_id,
                }).encode()
                
                response = await view.post(request)
        
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["is_followup"]
        assert response_data["bot_name"] == "APITestBot"

    async def test_followup_api_missing_fields(self):
        """Test followup API with missing required fields."""
        view = FollowupAPIView()
        request = MagicMock()
        request.body = json.dumps({
            "bot_name": "APITestBot",
            "participant_id": self.participant_id,
        }).encode()
        
        response = await view.post(request)
        
        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert "Missing required fields" in response_data["error"]

    async def test_followup_api_empty_bot_name(self):
        """Test followup API with empty bot name."""
        view = FollowupAPIView()
        request = MagicMock()
        request.body = json.dumps({
            "bot_name": "",
            "conversation_id": "api-test-conv-456",
            "participant_id": self.participant_id,
        }).encode()
        
        response = await view.post(request)
        
        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert "Missing required fields" in response_data["error"]

    async def test_followup_api_invalid_json(self):
        """Test followup API with invalid JSON."""
        view = FollowupAPIView()
        request = MagicMock()
        request.body = "invalid json"
        
        response = await view.post(request)
        
        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert "Invalid JSON" in response_data["error"]

    async def test_followup_api_generation_error(self):
        """Test followup API when generation fails."""
        with patch("chatbot.services.followup.generate_followup_message") as mock_generate:
            mock_generate.return_value = (None, "Generation failed")
            
            view = FollowupAPIView()
            request = MagicMock()
            request.body = json.dumps({
                "bot_name": "APITestBot",
                "conversation_id": "api-test-conv-456",
                "participant_id": self.participant_id,
            }).encode()
            
            response = await view.post(request)
        
        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert "Generation failed" in response_data["error"]

    async def test_followup_api_without_chunking(self):
        """Test followup API when chunking is disabled."""
        # Disable chunking for the bot
        self.bot.chunk_messages = False
        await sync_to_async(self.bot.save)()
        
        # Create idle user message
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Idle message",
            participant_id=self.participant_id,
            created_time=timezone.now() - timedelta(minutes=5),
        )
        
        with patch("chatbot.services.followup.generate_followup_message") as mock_generate:
            mock_generate.return_value = ("Simple response", None)
            
            view = FollowupAPIView()
            request = MagicMock()
            request.body = json.dumps({
                "bot_name": "APITestBot",
                "conversation_id": "api-test-conv-456",
                "participant_id": self.participant_id,
            }).encode()
            
            response = await view.post(request)
        
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["response_chunks"]) == 1
        assert response_data["response_chunks"][0] == "Simple response"

    async def test_followup_api_exception_handling(self):
        """Test exception handling in followup API."""
        with patch("chatbot.services.followup.generate_followup_message") as mock_generate:
            mock_generate.side_effect = Exception("Unexpected error")
            
            view = FollowupAPIView()
            request = MagicMock()
            request.body = json.dumps({
                "bot_name": "APITestBot",
                "conversation_id": "api-test-conv-456",
                "participant_id": self.participant_id,
            }).encode()
            
            response = await view.post(request)
        
        assert response.status_code == 500
        response_data = json.loads(response.content)
        assert "Unexpected error" in response_data["error"]


class TestFollowupEdgeCases(TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test data."""
        self.bot = BotFactory(
            name="EdgeCaseBot",
            follow_up_on_idle=True,
            idle_time_minutes=1,  # Very short idle time
            follow_up_instruction_prompt="Edge case test.",
        )
        
        self.conversation = ConversationFactory(
            conversation_id="edge-case-conv-789",
            bot_name="EdgeCaseBot",
        )

    async def test_followup_exactly_at_idle_threshold(self):
        """Test followup when user message is exactly at idle threshold."""
        # Create message exactly at idle threshold
        idle_threshold = timezone.now() - timedelta(minutes=1)
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Threshold message",
            participant_id="edge-user",
            created_time=idle_threshold,
        )
        
        is_idle = await is_user_idle("edge-case-conv-789", 1)
        assert is_idle

    async def test_followup_just_below_idle_threshold(self):
        """Test followup when user message is just below idle threshold."""
        # Create message just below idle threshold
        just_below_threshold = timezone.now() - timedelta(minutes=1, seconds=-30)
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Just below threshold",
            participant_id="edge-user",
            created_time=just_below_threshold,
        )
        
        is_idle = await is_user_idle("edge-case-conv-789", 1)
        assert not is_idle

    async def test_followup_with_very_long_idle_time(self):
        """Test followup with very long idle time setting."""
        self.bot.idle_time_minutes = 1440  # 24 hours
        await sync_to_async(self.bot.save)()
        
        # Create message from 25 hours ago
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Very old message",
            participant_id="edge-user",
            created_time=timezone.now() - timedelta(hours=25),
        )
        
        is_idle = await is_user_idle("edge-case-conv-789", 1440)
        assert is_idle

    async def test_followup_with_zero_idle_time(self):
        """Test followup with zero idle time (edge case)."""
        self.bot.idle_time_minutes = 0
        await sync_to_async(self.bot.save)()
        
        # Create recent message
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Recent message",
            participant_id="edge-user",
            created_time=timezone.now() - timedelta(seconds=1),
        )
        
        is_idle = await is_user_idle("edge-case-conv-789", 0)
        assert is_idle  # Should be considered idle with 0 threshold


class TestFollowupEndToEnd(TestCase):
    """End-to-end tests for followup functionality."""

    def setUp(self):
        """Set up test data for followup testing."""
        # Create a bot with followup enabled
        self.bot = BotFactory(
            name="FollowupTestBot",
            prompt="You are a helpful test bot that follows up on idle users.",
            model_type="OpenAI",
            model_id="gpt-4",
            chunk_messages=True,
            follow_up_on_idle=True,
            idle_time_minutes=1,  # 1 minute for testing
            follow_up_instruction_prompt="Check in with the user and ask if they need help.",
        )
        
        # Create a persona for the bot
        self.persona = PersonaFactory(
            name="HelpfulPersona",
            instructions="Always be helpful and check in with users.",
        )
        self.bot.personas.add(self.persona)
        
        # Create a conversation
        self.conversation = ConversationFactory(
            conversation_id="followup-test-conv-123",
            bot_name="FollowupTestBot",
            participant_id="test-user-456",
            selected_persona=self.persona,
        )
        
        # Create initial bot message
        Utterance.objects.create(
            conversation=self.conversation,
            speaker_id="bot",
            bot_name="FollowupTestBot",
            text="Hello! I'm here to help. How can I assist you today?",
            participant_id="test-user-456",
        )

    def test_complete_followup_flow_success(self):
        """Test the complete successful followup flow."""
        # Step 1: Send a user message
        user_message = Utterance.objects.create(
            conversation=self.conversation,
            speaker_id="user",
            bot_name=None,
            text="Hello, I need some help with Python programming.",
            participant_id="test-user-456",
        )
        
        # Verify user message was created
        assert user_message.speaker_id == "user"
        assert user_message.text == "Hello, I need some help with Python programming."
        
        # Step 2: Wait for idle time (simulate by setting message time to past)
        idle_threshold = timezone.now() - timedelta(minutes=2)  # 2 minutes ago
        user_message.created_time = idle_threshold
        user_message.save()
        
        # Step 3: Test followup endpoint
        followup_data = {
            "bot_name": "FollowupTestBot",
            "conversation_id": "followup-test-conv-123",
            "participant_id": "test-user-456",
        }
        
        # Mock the run_chat_round function to avoid real API calls
        with patch("chatbot.services.followup.run_chat_round") as mock_run_chat:
            mock_run_chat.return_value = "Hi there! I noticed you haven't responded in a while. Do you need any help with your Python programming question?"
            
            # Make the followup request
            response = self.client.post(
                "/api/followup/",
                data=json.dumps(followup_data),
                content_type="application/json",
            )
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        
        assert "response" in response_data
        assert "response_chunks" in response_data
        assert "bot_name" in response_data
        assert response_data["is_followup"]
        assert response_data["bot_name"] == "FollowupTestBot"
        
        # Verify the response contains the expected followup message
        assert "Hi there! I noticed you haven't responded" in response_data["response"]
        
        # Verify chunks were created
        assert isinstance(response_data["response_chunks"], list)
        assert len(response_data["response_chunks"]) > 0

    def test_followup_with_disabled_bot(self):
        """Test followup when bot has followup disabled."""
        # Disable followup for the bot
        self.bot.follow_up_on_idle = False
        self.bot.save()
        
        followup_data = {
            "bot_name": "FollowupTestBot",
            "conversation_id": "followup-test-conv-123",
            "participant_id": "test-user-456",
        }
        
        response = self.client.post(
            "/api/followup/",
            data=json.dumps(followup_data),
            content_type="application/json",
        )
        
        # Should return error
        assert response.status_code == 400
        response_data = response.json()
        assert "error" in response_data
        assert "Follow-up not enabled" in response_data["error"]

    def test_followup_without_instruction_prompt(self):
        """Test followup when bot has no instruction prompt."""
        # Remove instruction prompt
        self.bot.follow_up_instruction_prompt = ""
        self.bot.save()
        
        followup_data = {
            "bot_name": "FollowupTestBot",
            "conversation_id": "followup-test-conv-123",
            "participant_id": "test-user-456",
        }
        
        response = self.client.post(
            "/api/followup/",
            data=json.dumps(followup_data),
            content_type="application/json",
        )
        
        # Should return error
        assert response.status_code == 400
        response_data = response.json()
        assert "error" in response_data
        assert "No follow-up instruction prompt configured" in response_data["error"]

    def test_followup_user_not_idle(self):
        """Test followup when user is not idle."""
        # Create a recent user message (not idle)
        recent_message = Utterance.objects.create(
            conversation=self.conversation,
            speaker_id="user",
            bot_name=None,
            text="I'm still here and active!",
            participant_id="test-user-456",
        )
        
        # Set message time to recent (within idle threshold)
        recent_time = timezone.now() - timedelta(seconds=30)  # 30 seconds ago
        recent_message.created_time = recent_time
        recent_message.save()
        
        followup_data = {
            "bot_name": "FollowupTestBot",
            "conversation_id": "followup-test-conv-123",
            "participant_id": "test-user-456",
        }
        
        response = self.client.post(
            "/api/followup/",
            data=json.dumps(followup_data),
            content_type="application/json",
        )
        
        # Should return error
        assert response.status_code == 400
        response_data = response.json()
        assert "error" in response_data
        assert "User is not idle" in response_data["error"]

    def test_followup_missing_required_fields(self):
        """Test followup with missing required fields."""
        # Test missing bot_name
        followup_data = {
            "conversation_id": "followup-test-conv-123",
            "participant_id": "test-user-456",
        }
        
        response = self.client.post(
            "/api/followup/",
            data=json.dumps(followup_data),
            content_type="application/json",
        )
        
        assert response.status_code == 400
        response_data = response.json()
        assert "error" in response_data
        assert "Missing required fields" in response_data["error"]
        
        # Test missing conversation_id
        followup_data = {
            "bot_name": "FollowupTestBot",
            "participant_id": "test-user-456",
        }
        
        response = self.client.post(
            "/api/followup/",
            data=json.dumps(followup_data),
            content_type="application/json",
        )
        
        assert response.status_code == 400
        response_data = response.json()
        assert "error" in response_data
        assert "Missing required fields" in response_data["error"]

    def test_followup_invalid_json(self):
        """Test followup with invalid JSON."""
        response = self.client.post(
            "/api/followup/",
            data="invalid json data",
            content_type="application/json",
        )
        
        assert response.status_code == 400
        response_data = response.json()
        assert "error" in response_data
        assert "Invalid JSON" in response_data["error"]

    def test_followup_bot_not_found(self):
        """Test followup with non-existent bot."""
        followup_data = {
            "bot_name": "NonExistentBot",
            "conversation_id": "followup-test-conv-123",
            "participant_id": "test-user-456",
        }
        
        response = self.client.post(
            "/api/followup/",
            data=json.dumps(followup_data),
            content_type="application/json",
        )
        
        assert response.status_code == 400
        response_data = response.json()
        assert "error" in response_data
        assert "not found" in response_data["error"]

    def test_followup_with_chunking_disabled(self):
        """Test followup when bot has chunking disabled."""
        # Disable chunking for the bot
        self.bot.chunk_messages = False
        self.bot.save()
        
        # Make user idle
        user_message = Utterance.objects.create(
            conversation=self.conversation,
            speaker_id="user",
            bot_name=None,
            text="Test message",
            participant_id="test-user-456",
        )
        user_message.created_time = timezone.now() - timedelta(minutes=2)
        user_message.save()
        
        followup_data = {
            "bot_name": "FollowupTestBot",
            "conversation_id": "followup-test-conv-123",
            "participant_id": "test-user-456",
        }
        
        with patch("chatbot.services.followup.run_chat_round") as mock_run_chat:
            mock_run_chat.return_value = "Simple followup message without chunks."
            
            response = self.client.post(
                "/api/followup/",
                data=json.dumps(followup_data),
                content_type="application/json",
            )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Should return single chunk when chunking is disabled
        assert len(response_data["response_chunks"]) == 1
        assert response_data["response_chunks"][0] == "Simple followup message without chunks."

    def test_followup_conversation_initialization_flow(self):
        """Test the complete flow from conversation initialization to followup."""
        # Step 1: Initialize a new conversation
        init_data = {
            "bot_name": "FollowupTestBot",
            "conversation_id": "new-followup-conv-789",
            "participant_id": "new-test-user",
            "study_name": "followup_study",
            "user_group": "treatment",
            "survey_id": "followup_survey_123",
        }
        
        response = self.client.post(
            "/api/initialize_conversation/",
            data=json.dumps(init_data),
            content_type="application/json",
        )
        
        assert response.status_code == 200
        
        # Step 2: Send a user message
        chat_data = {
            "message": "Hello, I'm starting a new conversation.",
            "bot_name": "FollowupTestBot",
            "conversation_id": "new-followup-conv-789",
            "participant_id": "new-test-user",
        }
        
        with patch("chatbot.services.runchat.run_chat_round") as mock_run_chat:
            mock_run_chat.return_value = "Hello! I'm here to help you with your new conversation."
            
            response = self.client.post(
                "/api/chatbot/",
                data=json.dumps(chat_data),
                content_type="application/json",
            )
        
        assert response.status_code == 200
        
        # Step 3: Wait and test followup
        # Create a user message and make it idle
        conversation = Conversation.objects.get(conversation_id="new-followup-conv-789")
        user_message = Utterance.objects.create(
            conversation=conversation,
            speaker_id="user",
            bot_name=None,
            text="I'm waiting for followup",
            participant_id="new-test-user",
        )
        user_message.created_time = timezone.now() - timedelta(minutes=2)
        user_message.save()
        
        # Step 4: Test followup
        followup_data = {
            "bot_name": "FollowupTestBot",
            "conversation_id": "new-followup-conv-789",
            "participant_id": "new-test-user",
        }
        
        with patch("chatbot.services.followup.run_chat_round") as mock_run_chat:
            mock_run_chat.return_value = "Hey there! I noticed you haven't responded. Everything okay?"
            
            response = self.client.post(
                "/api/followup/",
                data=json.dumps(followup_data),
                content_type="application/json",
            )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["is_followup"]
        assert "Hey there! I noticed you haven't responded" in response_data["response"]

    def test_followup_bot_configuration_endpoint(self):
        """Test the bot configuration endpoint to verify followup settings."""
        response = self.client.get("/api/bots/")
        
        assert response.status_code == 200
        bots_data = response.json()
        
        # Find our test bot
        test_bot = next((b for b in bots_data["bots"] if b["name"] == "FollowupTestBot"), None)
        assert test_bot is not None
        
        # Verify followup configuration
        assert test_bot["follow_up_on_idle"]
        assert test_bot["idle_time_minutes"] == 1
        assert "Check in with the user" in test_bot["follow_up_instruction_prompt"]

    def test_followup_error_handling(self):
        """Test error handling in followup functionality."""
        # Test with malformed data
        malformed_data = {
            "bot_name": "FollowupTestBot",
            "conversation_id": None,  # Invalid conversation_id
            "participant_id": "test-user-456",
        }
        
        response = self.client.post(
            "/api/followup/",
            data=json.dumps(malformed_data),
            content_type="application/json",
        )
        
        assert response.status_code == 400
        
        # Test with empty bot name
        empty_bot_data = {
            "bot_name": "",
            "conversation_id": "followup-test-conv-123",
            "participant_id": "test-user-456",
        }
        
        response = self.client.post(
            "/api/followup/",
            data=json.dumps(empty_bot_data),
            content_type="application/json",
        )
        
        assert response.status_code == 400

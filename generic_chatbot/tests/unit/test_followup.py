"""
Unit tests for the followup service.

These tests focus on testing individual functions and components
of the followup service in isolation.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from django.test import TestCase
from django.utils import timezone
from asgiref.sync import sync_to_async

from chatbot.models import Bot, Conversation, Utterance, Persona
from chatbot.services.followup import (
    get_last_user_message_time,
    is_user_idle,
    generate_followup_message,
    FollowupAPIView
)
from tests.factories import BotFactory, ConversationFactory, PersonaFactory


class TestFollowupFunctions(TestCase):
    """Test individual followup functions."""

    def setUp(self):
        """Set up test data."""
        self.bot = BotFactory(
            name="TestBot",
            follow_up_on_idle=True,
            idle_time_minutes=5,
            follow_up_instruction_prompt="Check in with the user."
        )
        
        self.conversation = ConversationFactory(
            conversation_id="test-conv-123",
            bot_name="TestBot"
        )
        
        self.participant_id = "test-user-456"

    async def test_get_last_user_message_time_with_messages(self):
        """Test getting last user message time when messages exist."""
        # Create user messages with different timestamps
        old_message = await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Old message",
            participant_id=self.participant_id,
            created_time=timezone.now() - timedelta(hours=2)
        )
        
        recent_message = await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Recent message",
            participant_id=self.participant_id,
            created_time=timezone.now() - timedelta(minutes=30)
        )
        
        # Should return the most recent user message time
        last_time = await get_last_user_message_time("test-conv-123")
        self.assertEqual(last_time, recent_message.created_time)

    async def test_get_last_user_message_time_no_messages(self):
        """Test getting last user message time when no messages exist."""
        last_time = await get_last_user_message_time("test-conv-123")
        self.assertIsNone(last_time)

    async def test_get_last_user_message_time_only_bot_messages(self):
        """Test getting last user message time when only bot messages exist."""
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="bot",
            text="Bot message",
            participant_id=self.participant_id
        )
        
        last_time = await get_last_user_message_time("test-conv-123")
        self.assertIsNone(last_time)

    async def test_get_last_user_message_time_error_handling(self):
        """Test error handling in get_last_user_message_time."""
        # This should handle database errors gracefully
        with patch('chatbot.services.followup.Utterance.objects.filter') as mock_filter:
            mock_filter.side_effect = Exception("Database error")
            
            last_time = await get_last_user_message_time("test-conv-123")
            self.assertIsNone(last_time)

    async def test_is_user_idle_true(self):
        """Test is_user_idle when user is actually idle."""
        # Create a user message that's older than idle threshold
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Old message",
            participant_id=self.participant_id,
            created_time=timezone.now() - timedelta(minutes=10)  # 10 minutes ago
        )
        
        is_idle = await is_user_idle("test-conv-123", 5)  # 5 minute threshold
        self.assertTrue(is_idle)

    async def test_is_user_idle_false(self):
        """Test is_user_idle when user is not idle."""
        # Create a recent user message
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Recent message",
            participant_id=self.participant_id,
            created_time=timezone.now() - timedelta(minutes=2)  # 2 minutes ago
        )
        
        is_idle = await is_user_idle("test-conv-123", 5)  # 5 minute threshold
        self.assertFalse(is_idle)

    async def test_is_user_idle_no_messages(self):
        """Test is_user_idle when no user messages exist."""
        is_idle = await is_user_idle("test-conv-123", 5)
        self.assertFalse(is_idle)

    async def test_generate_followup_message_success(self):
        """Test successful followup message generation."""
        # Create a user message that's idle
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Idle message",
            participant_id=self.participant_id,
            created_time=timezone.now() - timedelta(minutes=10)
        )
        
        with patch('chatbot.services.followup.run_chat_round') as mock_run_chat:
            mock_run_chat.return_value = "Hey! Are you still there? Need any help?"
            
            response_text, error = await generate_followup_message(
                "TestBot", "test-conv-123", self.participant_id
            )
        
        self.assertIsNone(error)
        self.assertEqual(response_text, "Hey! Are you still there? Need any help?")

    async def test_generate_followup_message_bot_not_found(self):
        """Test followup generation with non-existent bot."""
        response_text, error = await generate_followup_message(
            "NonExistentBot", "test-conv-123", self.participant_id
        )
        
        self.assertIsNone(response_text)
        self.assertIn("not found", error)

    async def test_generate_followup_message_followup_disabled(self):
        """Test followup generation when followup is disabled."""
        self.bot.follow_up_on_idle = False
        await sync_to_async(self.bot.save)()
        
        response_text, error = await generate_followup_message(
            "TestBot", "test-conv-123", self.participant_id
        )
        
        self.assertIsNone(response_text)
        self.assertIn("Follow-up not enabled", error)

    async def test_generate_followup_message_no_instruction_prompt(self):
        """Test followup generation without instruction prompt."""
        self.bot.follow_up_instruction_prompt = ""
        await sync_to_async(self.bot.save)()
        
        response_text, error = await generate_followup_message(
            "TestBot", "test-conv-123", self.participant_id
        )
        
        self.assertIsNone(response_text)
        self.assertIn("No follow-up instruction prompt configured", error)

    async def test_generate_followup_message_user_not_idle(self):
        """Test followup generation when user is not idle."""
        # Create a recent user message
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Recent message",
            participant_id=self.participant_id,
            created_time=timezone.now() - timedelta(minutes=2)
        )
        
        response_text, error = await generate_followup_message(
            "TestBot", "test-conv-123", self.participant_id
        )
        
        self.assertIsNone(response_text)
        self.assertIn("User is not idle", error)

    async def test_generate_followup_message_exception_handling(self):
        """Test exception handling in followup generation."""
        with patch('chatbot.services.followup.Bot.objects.get') as mock_get:
            mock_get.side_effect = Exception("Unexpected error")
            
            response_text, error = await generate_followup_message(
                "TestBot", "test-conv-123", self.participant_id
            )
        
        self.assertIsNone(response_text)
        self.assertIn("Unexpected error", error)


class TestFollowupAPIView(TestCase):
    """Test the FollowupAPIView."""

    def setUp(self):
        """Set up test data."""
        self.bot = BotFactory(
            name="APITestBot",
            follow_up_on_idle=True,
            idle_time_minutes=3,
            follow_up_instruction_prompt="Check in with the user.",
            chunk_messages=True
        )
        
        self.conversation = ConversationFactory(
            conversation_id="api-test-conv-456",
            bot_name="APITestBot"
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
            created_time=timezone.now() - timedelta(minutes=5)
        )
        
        with patch('chatbot.services.followup.generate_followup_message') as mock_generate:
            mock_generate.return_value = ("Followup response", None)
            
            with patch('chatbot.services.followup.human_like_chunks') as mock_chunks:
                mock_chunks.return_value = ["Followup", "response"]
                
                view = FollowupAPIView()
                request = MagicMock()
                request.body = json.dumps({
                    "bot_name": "APITestBot",
                    "conversation_id": "api-test-conv-456",
                    "participant_id": self.participant_id
                }).encode()
                
                response = await view.post(request)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['is_followup'])
        self.assertEqual(response_data['bot_name'], 'APITestBot')

    async def test_followup_api_missing_fields(self):
        """Test followup API with missing required fields."""
        view = FollowupAPIView()
        request = MagicMock()
        request.body = json.dumps({
            "bot_name": "APITestBot",
            "participant_id": self.participant_id
        }).encode()
        
        response = await view.post(request)
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('Missing required fields', response_data['error'])

    async def test_followup_api_empty_bot_name(self):
        """Test followup API with empty bot name."""
        view = FollowupAPIView()
        request = MagicMock()
        request.body = json.dumps({
            "bot_name": "",
            "conversation_id": "api-test-conv-456",
            "participant_id": self.participant_id
        }).encode()
        
        response = await view.post(request)
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('Missing required fields', response_data['error'])

    async def test_followup_api_invalid_json(self):
        """Test followup API with invalid JSON."""
        view = FollowupAPIView()
        request = MagicMock()
        request.body = "invalid json"
        
        response = await view.post(request)
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('Invalid JSON', response_data['error'])

    async def test_followup_api_generation_error(self):
        """Test followup API when generation fails."""
        with patch('chatbot.services.followup.generate_followup_message') as mock_generate:
            mock_generate.return_value = (None, "Generation failed")
            
            view = FollowupAPIView()
            request = MagicMock()
            request.body = json.dumps({
                "bot_name": "APITestBot",
                "conversation_id": "api-test-conv-456",
                "participant_id": self.participant_id
            }).encode()
            
            response = await view.post(request)
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('Generation failed', response_data['error'])

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
            created_time=timezone.now() - timedelta(minutes=5)
        )
        
        with patch('chatbot.services.followup.generate_followup_message') as mock_generate:
            mock_generate.return_value = ("Simple response", None)
            
            view = FollowupAPIView()
            request = MagicMock()
            request.body = json.dumps({
                "bot_name": "APITestBot",
                "conversation_id": "api-test-conv-456",
                "participant_id": self.participant_id
            }).encode()
            
            response = await view.post(request)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['response_chunks']), 1)
        self.assertEqual(response_data['response_chunks'][0], "Simple response")

    async def test_followup_api_exception_handling(self):
        """Test exception handling in followup API."""
        with patch('chatbot.services.followup.generate_followup_message') as mock_generate:
            mock_generate.side_effect = Exception("Unexpected error")
            
            view = FollowupAPIView()
            request = MagicMock()
            request.body = json.dumps({
                "bot_name": "APITestBot",
                "conversation_id": "api-test-conv-456",
                "participant_id": self.participant_id
            }).encode()
            
            response = await view.post(request)
        
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.content)
        self.assertIn('Unexpected error', response_data['error'])


class TestFollowupEdgeCases(TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test data."""
        self.bot = BotFactory(
            name="EdgeCaseBot",
            follow_up_on_idle=True,
            idle_time_minutes=1,  # Very short idle time
            follow_up_instruction_prompt="Edge case test."
        )
        
        self.conversation = ConversationFactory(
            conversation_id="edge-case-conv-789",
            bot_name="EdgeCaseBot"
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
            created_time=idle_threshold
        )
        
        is_idle = await is_user_idle("edge-case-conv-789", 1)
        self.assertTrue(is_idle)

    async def test_followup_just_below_idle_threshold(self):
        """Test followup when user message is just below idle threshold."""
        # Create message just below idle threshold
        just_below_threshold = timezone.now() - timedelta(minutes=1, seconds=-30)
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Just below threshold",
            participant_id="edge-user",
            created_time=just_below_threshold
        )
        
        is_idle = await is_user_idle("edge-case-conv-789", 1)
        self.assertFalse(is_idle)

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
            created_time=timezone.now() - timedelta(hours=25)
        )
        
        is_idle = await is_user_idle("edge-case-conv-789", 1440)
        self.assertTrue(is_idle)

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
            created_time=timezone.now() - timedelta(seconds=1)
        )
        
        is_idle = await is_user_idle("edge-case-conv-789", 0)
        self.assertTrue(is_idle)  # Should be considered idle with 0 threshold

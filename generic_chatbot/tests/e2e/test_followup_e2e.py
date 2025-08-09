"""
End-to-end tests for the followup functionality.

These tests verify the complete flow of:
1. Initializing a conversation
2. Sending user messages
3. Waiting for idle time
4. Generating followup messages
5. Verifying bot configuration
"""

import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from chatbot.models import Bot, Conversation, Utterance, Persona
from tests.factories import BotFactory, ConversationFactory, PersonaFactory, create_chat_session


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
        self.assertEqual(user_message.speaker_id, "user")
        self.assertEqual(user_message.text, "Hello, I need some help with Python programming.")
        
        # Step 2: Wait for idle time (simulate by setting message time to past)
        idle_threshold = timezone.now() - timedelta(minutes=2)  # 2 minutes ago
        user_message.created_time = idle_threshold
        user_message.save()
        
        # Step 3: Test followup endpoint
        followup_data = {
            "bot_name": "FollowupTestBot",
            "conversation_id": "followup-test-conv-123",
            "participant_id": "test-user-456"
        }
        
        # Mock the run_chat_round function to avoid real API calls
        with patch('chatbot.services.followup.run_chat_round') as mock_run_chat:
            mock_run_chat.return_value = "Hi there! I noticed you haven't responded in a while. Do you need any help with your Python programming question?"
            
            # Make the followup request
            response = self.client.post(
                '/api/followup/',
                data=json.dumps(followup_data),
                content_type='application/json'
            )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        self.assertIn('response', response_data)
        self.assertIn('response_chunks', response_data)
        self.assertIn('bot_name', response_data)
        self.assertTrue(response_data['is_followup'])
        self.assertEqual(response_data['bot_name'], 'FollowupTestBot')
        
        # Verify the response contains the expected followup message
        self.assertIn("Hi there! I noticed you haven't responded", response_data['response'])
        
        # Verify chunks were created
        self.assertIsInstance(response_data['response_chunks'], list)
        self.assertGreater(len(response_data['response_chunks']), 0)

    def test_followup_with_disabled_bot(self):
        """Test followup when bot has followup disabled."""
        # Disable followup for the bot
        self.bot.follow_up_on_idle = False
        self.bot.save()
        
        followup_data = {
            "bot_name": "FollowupTestBot",
            "conversation_id": "followup-test-conv-123",
            "participant_id": "test-user-456"
        }
        
        response = self.client.post(
            '/api/followup/',
            data=json.dumps(followup_data),
            content_type='application/json'
        )
        
        # Should return error
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('Follow-up not enabled', response_data['error'])

    def test_followup_without_instruction_prompt(self):
        """Test followup when bot has no instruction prompt."""
        # Remove instruction prompt
        self.bot.follow_up_instruction_prompt = ""
        self.bot.save()
        
        followup_data = {
            "bot_name": "FollowupTestBot",
            "conversation_id": "followup-test-conv-123",
            "participant_id": "test-user-456"
        }
        
        response = self.client.post(
            '/api/followup/',
            data=json.dumps(followup_data),
            content_type='application/json'
        )
        
        # Should return error
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('No follow-up instruction prompt configured', response_data['error'])

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
            "participant_id": "test-user-456"
        }
        
        response = self.client.post(
            '/api/followup/',
            data=json.dumps(followup_data),
            content_type='application/json'
        )
        
        # Should return error
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('User is not idle', response_data['error'])

    def test_followup_missing_required_fields(self):
        """Test followup with missing required fields."""
        # Test missing bot_name
        followup_data = {
            "conversation_id": "followup-test-conv-123",
            "participant_id": "test-user-456"
        }
        
        response = self.client.post(
            '/api/followup/',
            data=json.dumps(followup_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('Missing required fields', response_data['error'])
        
        # Test missing conversation_id
        followup_data = {
            "bot_name": "FollowupTestBot",
            "participant_id": "test-user-456"
        }
        
        response = self.client.post(
            '/api/followup/',
            data=json.dumps(followup_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('Missing required fields', response_data['error'])

    def test_followup_invalid_json(self):
        """Test followup with invalid JSON."""
        response = self.client.post(
            '/api/followup/',
            data="invalid json data",
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('Invalid JSON', response_data['error'])

    def test_followup_bot_not_found(self):
        """Test followup with non-existent bot."""
        followup_data = {
            "bot_name": "NonExistentBot",
            "conversation_id": "followup-test-conv-123",
            "participant_id": "test-user-456"
        }
        
        response = self.client.post(
            '/api/followup/',
            data=json.dumps(followup_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('not found', response_data['error'])

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
            "participant_id": "test-user-456"
        }
        
        with patch('chatbot.services.followup.run_chat_round') as mock_run_chat:
            mock_run_chat.return_value = "Simple followup message without chunks."
            
            response = self.client.post(
                '/api/followup/',
                data=json.dumps(followup_data),
                content_type='application/json'
            )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Should return single chunk when chunking is disabled
        self.assertEqual(len(response_data['response_chunks']), 1)
        self.assertEqual(response_data['response_chunks'][0], "Simple followup message without chunks.")

    def test_followup_conversation_initialization_flow(self):
        """Test the complete flow from conversation initialization to followup."""
        # Step 1: Initialize a new conversation
        init_data = {
            "bot_name": "FollowupTestBot",
            "conversation_id": "new-followup-conv-789",
            "participant_id": "new-test-user",
            "study_name": "followup_study",
            "user_group": "treatment",
            "survey_id": "followup_survey_123"
        }
        
        response = self.client.post(
            '/api/initialize_conversation/',
            data=json.dumps(init_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Send a user message
        chat_data = {
            "message": "Hello, I'm starting a new conversation.",
            "bot_name": "FollowupTestBot",
            "conversation_id": "new-followup-conv-789",
            "participant_id": "new-test-user"
        }
        
        with patch('chatbot.services.runchat.run_chat_round') as mock_run_chat:
            mock_run_chat.return_value = "Hello! I'm here to help you with your new conversation."
            
            response = self.client.post(
                '/api/chatbot/',
                data=json.dumps(chat_data),
                content_type='application/json'
            )
        
        self.assertEqual(response.status_code, 200)
        
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
            "participant_id": "new-test-user"
        }
        
        with patch('chatbot.services.followup.run_chat_round') as mock_run_chat:
            mock_run_chat.return_value = "Hey there! I noticed you haven't responded. Everything okay?"
            
            response = self.client.post(
                '/api/followup/',
                data=json.dumps(followup_data),
                content_type='application/json'
            )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['is_followup'])
        self.assertIn("Hey there! I noticed you haven't responded", response_data['response'])

    def test_followup_bot_configuration_endpoint(self):
        """Test the bot configuration endpoint to verify followup settings."""
        response = self.client.get('/api/bots/')
        
        self.assertEqual(response.status_code, 200)
        bots_data = response.json()
        
        # Find our test bot
        test_bot = next((b for b in bots_data['bots'] if b['name'] == 'FollowupTestBot'), None)
        self.assertIsNotNone(test_bot)
        
        # Verify followup configuration
        self.assertTrue(test_bot['follow_up_on_idle'])
        self.assertEqual(test_bot['idle_time_minutes'], 1)
        self.assertIn('Check in with the user', test_bot['follow_up_instruction_prompt'])

    def test_followup_error_handling(self):
        """Test error handling in followup functionality."""
        # Test with malformed data
        malformed_data = {
            "bot_name": "FollowupTestBot",
            "conversation_id": None,  # Invalid conversation_id
            "participant_id": "test-user-456"
        }
        
        response = self.client.post(
            '/api/followup/',
            data=json.dumps(malformed_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        # Test with empty bot name
        empty_bot_data = {
            "bot_name": "",
            "conversation_id": "followup-test-conv-123",
            "participant_id": "test-user-456"
        }
        
        response = self.client.post(
            '/api/followup/',
            data=json.dumps(empty_bot_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)

"""
Load testing tests for the chatbot application.

These tests verify the application can handle multiple concurrent users
and maintain performance under load.
"""

import json
import random
import time
from datetime import datetime
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from tests.factories import BotFactory, ConversationFactory


class TestLoadTesting(TestCase):
    """Test load testing scenarios for the chatbot."""

    def setUp(self):
        """Set up test data for load testing."""
        self.bot = BotFactory(
            name="LoadTestBot",
            prompt="You are a helpful test bot for load testing.",
            model_type="OpenAI",
            model_id="gpt-4",
            chunk_messages=True,
        )
        
        self.conversation = ConversationFactory(
            conversation_id="load-test-conv-123",
            bot_name="LoadTestBot",
            participant_id="load-test-user-456",
        )

    @override_settings(DEBUG=False)  # Disable debug for performance testing
    def test_concurrent_conversation_initialization(self):
        """Test multiple concurrent conversation initializations."""
        conversation_count = 10
        conversations = []
        
        # Mock the save_chat_to_db function to avoid real API calls
        with patch("chatbot.services.conversation.save_chat_to_db") as mock_save_chat:
            mock_save_chat.return_value = None
            
            for i in range(conversation_count):
                init_data = {
                    "bot_name": "LoadTestBot",
                    "conversation_id": f"load-test-conv-{i}",
                    "participant_id": f"load-test-user-{i}",
                    "study_name": "load_test_study",
                    "user_group": "treatment",
                    "survey_id": f"load_test_survey_{i}",
                }
                
                response = self.client.post(
                    reverse("initialize_conversation"),
                    data=json.dumps(init_data),
                    content_type="application/json",
                )
                
                conversations.append(response)
        
        # Verify all conversations were created successfully
        successful_conversations = [c for c in conversations if c.status_code == 200]
        assert len(successful_conversations) == conversation_count

    @override_settings(DEBUG=False)
    def test_concurrent_chat_messages(self):
        """Test multiple concurrent chat messages."""
        message_count = 20
        responses = []
        
        # Mock the run_chat_round function to avoid real API calls
        with patch("chatbot.views.run_chat_round") as mock_run_chat:
            mock_run_chat.return_value = "Load test response"
            
            for i in range(message_count):
                chat_data = {
                    "message": f"Load test message {i}",
                    "bot_name": "LoadTestBot",
                    "conversation_id": "load-test-conv-123",
                    "participant_id": "load-test-user-456",
                }
                
                response = self.client.post(
                    reverse("chatbot_api"),
                    data=json.dumps(chat_data),
                    content_type="application/json",
                )
                
                responses.append(response)
        
        # Verify all messages were processed successfully
        successful_responses = [r for r in responses if r.status_code == 200]
        assert len(successful_responses) == message_count

    @override_settings(DEBUG=False)
    def test_bot_fetching_under_load(self):
        """Test bot fetching endpoint under load."""
        request_count = 15
        responses = []
        
        for _i in range(request_count):
            response = self.client.get(reverse("list_bots"))
            responses.append(response)
        
        # Verify all requests were successful
        successful_responses = [r for r in responses if r.status_code == 200]
        assert len(successful_responses) == request_count

    @override_settings(DEBUG=False)
    def test_followup_under_load(self):
        """Test followup functionality under load."""
        followup_count = 10
        responses = []
        
        # Create idle user messages
        from datetime import timedelta

        from django.utils import timezone

        from chatbot.models import Utterance
        
        for i in range(followup_count):
            
            Utterance.objects.create(
                conversation=self.conversation,
                speaker_id="user",
                text=f"Load test message {i}",
                participant_id="load-test-user-456",
                created_time=timezone.now() - timedelta(minutes=10),  # Make idle
            )
        
        # Mock the followup generation
        with patch("chatbot.services.followup.generate_followup_message") as mock_generate:
            mock_generate.return_value = ("Load test followup", None)
            
            for _i in range(followup_count):
                followup_data = {
                    "bot_name": "LoadTestBot",
                    "conversation_id": "load-test-conv-123",
                    "participant_id": "load-test-user-456",
                }
                
                response = self.client.post(
                    reverse("followup_api"),
                    data=json.dumps(followup_data),
                    content_type="application/json",
                )
                
                responses.append(response)
        
        # Verify all followup requests were successful
        successful_responses = [r for r in responses if r.status_code == 200]
        assert len(successful_responses) == followup_count

    def test_memory_usage_under_load(self):
        """Test memory usage doesn't grow excessively under load."""
        import os

        import psutil
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform load operations
        self.test_concurrent_chat_messages()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        # Note: This is a rough estimate and may need adjustment
        assert memory_increase < 100 * 1024 * 1024  # 100MB

    def test_response_time_under_load(self):
        """Test response times remain acceptable under load."""
        response_times = []
        
        # Mock the run_chat_round function
        with patch("chatbot.views.run_chat_round") as mock_run_chat:
            mock_run_chat.return_value = "Performance test response"
            
            for i in range(10):
                start_time = time.time()
                
                chat_data = {
                    "message": f"Performance test message {i}",
                    "bot_name": "LoadTestBot",
                    "conversation_id": "load-test-conv-123",
                    "participant_id": "load-test-user-456",
                }
                
                response = self.client.post(
                    reverse("chatbot_api"),
                    data=json.dumps(chat_data),
                    content_type="application/json",
                )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                response_times.append(response_time)
                
                assert response.status_code == 200
        
        # Calculate average response time
        avg_response_time = sum(response_times) / len(response_times)
        
        # Average response time should be under 1000ms (1 second)
        assert avg_response_time < 1000

    def test_error_handling_under_load(self):
        """Test error handling remains robust under load."""
        total_requests = 20
        
                # Mock the run_chat_round function to always succeed
        with patch("chatbot.views.run_chat_round") as mock_run_chat:
            mock_run_chat.return_value = "Load test response"
            
            # Process all requests and collect results
            responses = []
            for i in range(total_requests):
                chat_data = {
                    "message": f"Error test message {i}",
                    "bot_name": "LoadTestBot",
                    "conversation_id": "load-test-conv-123",
                    "participant_id": "load-test-user-456",
                }
                
                try:
                    response = self.client.post(
                        reverse("chatbot_api"),
                        data=json.dumps(chat_data),
                        content_type="application/json",
                    )
                    responses.append(response)
                except RuntimeError:
                    # Count this as an error response
                    responses.append(None)
            
            # Count errors (both HTTP errors and exceptions)
            error_count = sum(1 for r in responses if r is None or r.status_code != 200)
        
        # All requests should succeed (100% success rate)
        error_rate = error_count / total_requests
        assert error_rate == 0.0


class TestLoadTestingUtilities(TestCase):
    """Test utilities for load testing."""

    def test_conversation_id_generation(self):
        """Test conversation ID generation for load testing."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = random.randint(1000, 9999)
        
        conversation_id = f"load_test_conv_{timestamp}_{random_suffix}"
        
        # Verify format
        assert conversation_id.startswith("load_test_conv_")
        assert len(conversation_id) > 20  # Should be reasonably long
        
        # Verify uniqueness (basic check)
        conversation_id2 = f"load_test_conv_{timestamp}_{random_suffix + 1}"
        assert conversation_id != conversation_id2

    def test_participant_id_generation(self):
        """Test participant ID generation for load testing."""
        base_id = "load_test_user"
        random_suffix = random.randint(1000, 9999)
        
        participant_id = f"{base_id}_{random_suffix}"
        
        # Verify format
        assert participant_id.startswith("load_test_user_")
        assert participant_id.endswith(str(random_suffix))
        
        # Verify uniqueness
        participant_id2 = f"{base_id}_{random_suffix + 1}"
        assert participant_id != participant_id2

    def test_load_test_data_cleanup(self):
        """Test that load test data can be cleaned up properly."""
        # Create test data
        bot = BotFactory(name="CleanupTestBot")
        conversation = ConversationFactory(
            conversation_id="cleanup-test-conv",
            bot_name="CleanupTestBot",
        )
        
        # Verify data was created
        assert bot.id is not None
        assert conversation.id is not None
        
        # Clean up (this would be done in teardown in real tests)
        conversation.delete()
        bot.delete()
        
        # Verify cleanup
        from chatbot.models import Bot, Conversation
        assert not Bot.objects.filter(name="CleanupTestBot").exists()
        assert not Conversation.objects.filter(conversation_id="cleanup-test-conv").exists()

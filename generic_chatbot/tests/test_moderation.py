from unittest.mock import Mock, patch

import pytest
from django.test import override_settings

from chatbot.services.moderation import moderate_message


class TestModeration:
    """Test the moderation service for content filtering."""
    
    @pytest.mark.unit
    @patch("chatbot.services.moderation.model_dump")
    @patch("chatbot.services.moderation.OpenAI")
    @override_settings(MODERATION_VALUES_FOR_BLOCKED={"harassment": 0.7, "hate": 0.7, "sexual": 0.7, "self_harm": 0.7, "violence": 0.7})
    def test_moderation_clean_message(self, mock_openai_class, mock_model_dump):
        """Test that clean messages pass moderation."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock moderation response for clean content
        mock_response = Mock()
        mock_response.results = [Mock()]
        
        # Mock category_scores
        mock_category_scores = Mock()
        mock_response.results[0].category_scores = mock_category_scores
        
        # Mock model_dump to return a proper dictionary
        mock_model_dump.return_value = {
            "harassment": 0.1,
            "hate": 0.2,
            "sexual": 0.1,
            "self_harm": 0.0,
            "violence": 0.1,
        }
        
        mock_client.moderations.create.return_value = mock_response
        
        result = moderate_message("Hello, how are you today?")
        
        assert result == ""
        mock_client.moderations.create.assert_called_once_with(
            input="Hello, how are you today?",
            model="omni-moderation-latest",
        )
    
    @pytest.mark.unit
    @patch("chatbot.services.moderation.model_dump")
    @patch("chatbot.services.moderation.OpenAI")
    @override_settings(MODERATION_VALUES_FOR_BLOCKED={"harassment": 0.7, "hate": 0.7, "sexual": 0.7, "self_harm": 0.7, "violence": 0.7})
    def test_moderation_blocked_message_harassment(self, mock_openai_class, mock_model_dump):
        """Test that messages with high harassment scores are blocked."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock moderation response for blocked content
        mock_response = Mock()
        mock_response.results = [Mock()]
        
        # Mock category_scores
        mock_category_scores = Mock()
        mock_response.results[0].category_scores = mock_category_scores
        
        # Mock model_dump to return a proper dictionary
        mock_model_dump.return_value = {
            "harassment": 0.8,
            "hate": 0.2,
            "sexual": 0.1,
        }
        
        mock_client.moderations.create.return_value = mock_response
        
        result = moderate_message("You're an idiot and I hate you!")
        
        assert result == "harassment"
    
    @pytest.mark.unit
    @patch("chatbot.services.moderation.model_dump")
    @patch("chatbot.services.moderation.OpenAI")
    @override_settings(MODERATION_VALUES_FOR_BLOCKED={"harassment": 0.7, "hate": 0.7, "sexual": 0.7, "self_harm": 0.7, "violence": 0.7})
    def test_moderation_blocked_message_hate(self, mock_openai_class, mock_model_dump):
        """Test that messages with high hate scores are blocked."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock moderation response for blocked content
        mock_response = Mock()
        mock_response.results = [Mock()]
        
        # Mock category_scores
        mock_category_scores = Mock()
        mock_response.results[0].category_scores = mock_category_scores
        
        # Mock model_dump to return a proper dictionary
        mock_model_dump.return_value = {
            "harassment": 0.1,
            "hate": 0.9,
            "sexual": 0.1,
        }
        
        mock_client.moderations.create.return_value = mock_response
        
        result = moderate_message("I hate all people of a certain group!")
        
        assert result == "hate"
    
    @pytest.mark.unit
    @patch("chatbot.services.moderation.model_dump")
    @patch("chatbot.services.moderation.OpenAI")
    @override_settings(MODERATION_VALUES_FOR_BLOCKED={"harassment": 0.7, "hate": 0.7, "sexual": 0.7, "self_harm": 0.7, "violence": 0.7})
    def test_moderation_blocked_message_violence(self, mock_openai_class, mock_model_dump):
        """Test that messages with high violence scores are blocked."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock moderation response for blocked content
        mock_response = Mock()
        mock_response.results = [Mock()]
        
        # Mock category_scores
        mock_category_scores = Mock()
        mock_response.results[0].category_scores = mock_category_scores
        
        # Mock model_dump to return a proper dictionary
        mock_model_dump.return_value = {
            "harassment": 0.1,
            "hate": 0.2,
            "violence": 0.85,
        }
        
        mock_client.moderations.create.return_value = mock_response
        
        result = moderate_message("I want to hurt someone!")
        
        assert result == "violence"
    
    @pytest.mark.unit
    @patch("chatbot.services.moderation.model_dump")
    @patch("chatbot.services.moderation.OpenAI")
    @override_settings(MODERATION_VALUES_FOR_BLOCKED={"harassment": 0.7, "hate": 0.7, "sexual": 0.7, "self_harm": 0.7, "violence": 0.7})
    def test_moderation_multiple_high_scores(self, mock_openai_class, mock_model_dump):
        """Test that the first high score category is returned."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock moderation response for blocked content
        mock_response = Mock()
        mock_response.results = [Mock()]
        
        # Mock category_scores
        mock_category_scores = Mock()
        mock_response.results[0].category_scores = mock_category_scores
        
        # Mock model_dump to return a proper dictionary
        mock_model_dump.return_value = {
            "harassment": 0.9,
            "hate": 0.95,
            "sexual": 0.8,
        }
        
        mock_client.moderations.create.return_value = mock_response
        
        result = moderate_message("Very offensive message!")
        
        # Should return first category that exceeds threshold
        assert result == "harassment"
    
    @pytest.mark.unit
    @patch("chatbot.services.moderation.model_dump")
    @patch("chatbot.services.moderation.OpenAI")
    @override_settings(MODERATION_VALUES_FOR_BLOCKED={"harassment": 0.7, "hate": 0.7, "sexual": 0.7, "self_harm": 0.7, "violence": 0.7})
    def test_moderation_edge_case_threshold(self, mock_openai_class, mock_model_dump):
        """Test moderation at the threshold boundary."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock moderation response
        mock_response = Mock()
        mock_response.results = [Mock()]
        
        # Mock category_scores
        mock_category_scores = Mock()
        mock_response.results[0].category_scores = mock_category_scores
        
        # Mock model_dump to return a proper dictionary
        mock_model_dump.return_value = {
            "harassment": 1.0,
            "hate": 0.5,
        }
        
        mock_client.moderations.create.return_value = mock_response
        
        result = moderate_message("Message at threshold")
        
        # Should be blocked at exactly 1.0
        assert result == "harassment"
    
    @pytest.mark.unit
    @patch("chatbot.services.moderation.model_dump")
    @patch("chatbot.services.moderation.OpenAI")
    @override_settings(MODERATION_VALUES_FOR_BLOCKED={"harassment": 0.7, "hate": 0.7, "sexual": 0.7, "self_harm": 0.7, "violence": 0.7})
    def test_moderation_none_scores(self, mock_openai_class, mock_model_dump):
        """Test handling of None scores from API."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock moderation response with None scores
        mock_response = Mock()
        mock_response.results = [Mock()]
        
        # Mock category_scores
        mock_category_scores = Mock()
        mock_response.results[0].category_scores = mock_category_scores
        
        # Mock model_dump to return a proper dictionary
        mock_model_dump.return_value = {
            "harassment": None,
            "hate": 0.8,
            "sexual": None,
        }
        
        mock_client.moderations.create.return_value = mock_response
        
        result = moderate_message("Message with None scores")
        
        # Should still work with None values
        assert result == "hate"
    
    @pytest.mark.unit
    @patch("chatbot.services.moderation.model_dump")
    @patch("chatbot.services.moderation.OpenAI")
    @override_settings(MODERATION_VALUES_FOR_BLOCKED={"harassment": 0.7, "hate": 0.7, "sexual": 0.7, "self_harm": 0.7, "violence": 0.7})
    def test_moderation_empty_message(self, mock_openai_class, mock_model_dump):
        """Test moderation of empty message."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock moderation response
        mock_response = Mock()
        mock_response.results = [Mock()]
        
        # Mock category_scores
        mock_category_scores = Mock()
        mock_response.results[0].category_scores = mock_category_scores
        
        # Mock model_dump to return a proper dictionary
        mock_model_dump.return_value = {
            "harassment": 0.1,
            "hate": 0.1,
        }
        
        mock_client.moderations.create.return_value = mock_response
        
        result = moderate_message("")
        
        assert result == ""
        mock_client.moderations.create.assert_called_once_with(
            input="",
            model="omni-moderation-latest",
        )
    
    @pytest.mark.unit
    @patch("chatbot.services.moderation.model_dump")
    @patch("chatbot.services.moderation.OpenAI")
    @override_settings(MODERATION_VALUES_FOR_BLOCKED={"harassment": 0.7, "hate": 0.7, "sexual": 0.7, "self_harm": 0.7, "violence": 0.7})
    def test_moderation_long_message(self, mock_openai_class, mock_model_dump):
        """Test moderation of very long message."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock moderation response
        mock_response = Mock()
        mock_response.results = [Mock()]
        
        # Mock category_scores
        mock_category_scores = Mock()
        mock_response.results[0].category_scores = mock_category_scores
        
        # Mock model_dump to return a proper dictionary
        mock_model_dump.return_value = {
            "harassment": 0.1,
            "hate": 0.1,
        }
        
        mock_client.moderations.create.return_value = mock_response
        
        long_message = "This is a very long message. " * 100
        
        result = moderate_message(long_message)
        
        assert result == ""
        mock_client.moderations.create.assert_called_once_with(
            input=long_message,
            model="omni-moderation-latest",
        )
    
    @pytest.mark.unit
    @patch("chatbot.services.moderation.model_dump")
    @patch("chatbot.services.moderation.OpenAI")
    @override_settings(MODERATION_VALUES_FOR_BLOCKED={"harassment": 0.7, "hate": 0.7, "sexual": 0.7, "self_harm": 0.7, "violence": 0.7})
    def test_moderation_special_characters(self, mock_openai_class, mock_model_dump):
        """Test moderation of messages with special characters."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock moderation response
        mock_response = Mock()
        mock_response.results = [Mock()]
        
        # Mock category_scores
        mock_category_scores = Mock()
        mock_response.results[0].category_scores = mock_category_scores
        
        # Mock model_dump to return a proper dictionary
        mock_model_dump.return_value = {
            "harassment": 0.1,
            "hate": 0.1,
        }
        
        mock_client.moderations.create.return_value = mock_response
        
        special_message = "Hello! How are you? 😊 #testing @user"
        
        result = moderate_message(special_message)
        
        assert result == ""
        mock_client.moderations.create.assert_called_once_with(
            input=special_message,
            model="omni-moderation-latest",
        )

from unittest.mock import Mock, patch

import pytest
import time
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.test import TransactionTestCase
from django.utils import timezone
from datetime import timedelta

from chatbot.models import Bot, Conversation, Persona, Utterance


class TestRunChat(TransactionTestCase):
    """Test cases for runchat service functions."""

    def setUp(self):
        """Set up test data."""
        # Create test bot
        self.bot = Bot.objects.create(
            name="test-bot",
            prompt="You are a helpful assistant.",
            model_type="OpenAI",
            model_id="gpt-4"
        )
        
        # Create test persona
        self.persona = Persona.objects.create(
            name="FriendlyBot",
            instructions="Always be cheerful and use emojis 😊"
        )
        
        # Create test conversation
        self.conversation = Conversation.objects.create(
            conversation_id="test-conv-123",
            selected_persona=self.persona
        )
        
        # Clear cache before each test
        cache.clear()

    async def verify_utterance_saved(self, speaker_id, expected_text, **kwargs):
        """Helper to verify an utterance was saved to database."""
        utterance = await sync_to_async(Utterance.objects.get)(
            conversation=self.conversation, 
            speaker_id=speaker_id
        )
        assert utterance.text == expected_text
        for key, value in kwargs.items():
            assert getattr(utterance, key) == value

    def create_test_bot(self, name="test-bot", prompt="You are a helpful assistant.", **kwargs):
        """Helper to create a test bot."""
        return Bot.objects.create(
            name=name,
            prompt=prompt,
            model_type="OpenAI",
            model_id="gpt-4",
            **kwargs
        )

    @pytest.mark.unit
    def test_generate_system_prompt_bot_only(self):
        """Test system prompt generation with only bot prompt."""
        from chatbot.services.runchat import generate_system_prompt
        
        prompt = generate_system_prompt(self.bot)
        assert prompt == "You are a helpful assistant."

    @pytest.mark.unit
    def test_generate_system_prompt_with_persona(self):
        """Test system prompt generation with bot prompt and persona."""
        from chatbot.services.runchat import generate_system_prompt
        
        prompt = generate_system_prompt(self.bot, self.persona)
        
        expected = (
            "You are a helpful assistant.\n\n"
            "Additional personality instructions:\n"
            "Persona 'FriendlyBot': Always be cheerful and use emojis 😊"
        )
        assert prompt == expected

    @pytest.mark.unit
    def test_generate_system_prompt_empty_bot_prompt(self):
        """Test system prompt generation with empty bot prompt."""
        from chatbot.services.runchat import generate_system_prompt
        
        bot = self.create_test_bot(name="empty-bot", prompt="")
        prompt = generate_system_prompt(bot, self.persona)
        
        expected = (
            "Additional personality instructions:\n"
            "Persona 'FriendlyBot': Always be cheerful and use emojis 😊"
        )
        assert prompt == expected

    @pytest.mark.unit
    def test_generate_system_prompt_no_persona(self):
        """Test system prompt generation with no persona."""
        from chatbot.services.runchat import generate_system_prompt
        
        prompt = generate_system_prompt(self.bot, None)
        assert prompt == "You are a helpful assistant."

    @pytest.mark.unit
    def test_generate_system_prompt_error_handling(self):
        """Test system prompt generation error handling."""
        from chatbot.services.runchat import generate_system_prompt
        
        # Create a bot with invalid prompt that would cause an error
        bot = Mock()
        bot.prompt = None  # This will cause an error when trying to strip
        
        # Should handle the error gracefully and return empty string
        prompt = generate_system_prompt(bot)
        assert prompt == ""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_save_chat_to_db(self):
        """Test saving chat data to database."""
        from chatbot.services.runchat import save_chat_to_db
        
        await save_chat_to_db(
            conversation_id="test-conv-123",
            speaker_id="user",
            text="Hello, how are you?",
            bot_name=None,
            participant_id="user-123",
        )
        
        await self.verify_utterance_saved(
            speaker_id="user",
            expected_text="Hello, how are you?",
            participant_id="user-123",
            bot_name=None
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_save_chat_to_db_conversation_not_found(self):
        """Test saving chat data when conversation doesn't exist."""
        from chatbot.services.runchat import save_chat_to_db
        
        # Should not raise an exception, just log a warning
        await save_chat_to_db(
            conversation_id="non-existent-conv",
            speaker_id="user",
            text="Hello",
            bot_name=None,
            participant_id="user-123",
        )
        
        # Verify no utterance was created
        count = await sync_to_async(Utterance.objects.count)()
        assert count == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_chat_round_success(self):
        """Test successful chat round execution."""
        from chatbot.services.runchat import run_chat_round
        
        with patch("chatbot.services.runchat.moderate_message") as mock_moderation, \
             patch("server.engine.get_or_create_engine") as mock_engine, \
             patch("chatbot.services.runchat.Kani") as mock_kani:
            
            # Setup mocks
            mock_moderation.return_value = ""
            mock_engine.return_value = Mock()
            
            async def mock_full_round(*args, **kwargs):
                yield Mock(text="Hello! How can I help you?")
            
            mock_kani_instance = Mock()
            mock_kani_instance.full_round = mock_full_round
            mock_kani.return_value = mock_kani_instance
            
            # Run test
            result = await run_chat_round(
                bot_name="test-bot",
                conversation_id="test-conv-123",
                participant_id="user-123",
                message="Hello",
            )
            
            # Verify results
            assert result == "Hello! How can I help you?"
            await self.verify_utterance_saved("user", "Hello", participant_id="user-123")
            await self.verify_utterance_saved("assistant", "Hello! How can I help you?", bot_name="test-bot")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_chat_round_with_cache(self):
        """Test chat round with existing conversation history in cache."""
        from chatbot.services.runchat import run_chat_round
        
        # Pre-populate cache with conversation history
        cache_key = "conversation_cache_test-conv-123"
        cache.set(cache_key, [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"}
        ], timeout=3600)
        
        with patch("chatbot.services.runchat.moderate_message") as mock_moderation, \
             patch("server.engine.get_or_create_engine") as mock_engine, \
             patch("chatbot.services.runchat.Kani") as mock_kani:
            
            mock_moderation.return_value = ""
            mock_engine.return_value = Mock()
            
            async def mock_full_round(*args, **kwargs):
                yield Mock(text="New response")
            
            mock_kani_instance = Mock()
            mock_kani_instance.full_round = mock_full_round
            mock_kani.return_value = mock_kani_instance
            
            result = await run_chat_round(
                bot_name="test-bot",
                conversation_id="test-conv-123",
                participant_id="user-123",
                message="New message",
            )
            
            assert result == "New response"
            # Verify cache was updated with new message
            updated_cache = cache.get(cache_key)
            assert len(updated_cache) == 4  # Previous 2 + new 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_chat_round_load_history_from_db(self):
        """Test chat round loading conversation history from database."""
        from chatbot.services.runchat import run_chat_round
        
        # Create some previous utterances
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Previous user message",
            participant_id="user-123"
        )
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="assistant",
            text="Previous bot response",
            bot_name="test-bot"
        )
        
        with patch("chatbot.services.runchat.moderate_message") as mock_moderation, \
             patch("server.engine.get_or_create_engine") as mock_engine, \
             patch("chatbot.services.runchat.Kani") as mock_kani:
            
            mock_moderation.return_value = ""
            mock_engine.return_value = Mock()
            
            async def mock_full_round(*args, **kwargs):
                yield Mock(text="New response")
            
            mock_kani_instance = Mock()
            mock_kani_instance.full_round = mock_full_round
            mock_kani.return_value = mock_kani_instance
            
            result = await run_chat_round(
                bot_name="test-bot",
                conversation_id="test-conv-123",
                participant_id="user-123",
                message="New message",
            )
            
            assert result == "New response"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_chat_round_moderation_blocked(self):
        """Test chat round when message is blocked by moderation."""
        from chatbot.services.runchat import run_chat_round
        
        with patch("chatbot.services.runchat.moderate_message") as mock_moderation:
            mock_moderation.return_value = "Content blocked for harassment"
            
            result = await run_chat_round(
                bot_name="test-bot",
                conversation_id="test-conv-123",
                participant_id="user-123",
                message="Hello",
            )
            
            # Verify moderation response
            assert "blocked by moderation" in result
            assert "harassment" in result
            
            # Verify messages saved
            await self.verify_utterance_saved("user", "Hello")
            await self.verify_utterance_saved("assistant", result)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_chat_flow(self):
        """Test complete chat flow with minimal mocking."""
        from chatbot.services.runchat import run_chat_round
        
        # Only mock external APIs, use real database and cache
        with patch("chatbot.services.runchat.moderate_message") as mock_moderation, \
             patch("server.engine.get_or_create_engine") as mock_engine, \
             patch("chatbot.services.runchat.Kani") as mock_kani:
            
            mock_moderation.return_value = ""
            mock_engine.return_value = Mock()
            
            async def mock_full_round(*args, **kwargs):
                yield Mock(text="I'm here to help! What can I assist you with today?")
            
            mock_kani_instance = Mock()
            mock_kani_instance.full_round = mock_full_round
            mock_kani.return_value = mock_kani_instance
            
            # Test the actual user experience
            result = await run_chat_round(
                bot_name="test-bot",
                conversation_id="test-conv-123",
                participant_id="user-123",
                message="Hi, I need help with something",
            )
            
            # Verify complete flow worked
            assert "I'm here to help" in result
            assert len(result) > 0
            
            # Verify database state
            await self.verify_utterance_saved("user", "Hi, I need help with something", participant_id="user-123")
            await self.verify_utterance_saved("assistant", result, bot_name="test-bot")
            
            # Verify cache was populated
            cache_key = "conversation_cache_test-conv-123"
            cached_history = cache.get(cache_key)
            assert cached_history is not None
            assert len(cached_history) == 2

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_chat_response_time(self):
        """Ensure chat responses are reasonably fast."""
        from chatbot.services.runchat import run_chat_round
        
        with patch("chatbot.services.runchat.moderate_message") as mock_moderation, \
             patch("server.engine.get_or_create_engine") as mock_engine, \
             patch("chatbot.services.runchat.Kani") as mock_kani:
            
            mock_moderation.return_value = ""
            mock_engine.return_value = Mock()
            
            async def mock_full_round(*args, **kwargs):
                yield Mock(text="Quick response!")
            
            mock_kani_instance = Mock()
            mock_kani_instance.full_round = mock_full_round
            mock_kani.return_value = mock_kani_instance
            
            start_time = time.time()
            result = await run_chat_round(
                bot_name="test-bot",
                conversation_id="test-conv-123",
                participant_id="user-123",
                message="Hello",
            )
            response_time = time.time() - start_time
            
            assert result == "Quick response!"
            assert response_time < 2.0  # Should respond within 2 seconds
            print(f"Response time: {response_time:.3f} seconds")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_message_handling(self):
        """Test handling of empty user messages."""
        from chatbot.services.runchat import run_chat_round
        
        with patch("chatbot.services.runchat.moderate_message") as mock_moderation, \
             patch("server.engine.get_or_create_engine") as mock_engine, \
             patch("chatbot.services.runchat.Kani") as mock_kani:
            
            mock_moderation.return_value = ""
            mock_engine.return_value = Mock()
            
            async def mock_full_round(*args, **kwargs):
                yield Mock(text="I noticed you sent an empty message. How can I help you?")
            
            mock_kani_instance = Mock()
            mock_kani_instance.full_round = mock_full_round
            mock_kani.return_value = mock_kani_instance
            
            # Test with empty message
            result = await run_chat_round(
                bot_name="test-bot",
                conversation_id="test-conv-123",
                participant_id="user-123",
                message="",  # Empty message
            )
            
            # Should handle gracefully, not crash
            assert len(result) > 0
            assert "empty message" in result.lower() or "help" in result.lower()
            
            # Verify empty message was still saved to database
            await self.verify_utterance_saved("user", "", participant_id="user-123")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_last_user_message_time(self):
        """Test getting last user message time."""
        from chatbot.services.runchat import get_last_user_message_time
        
        # Create a user message
        user_utterance = await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Test message",
            participant_id="user-123"
        )
        
        last_time = await get_last_user_message_time("test-conv-123")
        assert last_time == user_utterance.created_time

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_last_user_message_time_no_messages(self):
        """Test getting last user message time when no messages exist."""
        from chatbot.services.runchat import get_last_user_message_time
        
        last_time = await get_last_user_message_time("test-conv-123")
        assert last_time is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_is_user_idle_true(self):
        """Test user idle detection when user is idle."""
        from chatbot.services.runchat import is_user_idle
        
        # Create a message from 10 minutes ago
        old_time = timezone.now() - timedelta(minutes=10)
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Old message",
            participant_id="user-123",
            created_time=old_time
        )
        
        is_idle = await is_user_idle("test-conv-123", 5)  # 5 minute idle threshold
        assert is_idle is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_is_user_idle_false(self):
        """Test user idle detection when user is not idle."""
        from chatbot.services.runchat import is_user_idle
        
        # Create a message from 2 minutes ago
        recent_time = timezone.now() - timedelta(minutes=2)
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Recent message",
            participant_id="user-123",
            created_time=recent_time
        )
        
        is_idle = await is_user_idle("test-conv-123", 5)  # 5 minute idle threshold
        assert is_idle is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_is_user_idle_no_messages(self):
        """Test user idle detection when no messages exist."""
        from chatbot.services.runchat import is_user_idle
        
        is_idle = await is_user_idle("test-conv-123", 5)
        assert is_idle is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_followup_message_success(self):
        """Test successful follow-up message generation."""
        from chatbot.services.runchat import generate_followup_message
        
        # Configure bot for follow-up
        bot = await sync_to_async(Bot.objects.get)(name="test-bot")
        bot.follow_up_on_idle = True
        bot.follow_up_instruction_prompt = "Ask the user how they're doing"
        bot.idle_time_minutes = 5
        await sync_to_async(bot.save)()
        
        # Create an old user message to make them idle
        old_time = timezone.now() - timedelta(minutes=10)
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Old message",
            participant_id="user-123",
            created_time=old_time
        )
        
        with patch("chatbot.services.runchat.run_chat_round") as mock_run_chat:
            mock_run_chat.return_value = "How are you doing today?"
            
            response, error = await generate_followup_message(
                bot_name="test-bot",
                conversation_id="test-conv-123",
                participant_id="user-123"
            )
            
            assert response == "How are you doing today?"
            assert error is None
            mock_run_chat.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_followup_message_not_enabled(self):
        """Test follow-up message when not enabled."""
        from chatbot.services.runchat import generate_followup_message
        
        # Configure bot without follow-up
        bot = await sync_to_async(Bot.objects.get)(name="test-bot")
        bot.follow_up_on_idle = False
        await sync_to_async(bot.save)()
        
        response, error = await generate_followup_message(
            bot_name="test-bot",
            conversation_id="test-conv-123",
            participant_id="user-123"
        )
        
        assert response is None
        assert error == "Follow-up not enabled for this bot"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_followup_message_no_prompt(self):
        """Test follow-up message when no instruction prompt configured."""
        from chatbot.services.runchat import generate_followup_message
        
        # Configure bot with follow-up but no prompt
        bot = await sync_to_async(Bot.objects.get)(name="test-bot")
        bot.follow_up_on_idle = True
        bot.follow_up_instruction_prompt = ""
        await sync_to_async(bot.save)()
        
        response, error = await generate_followup_message(
            bot_name="test-bot",
            conversation_id="test-conv-123",
            participant_id="user-123"
        )
        
        assert response is None
        assert error == "No follow-up instruction prompt configured"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_followup_message_user_not_idle(self):
        """Test follow-up message when user is not idle."""
        from chatbot.services.runchat import generate_followup_message
        
        # Configure bot for follow-up
        bot = await sync_to_async(Bot.objects.get)(name="test-bot")
        bot.follow_up_on_idle = True
        bot.follow_up_instruction_prompt = "Ask the user how they're doing"
        bot.idle_time_minutes = 5
        await sync_to_async(bot.save)()
        
        # Create a recent user message
        recent_time = timezone.now() - timedelta(minutes=2)
        await sync_to_async(Utterance.objects.create)(
            conversation=self.conversation,
            speaker_id="user",
            text="Recent message",
            participant_id="user-123",
            created_time=recent_time
        )
        
        response, error = await generate_followup_message(
            bot_name="test-bot",
            conversation_id="test-conv-123",
            participant_id="user-123"
        )
        
        assert response is None
        assert error == "User is not idle"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_followup_message_bot_not_found(self):
        """Test follow-up message when bot doesn't exist."""
        from chatbot.services.runchat import generate_followup_message
        
        response, error = await generate_followup_message(
            bot_name="non-existent-bot",
            conversation_id="test-conv-123",
            participant_id="user-123"
        )
        
        assert response is None
        assert error == "Bot 'non-existent-bot' not found"

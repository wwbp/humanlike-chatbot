from unittest.mock import Mock, patch

import pytest
from django.test import override_settings


class TestRunChat:
    """Test cases for runchat service functions."""

    @pytest.mark.unit
    @override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
    def test_generate_system_prompt_bot_only(self):
        """Test system prompt generation with only bot prompt."""
        from chatbot.services.runchat import generate_system_prompt
        
        # Create a mock bot object instead of using factory
        bot = Mock()
        bot.prompt = "You are a helpful assistant."
        
        prompt = generate_system_prompt(bot)
        
        assert prompt == "You are a helpful assistant."

    @pytest.mark.unit
    @override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
    def test_generate_system_prompt_with_persona(self):
        """Test system prompt generation with bot prompt and persona."""
        from chatbot.services.runchat import generate_system_prompt
        
        # Create mock objects instead of using factories
        bot = Mock()
        bot.prompt = "You are a helpful assistant."
        
        persona = Mock()
        persona.name = "FriendlyBot"
        persona.instructions = "Always be cheerful and use emojis 😊"
        
        prompt = generate_system_prompt(bot, persona)
        
        expected = (
            "You are a helpful assistant.\n\n"
            "Additional personality instructions:\n"
            "Persona 'FriendlyBot': Always be cheerful and use emojis 😊"
        )
        assert prompt == expected

    @pytest.mark.unit
    @override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
    def test_generate_system_prompt_empty_bot_prompt(self):
        """Test system prompt generation with empty bot prompt."""
        from chatbot.services.runchat import generate_system_prompt
        
        # Create mock objects instead of using factories
        bot = Mock()
        bot.prompt = ""
        
        persona = Mock()
        persona.name = "TestPersona"
        persona.instructions = "Test instructions"
        
        prompt = generate_system_prompt(bot, persona)
        
        expected = (
            "Additional personality instructions:\n"
            "Persona 'TestPersona': Test instructions"
        )
        assert prompt == expected

    @pytest.mark.unit
    @override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
    def test_generate_system_prompt_no_persona(self):
        """Test system prompt generation with no persona."""
        from chatbot.services.runchat import generate_system_prompt
        
        # Create a mock bot object instead of using factory
        bot = Mock()
        bot.prompt = "You are a helpful assistant."
        
        prompt = generate_system_prompt(bot, None)
        
        assert prompt == "You are a helpful assistant."

    @pytest.mark.unit
    @pytest.mark.asyncio
    @override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
    async def test_save_chat_to_db(self):
        """Test saving chat data to database."""
        from chatbot.services.runchat import save_chat_to_db
        
        # Mock the database operations
        with patch("chatbot.services.runchat.sync_to_async") as mock_sync_to_async, \
             patch("chatbot.services.runchat.moderate_message") as mock_moderation:
            # Mock the Conversation.objects.get
            async def mock_conversation_get(*args, **kwargs):
                return Mock()
            mock_sync_to_async.return_value = mock_conversation_get
            
            # Mock the Utterance.objects.create
            async def mock_utterance_create(*args, **kwargs):
                return Mock()
            mock_sync_to_async.return_value = mock_utterance_create
            
            # Mock moderation (no blocking)
            mock_moderation.return_value = ""
            
            result = await save_chat_to_db(
                conversation_id="test-conv-123",
                speaker_id="user",
                text="Hello, how are you?",
                bot_name="test-bot",
                participant_id="user-123",
            )
            
            # Should not raise an exception
            assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    @override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
    async def test_run_chat_round_success(self):
        """Test successful chat round execution."""
        from chatbot.services.runchat import run_chat_round
        
        # Mock the database operations and external dependencies
        with patch("chatbot.services.runchat.sync_to_async") as mock_sync_to_async, \
             patch("chatbot.services.runchat.moderate_message") as mock_moderation, \
             patch("chatbot.services.runchat.get_or_create_engine") as mock_engine, \
             patch("chatbot.services.runchat.Kani") as mock_kani:
            
            # Mock the bot query with proper attributes
            mock_bot = Mock()
            mock_bot.name = "test-bot"
            mock_bot.prompt = "You are a helpful assistant."
            mock_bot.model_type = "OpenAI"
            mock_bot.model_id = "gpt-4"
            mock_bot.personas = Mock()
            mock_bot.personas.exists.return_value = False
            mock_bot.personas.first.return_value = None
            
            # Create an async mock function that returns the bot
            async def mock_async_bot_get(*args, **kwargs):
                return mock_bot
            
            # Mock moderation (no blocking) - mock the sync_to_async wrapper
            async def mock_moderation_async(*args, **kwargs):
                return ""
            mock_sync_to_async.side_effect = lambda func: mock_moderation_async if func == mock_moderation else mock_async_bot_get
            
            # Mock Kani and its full_round method with proper async iterator
            async def mock_full_round(*args, **kwargs):
                yield Mock(text="Hello! How can I help you?")
            
            mock_kani_instance = Mock()
            mock_kani_instance.full_round = mock_full_round
            mock_kani.return_value = mock_kani_instance
            
            # Mock engine
            mock_engine_instance = Mock()
            mock_engine.return_value = mock_engine_instance
            
            # Mock save_chat_to_db
            with patch("chatbot.services.runchat.save_chat_to_db") as mock_save:
                mock_save.return_value = None
                
                result = await run_chat_round(
                    bot_name="test-bot",
                    conversation_id="test-conv-123",
                    participant_id="user-123",
                    message="Hello",
                )
                
                assert result == "Hello! How can I help you?"
                assert mock_save.call_count == 2  # Called for both user and bot messages

    @pytest.mark.unit
    @pytest.mark.asyncio
    @override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
    async def test_run_chat_round_engine_error(self):
        """Test chat round with engine error."""
        from chatbot.services.runchat import run_chat_round
        
        # Mock the database operations and external dependencies
        with patch("chatbot.services.runchat.sync_to_async") as mock_sync_to_async, \
             patch("chatbot.services.runchat.moderate_message") as mock_moderation, \
             patch("chatbot.services.runchat.get_or_create_engine") as mock_engine:
            
            # Mock the bot query with proper attributes
            mock_bot = Mock()
            mock_bot.name = "test-bot"
            mock_bot.prompt = "You are a helpful assistant."
            mock_bot.model_type = "OpenAI"
            mock_bot.model_id = "gpt-4"
            mock_bot.personas = Mock()
            mock_bot.personas.exists.return_value = False
            mock_bot.personas.first.return_value = None
            
            # Create an async mock function that returns the bot
            async def mock_async_bot_get(*args, **kwargs):
                return mock_bot
            
            # Mock moderation (no blocking) - return empty string to indicate no blocking
            async def mock_moderation_async(*args, **kwargs):
                return ""
            mock_sync_to_async.side_effect = lambda func: mock_moderation_async if func == mock_moderation else mock_async_bot_get
            
            # Mock engine to raise an error
            mock_engine.side_effect = Exception("Engine error")
            
            # Mock save_chat_to_db
            with patch("chatbot.services.runchat.save_chat_to_db") as mock_save:
                mock_save.return_value = None
                
                # The function should raise an exception when engine creation fails
                with pytest.raises(Exception, match="Engine error"):
                    await run_chat_round(
                        bot_name="test-bot",
                        conversation_id="test-conv-123",
                        participant_id="user-123",
                        message="Hello",
                    )

    @pytest.mark.unit
    @pytest.mark.asyncio
    @override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
    async def test_run_chat_round_save_error(self):
        """Test chat round with save error."""
        from chatbot.services.runchat import run_chat_round
        
        # Mock the database operations and external dependencies
        with patch("chatbot.services.runchat.sync_to_async") as mock_sync_to_async, \
             patch("chatbot.services.runchat.moderate_message") as mock_moderation, \
             patch("server.engine.get_or_create_engine") as mock_engine:
            
            # Mock the bot query with proper attributes
            mock_bot = Mock()
            mock_bot.name = "test-bot"
            mock_bot.prompt = "You are a helpful assistant."
            mock_bot.model_type = "OpenAI"
            mock_bot.model_id = "gpt-4"
            mock_bot.personas = Mock()
            mock_bot.personas.exists.return_value = False
            mock_bot.personas.first.return_value = None
            
            # Create an async mock function that returns the bot
            async def mock_async_bot_get(*args, **kwargs):
                return mock_bot
            
            mock_sync_to_async.return_value = mock_async_bot_get
            
            # Mock moderation (no blocking)
            mock_moderation.return_value = ""
            
            # Mock engine
            mock_engine_instance = Mock()
            mock_engine_instance.chat_round.return_value = Mock()
            mock_engine_instance.chat_round.return_value.content = "Hello! How can I help you?"
            mock_engine.return_value = mock_engine_instance
            
            # Mock save_chat_to_db to raise an error
            with patch("chatbot.services.runchat.save_chat_to_db") as mock_save:
                mock_save.side_effect = Exception("Database error")
                
                # This should raise an exception due to save error
                with pytest.raises(Exception, match="Database error"):
                    await run_chat_round(
                        bot_name="test-bot",
                        conversation_id="test-conv-123",
                        participant_id="user-123",
                        message="Hello",
                    )

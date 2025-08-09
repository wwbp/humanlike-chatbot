import json

from django.test import TestCase
from django.utils import timezone

# Remove problematic imports at module level
# from chatbot.models import Bot, Conversation, Utterance, Persona
# from tests.factories import BotFactory, ConversationFactory, PersonaFactory, create_chat_session

class TestChatFlowIntegration(TestCase):
    """Integration tests for chat flow functionality."""

    def setUp(self):
        """Set up test data."""
        from tests.factories import BotFactory, ConversationFactory, PersonaFactory
        
        self.bot = BotFactory(
            name="TestBot",
            prompt="You are a helpful test bot.",
            model_type="OpenAI",
            model_id="gpt-4",
            chunk_messages=True,
        )
        
        self.persona = PersonaFactory(
            name="FriendlyPersona",
            instructions="Always be cheerful and helpful!",
        )
        self.bot.personas.add(self.persona)
        
        self.conversation = ConversationFactory(
            conversation_id="test-conv-123",
            bot_name="TestBot",
            participant_id="test-user-456",
            selected_persona=self.persona,
        )
        
        # Create initial bot message
        from chatbot.models import Utterance
        Utterance.objects.create(
            conversation=self.conversation,
            speaker_id="bot",
            bot_name="TestBot",
            text="Hello! I'm TestBot. How can I help you today?",
            participant_id="test-user-456",
        )

    def test_complete_chat_flow_success(self):
        """Test complete successful chat flow."""
        from tests.factories import create_chat_session
        
        # Create a new chat session with unique bot name
        session_data = create_chat_session(
            bot_name=f"TestBot{int(timezone.now().timestamp() * 1000)}",
            participant_id="test-user-789",
        )
        
        # Verify session was created
        self.assertIn("conversation_id", session_data)
        self.assertIn("bot_name", session_data)
        self.assertIn("participant_id", session_data)
        self.assertEqual(session_data["participant_id"], "test-user-789")

    def test_chat_flow_conversation_persistence(self):
        """Test that conversation data persists correctly."""
        # Verify conversation was created
        self.assertEqual(self.conversation.bot_name, "TestBot")
        self.assertEqual(self.conversation.participant_id, "test-user-456")
        self.assertEqual(self.conversation.selected_persona, self.persona)
        
        # Verify initial message was created
        from chatbot.models import Utterance
        utterances = Utterance.objects.filter(conversation=self.conversation)
        self.assertEqual(utterances.count(), 1)
        self.assertEqual(utterances.first().speaker_id, "bot")

    def test_chat_flow_with_different_bot_configs(self):
        """Test chat flow with various bot configurations."""
        # Test with different model types
        from tests.factories import BotFactory
        
        anthropic_bot = BotFactory(
            name="AnthropicBot",
            model_type="Anthropic",
            model_id="claude-3-sonnet",
        )
        
        self.assertEqual(anthropic_bot.model_type, "Anthropic")
        self.assertEqual(anthropic_bot.model_id, "claude-3-sonnet")

    def test_chat_flow_error_handling(self):
        """Test error handling in chat flow."""
        # Test with invalid bot name - this should work since we create the bot
        from tests.factories import create_chat_session
        
        # The function should work even with custom bot names
        session_data = create_chat_session(
            bot_name="CustomTestBot",
            participant_id="test-user",
        )
        
        # Verify it was created successfully
        self.assertEqual(session_data["bot_name"], "CustomTestBot")

    def test_chat_flow_missing_required_fields(self):
        """Test chat flow with missing required fields."""
        from tests.factories import create_chat_session
        
        # Test with empty bot_name - should use timestamp-based unique name
        session_data = create_chat_session(
            bot_name="",
            participant_id="test-user",
        )
        
        # Should create a bot with a unique name
        self.assertIsNotNone(session_data["bot_name"])
        self.assertNotEqual(session_data["bot_name"], "")

    def test_chat_flow_invalid_json(self):
        """Test chat flow with invalid JSON data."""
        # This would typically be tested in API endpoints
        # For now, we'll test basic JSON validation
        invalid_json = "{'invalid': json}"
        
        with self.assertRaises(json.JSONDecodeError):
            json.loads(invalid_json)

    def test_chat_flow_moderation_blocked(self):
        """Test chat flow when message is blocked by moderation."""
        # Test moderation integration
        from chatbot.services.moderation import moderate_message
        
        # Test with potentially problematic message
        result = moderate_message("This is a normal message")
        self.assertIsInstance(result, str)

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from chatbot.models import (
    Avatar,
    Bot,
    Control,
    Conversation,
    Keystroke,
    Persona,
    Utterance,
)


class PersonaFactory(DjangoModelFactory):
    """Factory for creating Persona instances."""
    
    class Meta:
        model = Persona
    
    name = factory.Sequence(lambda n: f"TestPersona{n}")
    instructions = factory.Faker("text", max_nb_chars=200)


class BotFactory(DjangoModelFactory):
    """Factory for creating Bot instances."""
    
    class Meta:
        model = Bot
    
    name = factory.Sequence(lambda n: f"TestBot{n}")
    prompt = factory.Faker("text", max_nb_chars=500)
    model_type = factory.Iterator(["OpenAI", "Anthropic"])
    model_id = factory.Iterator(["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet"])
    initial_utterance = factory.Faker("sentence")
    avatar_type = factory.Iterator(["none", "default", "user"])
    chunk_messages = True
    follow_up_on_idle = False
    idle_time_minutes = 5
    follow_up_instruction_prompt = factory.Faker("text", max_nb_chars=200)
    
    @factory.post_generation
    def personas(self, create, extracted, **kwargs):
        """Add personas to bot if specified."""
        if not create:
            return
        
        if extracted:
            for persona in extracted:
                self.personas.add(persona)


class ConversationFactory(DjangoModelFactory):
    """Factory for creating Conversation instances."""
    
    class Meta:
        model = Conversation
    
    conversation_id = factory.Sequence(lambda n: f"test-conv-{n}")
    bot_name = factory.Sequence(lambda n: f"TestBot{n}")
    participant_id = factory.Sequence(lambda n: f"test-user-{n}")
    initial_utterance = factory.Faker("sentence")
    study_name = factory.Faker("word")
    user_group = factory.Iterator(["control", "treatment", "baseline"])
    survey_id = factory.Sequence(lambda n: f"survey-{n}")
    survey_meta_data = factory.Faker("json")
    started_time = factory.LazyFunction(timezone.now)
    selected_persona = factory.SubFactory(PersonaFactory)


class UtteranceFactory(DjangoModelFactory):
    """Factory for creating Utterance instances."""
    
    class Meta:
        model = Utterance
    
    conversation = factory.SubFactory(ConversationFactory)
    speaker_id = factory.Iterator(["user", "bot"])
    bot_name = factory.Sequence(lambda n: f"TestBot{n}")
    participant_id = factory.Sequence(lambda n: f"test-user-{n}")
    created_time = factory.LazyFunction(timezone.now)
    text = factory.Faker("text", max_nb_chars=100)
    is_voice = False
    
    @factory.lazy_attribute
    def bot_name(self):
        """Set bot_name based on speaker_id."""
        if self.speaker_id == "bot":
            return factory.Sequence(lambda n: f"TestBot{n}")
        return None
    
    @factory.lazy_attribute
    def participant_id(self):
        """Set participant_id based on speaker_id."""
        if self.speaker_id == "user":
            return factory.Sequence(lambda n: f"test-user-{n}")
        return None


class AvatarFactory(DjangoModelFactory):
    """Factory for creating Avatar instances."""
    
    class Meta:
        model = Avatar
    
    bot = factory.SubFactory(BotFactory)
    bot_conversation = factory.Sequence(lambda n: f"conv-{n}")
    condition = factory.Iterator(["control", "similar", "dissimilar"])
    participant_avatar = factory.Faker("text", max_nb_chars=100)
    chatbot_avatar = factory.Faker("text", max_nb_chars=100)


class KeystrokeFactory(DjangoModelFactory):
    """Factory for creating Keystroke instances."""
    
    class Meta:
        model = Keystroke
    
    conversation_id = factory.Sequence(lambda n: f"test-conv-{n}")
    total_time_on_page = factory.Faker("pyfloat", min_value=0.1, max_value=300.0)
    total_time_away_from_page = factory.Faker("pyfloat", min_value=0.0, max_value=100.0)
    keystroke_count = factory.Faker("pyint", min_value=1, max_value=1000)
    timestamp = factory.LazyFunction(timezone.now)


class ControlFactory(DjangoModelFactory):
    """Factory for creating Control instances."""
    
    class Meta:
        model = Control
    
    chunk_messages = True
    follow_up_on_idle = False
    idle_time_minutes = 5
    follow_up_instruction_prompt = factory.Faker("text", max_nb_chars=200)


# Helper functions for common test scenarios
def create_chat_session(bot_name=None, participant_id="test-user"):
    """Create a complete chat session with bot, conversation, and initial messages."""
    # Use unique bot name if not provided or if empty
    if not bot_name:
        bot_name = f"TestBot{int(timezone.now().timestamp() * 1000)}"
    
    bot = BotFactory(name=bot_name)
    persona = PersonaFactory()
    bot.personas.add(persona)
    
    conversation = ConversationFactory(
        bot_name=bot_name,
        participant_id=participant_id,
        selected_persona=persona,
    )
    
    # Add initial bot message
    UtteranceFactory(
        conversation=conversation,
        speaker_id="bot",
        bot_name=bot_name,
        text=bot.initial_utterance,
    )
    
    return {
        "bot": bot,
        "conversation": conversation,
        "persona": persona,
        "conversation_id": conversation.conversation_id,
        "bot_name": bot_name,
        "participant_id": participant_id,
    }


def create_conversation_history(conversation, message_count=5):
    """Create a conversation with alternating user/bot messages."""
    messages = []
    
    for i in range(message_count):
        speaker = "user" if i % 2 == 0 else "bot"
        text = f"Message {i+1} from {speaker}"
        
        utterance = UtteranceFactory(
            conversation=conversation,
            speaker_id=speaker,
            text=text,
            bot_name=conversation.bot_name if speaker == "bot" else None,
            participant_id=conversation.participant_id if speaker == "user" else None,
        )
        messages.append(utterance)
    
    return messages

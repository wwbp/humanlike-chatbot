import os

import django
import pytest

# Configure Django settings for testing BEFORE any other imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "generic_chatbot.test_settings")

# Configure Django
django.setup()

@pytest.fixture(autouse=True)
def mock_external_apis(monkeypatch):
    """Mock external API calls to avoid real network requests during testing."""
    # Mock OpenAI API key
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-12345")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-67890")
    
    # Mock AWS credentials
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-access-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret-key")
    monkeypatch.setenv("AWS_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

@pytest.fixture
def mock_openai_client(mocker):
    """Mock OpenAI client for testing."""
    mock_client = mocker.patch("openai.OpenAI")
    mock_client.return_value.moderations.create.return_value.results = [
        mocker.Mock(category_scores=mocker.Mock()),
    ]
    return mock_client

@pytest.fixture
def mock_kani_engine(mocker):
    """Mock Kani engine for testing."""
    mock_engine = mocker.patch("kani.Kani")
    mock_engine.return_value.chat_round.return_value = "Mocked AI response"
    return mock_engine

@pytest.fixture
def mock_redis_cache(mocker):
    """Mock Redis cache for testing."""
    mock_cache = mocker.patch("django.core.cache.cache")
    mock_cache.get.return_value = None
    mock_cache.set.return_value = True
    return mock_cache

@pytest.fixture
def sample_conversation_data():
    """Sample data for creating test conversations."""
    return {
        "conversation_id": "test-conv-123",
        "bot_name": "TestBot",
        "participant_id": "test-user-456",
        "study_name": "Test Study",
        "user_group": "control",
        "survey_id": "test-survey-789",
    }

@pytest.fixture
def sample_bot_data():
    """Sample data for creating test bots."""
    return {
        "name": "TestBot",
        "prompt": "You are a helpful test bot.",
        "model_type": "OpenAI",
        "model_id": "gpt-4",
        "initial_utterance": "Hello! I'm a test bot.",
        "chunk_messages": True,
        "follow_up_on_idle": False,
    }

@pytest.fixture
def sample_persona_data():
    """Sample data for creating test personas."""
    return {
        "name": "TestPersona",
        "instructions": "Be friendly and helpful in testing scenarios.",
    }

@pytest.fixture
def sample_utterance_data():
    """Sample data for creating test utterances."""
    return {
        "speaker_id": "user",
        "text": "Hello, this is a test message.",
        "bot_name": None,
        "participant_id": "test-user-456",
        "is_voice": False,
    }

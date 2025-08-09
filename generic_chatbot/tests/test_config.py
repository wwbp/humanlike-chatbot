"""
Simplified test configuration for consolidated testing.

This file provides a clean, focused testing environment that consolidates
all the essential test configuration in one place.
"""

import os

import pytest
from django.conf import settings
from django.test import TestCase

# Test database configuration
TEST_DATABASE_CONFIG = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {
            "NAME": ":memory:",
        },
    },
}

# Test settings override
TEST_SETTINGS = {
    "DATABASES": TEST_DATABASE_CONFIG,
    "CACHES": {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
    },
    "MEDIA_ROOT": "/tmp/test_media/",
    "STATIC_ROOT": "/tmp/test_static/",
    "DEBUG": False,
    "SECRET_KEY": "test-secret-key-for-testing-only",
    "MIDDLEWARE": [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
    ],
    "INSTALLED_APPS": [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "chatbot",
    ],
    "TEMPLATES": [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ],
            },
        },
    ],
    "ROOT_URLCONF": "generic_chatbot.urls",
    "WSGI_APPLICATION": "generic_chatbot.wsgi.application",
    "LANGUAGE_CODE": "en-us",
    "TIME_ZONE": "UTC",
    "USE_I18N": True,
    "USE_TZ": True,
    "STATIC_URL": "/static/",
    "MEDIA_URL": "/media/",
    "DEFAULT_AUTO_FIELD": "django.db.models.BigAutoField",
    "LOGGING": {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "chatbot": {
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    },
}


class BaseTestCase(TestCase):
    """Base test case with common configuration and utilities."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with overridden settings."""
        super().setUpClass()
        
    def setUp(self):
        """Set up each test method."""
        super().setUp()
        
    def tearDown(self):
        """Clean up after each test method."""
        super().tearDown()
        
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests in the class."""
        super().tearDownClass()


# Pytest configuration
def pytest_configure():
    """Configure pytest with Django settings."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "generic_chatbot.test_settings")
    
    # Override settings for testing
    for key, value in TEST_SETTINGS.items():
        setattr(settings, key, value)


# Test utilities
class TestUtils:
    """Utility functions for testing."""
    
    @staticmethod
    def create_test_bot_data():
        """Create standard test bot data."""
        return {
            "name": "TestBot",
            "prompt": "You are a helpful test bot.",
            "model_type": "OpenAI",
            "model_id": "gpt-4",
            "chunk_messages": True,
            "follow_up_on_idle": True,
            "idle_time_minutes": 5,
            "follow_up_instruction_prompt": "Check in with the user.",
        }
    
    @staticmethod
    def create_test_conversation_data():
        """Create standard test conversation data."""
        return {
            "conversation_id": "test-conv-123",
            "bot_name": "TestBot",
            "participant_id": "test-user-456",
        }
    
    @staticmethod
    def create_test_utterance_data():
        """Create standard test utterance data."""
        return {
            "speaker_id": "user",
            "text": "Hello, this is a test message.",
            "participant_id": "test-user-456",
        }


# Fixture definitions for pytest
@pytest.fixture
def test_bot_data():
    """Fixture providing test bot data."""
    return TestUtils.create_test_bot_data()


@pytest.fixture
def test_conversation_data():
    """Fixture providing test conversation data."""
    return TestUtils.create_test_conversation_data()


@pytest.fixture
def test_utterance_data():
    """Fixture providing test utterance data."""
    return TestUtils.create_test_utterance_data()


# Test markers
pytest_plugins = ["pytest_django"]

# Mark tests that require database
pytestmark = pytest.mark.django_db

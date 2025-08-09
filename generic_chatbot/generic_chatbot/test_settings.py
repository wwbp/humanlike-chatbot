import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Add the project root to Python path
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "generic_chatbot.settings")

# Configure Django settings directly instead of importing
# These will be overridden by environment variables below
SECRET_KEY = "test-secret-key-for-testing-only"
DEBUG = True
ALLOWED_HOSTS = ["*"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_redis",
    "chatbot",
    "rest_framework",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "generic_chatbot.urls"
WSGI_APPLICATION = "generic_chatbot.wsgi.application"

# Database - use test database to avoid conflicts with main app
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DATABASE_ENGINE", "django.db.backends.mysql"),
        "NAME": os.getenv("TEST_DATABASE_NAME", "test_chatbot_db"),
        "USER": os.getenv("DATABASE_USER", "user"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "test123"),
        "HOST": os.getenv("DATABASE_HOST", "db"),
        "PORT": os.getenv("DATABASE_PORT", "3306"),
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    },
}

# Cache settings for testing
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    },
}

# Use environment variables for API keys, fallback to test keys if not set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "test-key-12345")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "test-key-67890")

# Disable logging during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "True").lower() == "true"

# Additional environment variables for testing
SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-for-testing-only")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0,backend").split(",")

# AWS settings for testing
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "test-bucket")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test-key")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test-secret")

# Moderation settings for testing
MODERATION_VALUES_FOR_BLOCKED = {
    "harassment": 0.5,
    "harassment/threatening": 0.1,
    "hate": 0.5,
    "hate/threatening": 0.1,
    "self-harm": 0.2,
    "self-harm/instructions": 0.5,
    "self-harm/intent": 0.7,
    "sexual": 0.5,
    "sexual/minors": 0.2,
    "violence": 0.7,
    "violence/graphic": 0.8,
}

# Backend environment
BACKEND_ENVIRONMENT = os.getenv("BACKEND_ENVIRONMENT", "test")

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR, "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

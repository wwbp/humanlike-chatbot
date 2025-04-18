from pathlib import Path
import os
from dotenv import load_dotenv
import requests

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
ROOT_DIR = BASE_DIR.parent
dotenv_path = os.path.join(ROOT_DIR, '.env')
load_dotenv(dotenv_path)


STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', '!g8ik7!xk!9xyldg+r75$^@tdt+d')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ["bot.wwbp.org", "localhost",
                 "127.0.0.1", "backend", "0.0.0.0"]

# REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')
REDIS_URL = os.getenv(
    'REDIS_URL', 'rediss://humanlikebotcache-5rqgxm.serverless.use1.cache.amazonaws.com:6379')

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# Append Elastic Beanstalk Load Balancer Health Check requests since the source host IP address keeps changing
try:
    token = requests.put('http://169.254.169.254/latest/api/token',
                         headers={'X-aws-ec2-metadata-token-ttl-seconds': '60'}).text
    internal_ip = requests.get('http://169.254.169.254/latest/meta-data/local-ipv4',
                               headers={'X-aws-ec2-metadata-token': token}).text
except requests.exceptions.ConnectionError:
    pass
else:
    ALLOWED_HOSTS.append(internal_ip)
del requests

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
    "aws_xray_sdk.ext.django",
]

MIDDLEWARE = [
    "aws_xray_sdk.ext.django.middleware.XRayMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://backend:8000",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://backend:3000",
]

ROOT_URLCONF = "generic_chatbot.urls"


ASGI_APPLICATION = "generic_chatbot.asgi.application"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR, 'templates'],
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

WSGI_APPLICATION = "generic_chatbot.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

X_FRAME_OPTIONS = 'ALLOWALL'
# consider restricting in production
CORS_ALLOW_ALL_ORIGINS = True
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True

XRAY_RECORDER = {
    'AWS_XRAY_DAEMON_ADDRESS': '127.0.0.1:2000',
    # If turned on built-in database queries and template rendering will be recorded as subsegments
    'AUTO_INSTRUMENT': True,
    'AWS_XRAY_CONTEXT_MISSING': 'LOG_ERROR',
    'PLUGINS': (),
    'SAMPLING': True,
    'SAMPLING_RULES': None,
    # the segment name for segments generated from incoming requests
    'AWS_XRAY_TRACING_NAME': 'generic-chatbot',
    'DYNAMIC_NAMING': None,  # defines a pattern that host names should match
    # defines when a segment starts to stream out its children subsegments
    'STREAMING_THRESHOLD': None,
}

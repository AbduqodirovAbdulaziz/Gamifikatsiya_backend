import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required in production")

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS if h.strip()]
if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS environment variable is required in production")

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": redis_url,
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [redis_url],
        },
    },
}

CELERY_BROKER_URL = redis_url
CELERY_RESULT_BACKEND = redis_url

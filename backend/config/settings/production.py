import os
from urllib.parse import urlparse

import dj_database_url

from .base import *

SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required in production")

DEBUG = False

ALLOWED_HOSTS = split_env_list("ALLOWED_HOSTS")
render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)

render_url = os.environ.get("RENDER_EXTERNAL_URL")
frontend_url = os.environ.get("FRONTEND_URL")
if render_url:
    render_host = urlparse(render_url).hostname
    if render_host and render_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(render_host)
if not ALLOWED_HOSTS:
    raise ValueError(
        "ALLOWED_HOSTS, RENDER_EXTERNAL_HOSTNAME, or RENDER_EXTERNAL_URL environment variable is required in production"
    )

CORS_ALLOWED_ORIGINS = split_env_list("CORS_ALLOWED_ORIGINS")
for origin in (render_url, frontend_url):
    if origin and origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(origin)

CSRF_TRUSTED_ORIGINS = split_env_list("CSRF_TRUSTED_ORIGINS")
for origin in (render_url, frontend_url):
    if origin and origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() in (
    "true",
    "1",
    "yes",
)
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

database_url = os.environ.get("DATABASE_URL")
if database_url:
    DATABASES["default"] = dj_database_url.parse(database_url, conn_max_age=600)

redis_url = os.environ.get("REDIS_URL")

if redis_url:
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
        }
    }
    CELERY_BROKER_URL = redis_url
    CELERY_RESULT_BACKEND = redis_url
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }

CELERY_TASK_ALWAYS_EAGER = False

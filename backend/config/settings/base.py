import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


def split_env_list(name, default=""):
    value = os.environ.get(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = "django-insecure-dev-key-only-for-development"

ALLOWED_HOSTS = split_env_list("ALLOWED_HOSTS", "*")

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "channels",
    "apps.users",
    "apps.classroom",
    "apps.courses",
    "apps.quizzes",
    "apps.gamification",
    "apps.competition",
    "apps.notifications",
    "apps.chat",
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

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
    }
}

AUTH_USER_MODEL = "users.CustomUser"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "quiz_submit": "30/hour",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

CORS_ALLOWED_ORIGINS = split_env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8081,http://localhost:8000",
)
render_url = os.environ.get("RENDER_EXTERNAL_URL")
frontend_url = os.environ.get("FRONTEND_URL")
for extra_origin in (render_url, frontend_url):
    if extra_origin and extra_origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(extra_origin)

CORS_ALLOW_CREDENTIALS = True

SPECTACULAR_SETTINGS = {
    "TITLE": "EduGame API",
    "DESCRIPTION": "Gamifikatsiya asosidagi ta'lim platformasi API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TIMEZONE = TIME_ZONE

# ═══════════════════════════════════════════════════════════
# JAZZMIN — Deep Navy #0F2854 premium tema
# ═══════════════════════════════════════════════════════════
JAZZMIN_SETTINGS = {
    "site_title": "EduGame Admin",
    "site_header": "EduGame",
    "site_brand": "EduGame",
    "default_theme_mode": "light",
    "welcome_sign": "EduGame boshqaruv paneliga xush kelibsiz!",
    "copyright": "EduGame",
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "icon": "fas fa-home"},
        {
            "name": "API Docs",
            "url": "/api/docs/",
            "icon": "fas fa-book",
            "new_window": True,
        },
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": ["apps.notifications"],
    "show_ui_builder": False,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "users.CustomUser": "fas fa-user-shield",
        "users.StudentProfile": "fas fa-user-graduate",
        "users.TeacherProfile": "fas fa-chalkboard-teacher",
        "courses.Course": "fas fa-book",
        "courses.Lesson": "fas fa-chalkboard",
        "courses.LessonProgress": "fas fa-tasks",
        "courses.CourseCompletion": "fas fa-certificate",
        "quizzes.Quiz": "fas fa-question-circle",
        "quizzes.Question": "fas fa-align-left",
        "quizzes.AnswerChoice": "fas fa-check-square",
        "quizzes.QuizAttempt": "fas fa-history",
        "quizzes.StudentAnswer": "fas fa-pen",
        "gamification.Badge": "fas fa-medal",
        "gamification.UserBadge": "fas fa-user-tag",
        "gamification.XPTransaction": "fas fa-coins",
        "gamification.LeaderboardEntry": "fas fa-trophy",
        "gamification.Streak": "fas fa-fire",
        "gamification.DailyQuest": "fas fa-calendar-check",
        "gamification.LevelTitle": "fas fa-star",
        "competition.Tournament": "fas fa-gamepad",
        "competition.TournamentParticipant": "fas fa-handshake",
        "competition.Challenge": "fas fa-bolt",
        "competition.ChallengeAttempt": "fas fa-running",
        "classroom.Classroom": "fas fa-school",
        "classroom.Enrollment": "fas fa-id-card",
        "classroom.ClassroomInvitation": "fas fa-envelope-open-text",
        "notifications.Notification": "fas fa-bell",
        "notifications.PushNotificationLog": "fas fa-clipboard-list",
        "chat.ChatRoom": "fas fa-comments",
        "chat.Message": "fas fa-comment-alt",
        "chat.MessageReaction": "fas fa-smile",
    },
}

# ═══════════════════════════════════════════════════════════
# Jazzmin UI Tweaklar
# ═══════════════════════════════════════════════════════════
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": True,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "flatly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

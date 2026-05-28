import os
from datetime import timedelta
from urllib.parse import urlparse
from decouple import config, Csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", default=False, cast=bool)

# Railway injects RAILWAY_STATIC_URL; allow it plus any explicit hosts
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "tenants",
    "users",
    "ingestion",
    "records",
    "audit",
    "dashboard",
]

_base_middleware = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# WhiteNoise must sit directly after SecurityMiddleware.
# Only load it in production — dev server serves staticfiles natively
# and WhiteNoise warns when STATIC_ROOT doesn't exist yet (no collectstatic run).
if not DEBUG:
    _base_middleware.insert(2, "whitenoise.middleware.WhiteNoiseMiddleware")

MIDDLEWARE = _base_middleware

ROOT_URLCONF = "breathe_esg.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "breathe_esg.wsgi.application"

# ── Database ─────────────────────────────────────────────────────────────────
# Railway provides DATABASE_URL automatically when a PostgreSQL plugin is added.
DATABASE_URL = config("DATABASE_URL")
_db = urlparse(DATABASE_URL)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _db.path[1:],
        "USER": _db.username,
        "PASSWORD": _db.password,
        "HOST": _db.hostname,
        "PORT": _db.port or 5432,
        "OPTIONS": {
            "sslmode": config("DB_SSLMODE", default="require"),
        },
        "CONN_MAX_AGE": 60,   # reuse connections; avoids per-request TCP overhead
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"
AUTH_PASSWORD_VALIDATORS = []

# ── Internationalisation ──────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"          # always store UTC; per-tenant display handled in UI
USE_I18N = True
USE_TZ = True

# ── Static / Media ────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")   # populated by collectstatic
# CompressedManifestStaticFilesStorage requires collectstatic to have run.
# Use default storage locally so runserver works without that step.
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = config("MEDIA_ROOT", default=os.path.join(BASE_DIR, "media"))


_cors_all = config("CORS_ALLOW_ALL_ORIGINS", default=False, cast=bool)
if _cors_all:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = config(
        "FRONTEND_URL",
        default="http://localhost:5173",
        cast=Csv(),
    )
CORS_ALLOW_CREDENTIALS = True   # needed for httpOnly refresh cookie

# ── Security headers (only meaningful when DEBUG=False) ───────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # Railway terminates TLS at the edge and proxies plain HTTP internally.
    # SECURE_SSL_REDIRECT must default False — Railway's proxy already enforces
    # HTTPS externally, and setting this True causes redirect loops behind the proxy.
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ── DRF ──────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# ── JWT ───────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(minutes=config("JWT_ACCESS_MINUTES", default=15, cast=int)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS":  False,
    "ALGORITHM":              "HS256",
    "SIGNING_KEY":            SECRET_KEY,
    "AUTH_HEADER_TYPES":      ("Bearer",),
    "USER_ID_FIELD":          "id",
    "USER_ID_CLAIM":          "user_id",
}

# ── Concur API ────────────────────────────────────────────────────────────────
CONCUR_CLIENT_ID     = config("CONCUR_CLIENT_ID",     default="")
CONCUR_CLIENT_SECRET = config("CONCUR_CLIENT_SECRET", default="")
CONCUR_BASE_URL      = config("CONCUR_BASE_URL",      default="https://us.api.concursolutions.com")

# ── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": config("LOG_LEVEL", default="INFO"),
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django.db.backends": {
            "handlers": ["console"],
            # Set to DEBUG locally to see SQL; keep WARNING in prod
            "level": config("DB_LOG_LEVEL", default="WARNING"),
            "propagate": False,
        },
    },
}
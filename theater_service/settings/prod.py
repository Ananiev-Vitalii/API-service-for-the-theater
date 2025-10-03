from theater_service.settings.base import *  # noqa

DEBUG = False

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ["POSTGRES_HOST"],
        "PORT": int(os.environ.get("POSTGRES_DB_PORT", 5432)),
        "OPTIONS": {"sslmode": "require"},
    }
}

STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

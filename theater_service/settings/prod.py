from theater_service.settings.base import *  # noqa

DEBUG = False

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS += ["anymail"]

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

EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"
ANYMAIL = {
    "SENDGRID_API_KEY": os.environ["SENDGRID_API_KEY"],
}
DEFAULT_FROM_EMAIL = "noreply@your-domain.com"
SERVER_EMAIL = DEFAULT_FROM_EMAIL

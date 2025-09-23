# from .base import *
#
# DEBUG = False
#
# ALLOWED_HOSTS = ["127.0.0.1"]
#
# RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
# if RENDER_EXTERNAL_HOSTNAME:
#     ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
#
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.environ["POSTGRES_DB"],
#         "USER": os.environ["POSTGRES_USER"],
#         "PASSWORD": os.environ["POSTGRES_PASSWORD"],
#         "HOST": os.environ["POSTGRES_HOST"],
#         "PORT": int(os.environ["POSTGRES_DB_PORT"]),
#
#     }
# }
#
# # AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
# # AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
# # AWS_STORAGE_BUCKET_NAME = os.environ["AWS_STORAGE_BUCKET_NAME"]
# # AWS_S3_REGION_NAME = os.environ["AWS_S3_REGION_NAME"]
# # AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
# DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
# MEDIA_ROOT = ""
# # MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"

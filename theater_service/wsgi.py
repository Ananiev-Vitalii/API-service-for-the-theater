"""
WSGI config for theater_service project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.conf import settings
from django.core.wsgi import get_wsgi_application

os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theater_service.settings')

application = get_wsgi_application()

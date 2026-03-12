"""
ASGI config for lovenest_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import sys

# Add Super Admin folder to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Super Admin'))

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lovenest_backend.settings')

application = get_asgi_application()

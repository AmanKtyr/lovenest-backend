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

import socketio
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lovenest_backend.settings')

django_asgi_app = get_asgi_application()

try:
    from api.socket_events import sio
    application = socketio.ASGIApp(sio, django_asgi_app)
except Exception as e:
    print(f"Failed to load socket events: {e}")
    application = django_asgi_app

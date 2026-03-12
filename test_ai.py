import os
import sys
from pathlib import Path
import django

# Setup django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lovenest_backend.settings')
django.setup()

from django.conf import settings
print(f"SETTINGS GEMINI_API_KEY: {'SET' if getattr(settings, 'GEMINI_API_KEY', None) else 'NONE'}")
if getattr(settings, 'GEMINI_API_KEY', None):
    print(f"KEY START: {settings.GEMINI_API_KEY[:4]}...")

from ai_features.services import get_model
try:
    model = get_model()
    print("SUCCESS: Model created")
except Exception as e:
    print(f"FAILURE: {e}")

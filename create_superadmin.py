import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lovenest_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(is_superuser=True).exists():
    user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    user.first_name = "Super"
    user.last_name = "Admin"
    user.save()
    print("Created superadmin account: admin / admin123")
else:
    print("Superuser already exists.")

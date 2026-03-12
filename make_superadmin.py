import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lovenest_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

email_target = 'ktyrpro@gmail.com'
user = User.objects.filter(email=email_target).first()

if user:
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print(f"Successfully made {user.email} a superuser!")
else:
    print(f"User {email_target} not found! Looking up all users:")
    for u in User.objects.all():
        print(f" - {u.email} (Username: {u.username}, Superuser: {u.is_superuser})")

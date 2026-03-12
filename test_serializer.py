import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from subscriptions.models import UserSubscription
from subscriptions.serializers import UserSubscriptionSerializer

try:
    subs = UserSubscription.objects.all()
    data = UserSubscriptionSerializer(subs, many=True).data
    with open('test_output.json', 'w') as f:
        import json
        json.dump(data, f)
    print("SUCCESS")
except Exception as e:
    import traceback
    with open('test_output.txt', 'w') as f:
        traceback.print_exc(file=f)
    print("ERROR")

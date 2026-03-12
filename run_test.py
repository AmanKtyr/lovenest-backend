import os
import django
import sys

# Set up Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lovenest_backend.settings') # Assuming project name is lovenest_backend based on previous file paths
django.setup()

from api.models import User, Notification

def run():
    print("Starting manual notification test...")
    u = User.objects.first()
    if u:
        print(f"Found user: {u.username} (ID: {u.id})")
        
        # Check existing count
        initial_count = Notification.objects.filter(recipient=u).count()
        print(f"Initial notification count: {initial_count}")

        # Create
        n = Notification.objects.create(
            recipient=u,
            actor=u,
            verb="System Test Notification",
            description="This is a test notification invoked manually via run_test.py",
            target_model="System",
            target_id="1"
        )
        print(f"Created notification ID: {n.id}")
        
        # Verify
        final_count = Notification.objects.filter(recipient=u).count()
        print(f"Final notification count: {final_count}")
        
        if final_count > initial_count:
            print("SUCCESS: Notification created and saved to DB.")
        else:
            print("FAILURE: Notification count did not increase.")
            
    else:
        print("No users found in database.")

if __name__ == "__main__":
    run()

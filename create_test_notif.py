from api.models import User, Notification

u = User.objects.first()
if u:
    print(f"Found user: {u.username} (ID: {u.id})")
    Notification.objects.create(
        recipient=u,
        actor=u,
        verb="System Test Notification",
        description="This is a test notification invoked manually to verify the system."
    )
    count = Notification.objects.filter(recipient=u, is_read=False).count()
    print(f"Notification created. Unread count for {u.username}: {count}")
else:
    print("No users found in database.")

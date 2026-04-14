import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import User, Memory, Notification

@receiver(post_delete, sender=User)
def delete_user_profile_image(sender, instance, **kwargs):
    """Deletes profile image from filesystem when user account is deleted."""
    try:
        if instance.profile_image and hasattr(instance.profile_image, 'path'):
            if os.path.isfile(instance.profile_image.path):
                os.remove(instance.profile_image.path)
    except (ValueError, OSError, Exception):
        pass

@receiver(post_delete, sender=Memory)
def delete_memory_image(sender, instance, **kwargs):
    """Deletes memory image from filesystem when memory entry is deleted."""
    try:
        if instance.image and hasattr(instance.image, 'path'):
            if os.path.isfile(instance.image.path):
                os.remove(instance.image.path)
    except (ValueError, OSError, Exception):
        pass


def create_notification(sender_user, couple, verb, target_model=None, target_id=None, description=None):
    """
    Create a notification for the partner in a couple.
    Called from views like update_mood, request_deletion, reset_password_with_partner, etc.
    """
    if not couple:
        return None

    # Determine the recipient (the other partner)
    recipient = couple.get_other_user(sender_user)
    if not recipient:
        return None

    return Notification.objects.create(
        recipient=recipient,
        actor=sender_user,
        verb=verb,
        target_model=target_model or '',
        target_id=str(target_id) if target_id else '',
        description=description or '',
    )

from django.db.models.signals import post_save

@receiver(post_save, sender=Notification)
def emit_notification_on_save(sender, instance, created, **kwargs):
    if created:
        try:
            from api.socket_events import sio
            import asyncio
            data = {
                'id': instance.id,
                'verb': instance.verb,
                'description': instance.description,
                'target_model': instance.target_model,
                'created_at': instance.created_at.isoformat(),
                'actor': {'username': instance.actor.username} if instance.actor else None
            }
            user_room = f"user_{instance.recipient.id}"
            
            async def emit_notif():
                await sio.emit('new_notification', data, room=user_room)
                
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(emit_notif())
            else:
                loop.run_until_complete(emit_notif())
        except Exception as e:
            print(f"Notification socket emit failed: {e}")

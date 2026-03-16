import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import User, Memory, Notification

@receiver(post_delete, sender=User)
def delete_user_profile_image(sender, instance, **kwargs):
    """Deletes profile image from filesystem when user account is deleted."""
    if instance.profile_image:
        if os.path.isfile(instance.profile_image.path):
            try:
                os.remove(instance.profile_image.path)
            except Exception:
                pass

@receiver(post_delete, sender=Memory)
def delete_memory_image(sender, instance, **kwargs):
    """Deletes memory image from filesystem when memory entry is deleted."""
    if instance.image:
        if os.path.isfile(instance.image.path):
            try:
                os.remove(instance.image.path)
            except Exception:
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


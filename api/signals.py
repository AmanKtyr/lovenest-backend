import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import User, Memory

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

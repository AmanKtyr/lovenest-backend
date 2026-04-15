import os
import asyncio
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import User, Memory, Notification, ChatMessage, Todo, BucketItem, Question
from asgiref.sync import sync_to_async

from asgiref.sync import async_to_sync

def emit_socket_event(event_name, data, room):
    """
    Safely emit a socket event from a synchronous context (Django signal/view)
    to the asynchronous Socket.io server.
    """
    try:
        from api.socket_events import sio
        
        # We try to use async_to_sync which is the standard way to bridge
        # synchronous Django views/signals to asynchronous code in an ASGI setup.
        try:
            async_to_sync(sio.emit)(event_name, data, room=room)
        except Exception:
            # Fallback for complex threading environments or if async_to_sync fails
            import asyncio
            async def do_emit():
                await sio.emit(event_name, data, room=room)
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(do_emit())
                else:
                    loop.run_until_complete(do_emit())
            except RuntimeError:
                asyncio.run(do_emit())
    except Exception as e:
        print(f"Socket emit failed: {e}")

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
    """
    if not couple: return None
    recipient = couple.get_other_user(sender_user)
    if not recipient: return None

    return Notification.objects.create(
        recipient=recipient,
        actor=sender_user,
        verb=verb,
        target_model=target_model or '',
        target_id=str(target_id) if target_id else '',
        description=description or '',
    )

@receiver(post_save, sender=Notification)
def emit_notification_on_save(sender, instance, created, **kwargs):
    if created:
        data = {
            'id': instance.id,
            'verb': instance.verb,
            'description': instance.description,
            'target_model': instance.target_model,
            'target_id': instance.target_id,
            'created_at': instance.created_at.isoformat(),
            'actor': {'username': instance.actor.username} if instance.actor else None
        }
        user_room = f"user_{instance.recipient.id}"
        emit_socket_event('new_notification', data, user_room)

# Industrial Real-time Auto-Notifications for Core Features
@receiver(post_save, sender=Todo)
def notify_todo_update(sender, instance, created, **kwargs):
    verb = "added a new todo" if created else "updated a todo"
    couple = instance.couple
    create_notification(
        sender_user=instance.created_by,
        couple=couple,
        verb=f"{verb}: {instance.title}",
        target_model='Todo',
        target_id=instance.id
    )
    # Broadcast general update for real-time UI refresh
    emit_socket_event('model_updated', {'model': 'Todo', 'action': 'save', 'id': instance.id}, f"couple_{couple.id}")

@receiver(post_save, sender=Memory)
def notify_memory_added(sender, instance, created, **kwargs):
    if created:
        create_notification(
            sender_user=instance.couple.partner_1,
            couple=instance.couple,
            verb=f"added a new memory: {instance.title}",
            target_model='Memory',
            target_id=instance.id
        )
        emit_socket_event('model_updated', {'model': 'Memory', 'action': 'create', 'id': instance.id}, f"couple_{instance.couple.id}")

@receiver(post_save, sender=BucketItem)
def notify_bucket_update(sender, instance, created, **kwargs):
    verb = "added a bucket list item" if created else "updated a bucket list item"
    create_notification(
        sender_user=instance.couple.partner_1,
        couple=instance.couple,
        verb=f"{verb}: {instance.title}",
        target_model='BucketItem',
        target_id=instance.id
    )
    emit_socket_event('model_updated', {'model': 'BucketItem', 'action': 'save', 'id': instance.id}, f"couple_{instance.couple.id}")

@receiver(post_save, sender=Question)
def notify_question_added(sender, instance, created, **kwargs):
    if created:
        create_notification(
            sender_user=instance.creator,
            couple=instance.couple,
            verb=f"asked a new question: {instance.text}",
            target_model='Question',
            target_id=instance.id
        )
        emit_socket_event('model_updated', {'model': 'Question', 'action': 'create', 'id': instance.id}, f"couple_{instance.couple.id}")


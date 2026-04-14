import socketio
import os
import django
from django.utils import timezone
from datetime import timedelta
from asgiref.sync import sync_to_async

# Initialize Django (needed if this file is imported early by ASGI)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lovenest_backend.settings')
django.setup()

from api.models import Couple, User, ChatMessage

# Create an ASGI Async Server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

@sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

@sync_to_async
def get_couple(couple_id):
    try:
        return Couple.objects.get(id=couple_id)
    except Couple.DoesNotExist:
        return None

@sync_to_async
def save_chat_message(couple, sender, content):
    return ChatMessage.objects.create(couple=couple, sender=sender, content=content)

@sync_to_async
def cleanup_old_messages(couple_id):
    cutoff = timezone.now() - timedelta(hours=24)
    return ChatMessage.objects.filter(couple_id=couple_id, created_at__lt=cutoff).delete()

@sio.event
async def connect(sid, environ):
    # Industrial logging for debugging real-time connections
    print(f"Socket connected: {sid}")

@sio.event
async def join_room(sid, data):
    couple_id = data.get('couple_id')
    user_id = data.get('user_id')
    
    if user_id:
        user_room = f"user_{user_id}"
        await sio.enter_room(sid, user_room)
        print(f"User {user_id} joined room: {user_room}")
        
    if couple_id:
        room = f"couple_{couple_id}"
        await sio.enter_room(sid, room)
        print(f"User {user_id} joined couple room: {room}")
        await sio.emit('joined', {'room': room, 'user': user_id}, room=room)

@sio.event
async def send_message(sid, data):
    """
    Receives matching data: couple_id, sender_id, content
    """
    couple_id = data.get('couple_id')
    sender_id = data.get('sender_id')
    content = data.get('content')
    
    if not couple_id or not sender_id or not content:
        return

    # Delete messages older than 24h for this couple
    await cleanup_old_messages(couple_id)
    
    # Save the new message
    try:
        sender = await get_user(sender_id)
        couple = await get_couple(couple_id)
        
        if sender and couple:
            msg = await save_chat_message(couple, sender, content)
            
            room = f"couple_{couple_id}"
            await sio.emit('new_message', {
                'id': msg.id,
                'sender_id': sender.id,
                'content': msg.content,
                'created_at': msg.created_at.isoformat()
            }, room=room)
    except Exception as e:
        print(f"Chat Socket Exception: {e}")

@sio.event
async def disconnect(sid):
    print(f"Socket disconnected: {sid}")

@sio.event
async def typing(sid, data):
    couple_id = data.get('couple_id')
    user_id = data.get('user_id')
    if couple_id and user_id:
        room = f"couple_{couple_id}"
        await sio.emit('partner_typing', {'user_id': user_id}, room=room, skip_sid=sid)

@sio.event
async def stop_typing(sid, data):
    couple_id = data.get('couple_id')
    user_id = data.get('user_id')
    if couple_id and user_id:
        room = f"couple_{couple_id}"
        await sio.emit('partner_stop_typing', {'user_id': user_id}, room=room, skip_sid=sid)


import socketio
import os
import django
from django.utils import timezone
from datetime import timedelta

# Initialize Django (needed if this file is imported early by ASGI)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lovenest_backend.settings')
django.setup()

from api.models import Couple, User, ChatMessage

# Create an ASGI Async Server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

@sio.event
async def connect(sid, environ):
    # Note: For production, extract user token from headers or query string
    # For now, we will trust the client joining the "couple_room"
    pass

@sio.event
async def join_room(sid, data):
    couple_id = data.get('couple_id')
    user_id = data.get('user_id')
    
    if user_id:
        user_room = f"user_{user_id}"
        sio.enter_room(sid, user_room)
        
    if couple_id:
        room = f"couple_{couple_id}"
        sio.enter_room(sid, room)
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
    cutoff = timezone.now() - timedelta(hours=24)
    ChatMessage.objects.filter(couple_id=couple_id, created_at__lt=cutoff).delete()
    
    # Save the new message
    try:
        sender = User.objects.get(id=sender_id)
        couple = Couple.objects.get(id=couple_id)
        msg = ChatMessage.objects.create(couple=couple, sender=sender, content=content)
        
        room = f"couple_{couple_id}"
        await sio.emit('new_message', {
            'id': msg.id,
            'sender_id': msg.sender.id,
            'content': msg.content,
            'created_at': msg.created_at.isoformat()
        }, room=room)
    except Exception as e:
        print(f"Chat Exception: {e}")

@sio.event
async def disconnect(sid):
    pass

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

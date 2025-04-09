from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from .models import Room, Message
from .forms import UserRegistrationForm
from django.http import JsonResponse
import importlib

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('chat:index')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def index(request):
    rooms = Room.objects.all()
    return render(request, 'chat/index.html', {
        'rooms': rooms
    })

@login_required
def room(request, room_name):
    # Get or create room
    room, created = Room.objects.get_or_create(name=room_name)
    
    # Get most recent messages for this room, ordered by timestamp
    messages = Message.objects.filter(room=room).order_by('timestamp')[:100]
    
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'username': request.user.username,
        'messages': messages,
        'room_id': room.id
    })

@login_required
def diagnostics(request):
    """View for diagnosing WebSocket connection issues"""
    room_count = Room.objects.count()
    message_count = Message.objects.count()
    
    # Get latest messages
    latest_messages = Message.objects.order_by('-timestamp')[:10]
    
    return render(request, 'chat/diagnostics.html', {
        'room_count': room_count,
        'message_count': message_count,
        'latest_messages': latest_messages,
        'username': request.user.username
    })

@login_required
def message_api(request, room_name):
    """API view to get messages for a room"""
    try:
        room = Room.objects.get(name=room_name)
        messages = Message.objects.filter(room=room).order_by('timestamp')[:100]
        message_data = [{
            'id': msg.id,
            'username': msg.user.username,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for msg in messages]
        return JsonResponse({'messages': message_data, 'count': len(message_data)})
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)

@login_required
def server_info_api(request):
    """API endpoint to get server information"""
    redis_available = False
    channels_version = "Not installed"
    asgi_server = "Unknown"
    
    # Check if channels is installed and get version
    try:
        channels = importlib.import_module('channels')
        channels_version = getattr(channels, '__version__', 'Unknown')
    except ImportError:
        channels_version = "Not installed"
    
    # Check if Redis is available
    try:
        from channels_redis.core import RedisChannelLayer
        import redis
        
        client = redis.Redis(host='127.0.0.1', port=6379, db=0)
        client.ping()
        redis_available = True
    except Exception as e:
        redis_available = False
    
    # Get ASGI server info
    try:
        import sys
        if 'daphne' in sys.modules:
            asgi_server = "Daphne"
        elif 'uvicorn' in sys.modules:
            asgi_server = "Uvicorn"
        elif 'hypercorn' in sys.modules:
            asgi_server = "Hypercorn"
    except Exception:
        pass
    
    return JsonResponse({
        'channels_version': channels_version,
        'redis_available': redis_available,
        'asgi_server': asgi_server,
    })

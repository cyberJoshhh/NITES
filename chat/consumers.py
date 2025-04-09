import json
import urllib.parse
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message, Room

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # URL decode the room name to handle spaces and special characters
        encoded_room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_name = urllib.parse.unquote(encoded_room_name)
        
        # Create a safe version of the room name for the channel layer
        # Channel layer names must be ASCII alphanumerics, hyphens, underscores, or periods
        self.room_group_name = f'chat_{hash(self.room_name)}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        print(f"WebSocket connected for room: {self.room_name}")
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected from room: {self.room_name}, code: {close_code}")

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            username = text_data_json['username']
            
            print(f"Received message from {username} in room {self.room_name}: {message[:50]}")
            
            # Save message to database
            await self.save_message(username, message)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username
                }
            )
        except Exception as e:
            print(f"Error in receive: {e}")
            # Send error message back to client
            await self.send(text_data=json.dumps({
                'error': str(e),
                'message': 'Error processing your message',
                'username': 'System'
            }))

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username
        }))
    
    @database_sync_to_async
    def save_message(self, username, message):
        try:
            user = User.objects.get(username=username)
            room, created = Room.objects.get_or_create(name=self.room_name)
            msg = Message.objects.create(user=user, room=room, content=message)
            print(f"Message saved to database: {msg}")
            return True
        except User.DoesNotExist:
            print(f"User {username} does not exist")
            return False
        except Exception as e:
            print(f"Error saving message: {e}")
            return False 
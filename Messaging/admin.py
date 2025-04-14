from django.contrib import admin
from .models import ChatGroup, Message

@admin.register(ChatGroup)
class ChatGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    search_fields = ('name',)
    filter_horizontal = ('members',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'group', 'content', 'timestamp', 'is_read', 'message_type')
    list_filter = ('message_type', 'is_read', 'timestamp')
    search_fields = ('content',)
    date_hierarchy = 'timestamp'

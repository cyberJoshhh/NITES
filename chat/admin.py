from django.contrib import admin
from .models import Room, Message

class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'content', 'timestamp')
    list_filter = ('room', 'user', 'timestamp')
    search_fields = ('content', 'user__username', 'room__name')
    date_hierarchy = 'timestamp'

class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    date_hierarchy = 'created_at'

admin.site.register(Room, RoomAdmin)
admin.site.register(Message, MessageAdmin)

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from System.models import PDFFile

class ChatGroup(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, related_name='chat_groups')
    
    def __str__(self):
        return self.name

class Message(models.Model):
    MESSAGE_TYPES = (
        ('direct', 'Direct Message'),
        ('group', 'Group Message'),
    )
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    content = models.TextField(blank=True)  # Allow empty content when there's an attachment
    attachment = models.ForeignKey(PDFFile, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        if self.message_type == 'direct':
            return f"From {self.sender} to {self.recipient}: {self.content[:20]}"
        else:
            return f"From {self.sender} to group {self.group}: {self.content[:20]}"

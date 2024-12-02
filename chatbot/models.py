from django.db import models
from accounts.models import CustomUser
from django.utils import timezone


class ChatMessage(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True) 
    is_user_message = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.name} - {'User' if self.is_user_message else 'Bot'}: {self.message}"

    class Meta:
        ordering = ['created_at']


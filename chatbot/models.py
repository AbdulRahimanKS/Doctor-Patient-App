from django.db import models
from accounts.models import CustomUser
from django.utils.timezone import now
from zoneinfo import ZoneInfo


class ChatMessage(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True) 
    is_user_message = models.BooleanField(default=True)
    
    # def save(self, *args, **kwargs):
    #     if not self.created_at:
    #         india_timezone = ZoneInfo('Asia/Kolkata')
    #         self.created_at = now().astimezone(india_timezone)
    #     super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.name} - {'User' if self.is_user_message else 'Bot'}: {self.message}"

    class Meta:
        ordering = ['created_at']


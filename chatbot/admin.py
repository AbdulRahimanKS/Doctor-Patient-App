from django.contrib import admin
from chatbot.models import ChatMessage

class ChatMessageAdmin(admin.ModelAdmin):
    ordering = ('-created_at',)

admin.site.register(ChatMessage, ChatMessageAdmin)

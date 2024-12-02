from typing import Any
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from chatbot.models import ChatMessage
from datetime import date, timedelta, datetime
from django.utils.timezone import localtime


# To view chat page
class ChatPageView(TemplateView):
    template_name = 'chat_page.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat_messages = ChatMessage.objects.filter(user=self.request.user).order_by('created_at')
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        chat_history = []
        for message in chat_messages:
            message_date = message.created_at.date()
            
            if message_date == today:
                date_label = "Today"
            elif message_date == yesterday:
                date_label = "Yesterday"
            else:
                date_label = message_date.strftime("%d %B %Y")
                
            chat_history.append({
                'message': message.message,
                'is_user_message': message.is_user_message,
                'created_at': localtime(message.created_at).strftime("%I:%M %p"),
                'date_label': date_label,
            })

        grouped_chat_history = {}
        for entry in chat_history:
            grouped_chat_history.setdefault(entry['date_label'], []).append(entry)

        context['chat_history'] = grouped_chat_history
                
        return context
    
    
# To get bot response
class ChatbotAPIView(APIView):
    def post(self, request, *args, **kwargs):
        hardcoded_responses = {
            'hello': 'Hi! How can I assist you today?',
            'how are you': 'I\'m doing great, thank you for asking!',
            'bye': 'Goodbye! Have a nice day!',
        }
        
        user_message = request.data.get('message', '').lower()
        bot_reply = hardcoded_responses.get(user_message, "Sorry, I didn't understand that. Can you rephrase?")
        
        ChatMessage.objects.create(user=self.request.user, message=user_message, is_user_message=True)
        ChatMessage.objects.create(user=self.request.user, message=bot_reply, is_user_message=False)
        
        return Response({
            'response': bot_reply
        }, status=status.HTTP_200_OK)
    
    
    
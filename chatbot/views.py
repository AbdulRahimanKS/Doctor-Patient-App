from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from chatbot.models import ChatMessage
from datetime import timedelta
from django.utils.timezone import localtime, localdate
from django.utils import timezone
from accounts.mixins import PatientLoginRequiredMixin


# To view chat page
class ChatPageView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'chat_page.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat_messages = ChatMessage.objects.filter(user=self.request.user).order_by('created_at')
        
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)
        
        chat_history = []
        for message in chat_messages:
            local_created_at = localtime(message.created_at)
            message_date = local_created_at.date()
            
            if message_date == today:
                date_label = "Today"
            elif message_date == yesterday:
                date_label = "Yesterday"
            else:
                date_label = message_date.strftime("%d %B %Y")
                
            chat_history.append({
                'message': message.message,
                'is_user_message': message.is_user_message,
                'created_at': local_created_at.strftime("%I:%M %p"),
                'date_label': date_label,
            })

        grouped_chat_history = {}
        for entry in chat_history:
            grouped_chat_history.setdefault(entry['date_label'], []).append(entry)

        context['chat_history'] = grouped_chat_history
                
        return context
    
    
# To chat dynamically
class ChatbotAPIView(PatientLoginRequiredMixin, APIView):
    def post(self, request, *args, **kwargs):
        hardcoded_responses = {
            'hello': 'Hi! How can I assist you today?',
            'how are you': 'I\'m doing great, thank you for asking!',
            'bye': 'Goodbye! Have a nice day!',
        }
        
        user_message = request.data.get('message', '').lower()
        bot_reply = hardcoded_responses.get(user_message, "Sorry, I didn't understand that. Can you rephrase?")
        
        today = localdate()
        
        user_msg_obj = ChatMessage.objects.create(user=self.request.user, message=user_message, is_user_message=True)
        bot_msg_obj = ChatMessage.objects.create(user=self.request.user, message=bot_reply, is_user_message=False)
        
        user_msg_created_at = localtime(user_msg_obj.created_at)
        bot_msg_created_at = localtime(bot_msg_obj.created_at)
             
        return Response({
            'user_message': {
                'message': user_message,
                'created_at': user_msg_created_at.strftime("%I:%M %p"),
                'added_time': user_msg_obj.created_at,
            },
            'bot_reply': {
                'message': bot_reply,
                'created_at': bot_msg_created_at.strftime("%I:%M %p"),
                'added_time': bot_msg_obj.created_at,
            }
        }, status=status.HTTP_200_OK)

    
    
from django.urls import path
from chatbot.views import  ChatPageView, ChatbotAPIView


urlpatterns = [
    path('chat_page/', ChatPageView.as_view(), name='chat_page'),
    path('chat_response/', ChatbotAPIView.as_view(), name='chat_response'),
]


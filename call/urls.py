from django.urls import path
from call.views import TestAPIView, APICall


urlpatterns = [
    path('test/', TestAPIView.as_view(), name='test'),
    path('api/', APICall.as_view(), name='api'),
]

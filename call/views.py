import json
from django.views.generic import TemplateView
from django.views import View
from requests import request
from DoctorApp.settings import VIDEO_SDK_API_KEY
from django.http import HttpResponse, JsonResponse


class TestAPIView(TemplateView):
    template_name = 'test.html'
    

class APICall(View):
    def post(self, request, *args, **kwargs):
        username = 'sample'
        apiKey = VIDEO_SDK_API_KEY
        meeting_id = "8yi4-66lo-8lw6"
        is_doctor = True
        
        return JsonResponse({'success': True, 'username': username, 'apiKey': apiKey, 'meeting_id': meeting_id, 'is_doctor': is_doctor})

    
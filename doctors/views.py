from collections import defaultdict
from io import BytesIO
import json
import os
import zipfile
from django.utils.timezone import now, localtime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView
import jwt
import requests
from django.http import FileResponse
from patients.models import AppointmentSlot, DoctorProfile, PatientInfo, PatientAttachments, Notification
from django.contrib import messages
from django.db.models import Q
from datetime import datetime, timedelta
from DoctorApp.settings import VIDEO_SDK_API_KEY, VIDEO_SDK_API_SECRET, VIDEO_SDK_API_URL
from patients.utils import get_india_timezone


# Doctor home page view
class DoctorHomeView(TemplateView):
    template_name = 'doctor_home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_date, current_time_obj = get_india_timezone()

        doctor = get_object_or_404(DoctorProfile.objects.select_related('specialization'), user=self.request.user)

        # today_appointments = AppointmentSlot.objects.filter(
        #     doctor=doctor, is_available=True, is_booked=True, date=current_date).filter(end_time__gte=current_time_obj).order_by('-start_time')
        
        today_appointments = AppointmentSlot.objects.filter(doctor=doctor, is_available=True, is_booked=True)

        
        for slot in today_appointments:
            confirmed_appointment = slot.appointmentrequest_set.filter(status='Confirmed').first()
            slot.confirmed_appointment = confirmed_appointment

            if confirmed_appointment:
                patient_info = PatientInfo.objects.filter(appointment=confirmed_appointment).first()
                slot.patient_info = patient_info
                
                if patient_info:
                    patient_attachments = PatientAttachments.objects.filter(patient_info=patient_info)
                    slot.patient_attachments = patient_attachments
                    
        notification_count = Notification.objects.filter(user=self.request.user, is_read=False).count()

        context['today_appointments'] = today_appointments
        context['notification_count'] = notification_count
        
        return context
    
    
# Slot adding view
class SlotAddView(TemplateView):
    template_name = 'add_slots.html'
    
    def post(self, request, *args, **kwargs):
        appointment_date = request.POST.get('appointment-date')
        start_time = request.POST.get('start-time')
        end_time = request.POST.get('end-time')
    
        doctor = get_object_or_404(DoctorProfile, user=self.request.user)
        
        existing_slot = AppointmentSlot.objects.filter(doctor=doctor, date=appointment_date, start_time=start_time, end_time=end_time).exists()
        
        if existing_slot:
            messages.info(request, 'Slot with same data already exists. Please add another slot!')
            return self.render_to_response({'appointment_date': appointment_date, 'start_time': start_time, 'end_time': end_time})
        slot = AppointmentSlot.objects.create(doctor=doctor, date=appointment_date, start_time=start_time, end_time=end_time)
    
        return redirect('doctor_home')
    

# Slot list view
class SlotListView(TemplateView):
    template_name ='list_slots.html'
    
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip().lower()
        
        doctor = get_object_or_404(DoctorProfile, user=self.request.user)
        slots = AppointmentSlot.objects.filter(doctor=doctor).order_by('-date', '-start_time')
        
        if query:
            try:
                month_number = datetime.strptime(query, '%B').month
                slots = slots.filter(date__month=month_number)
            except ValueError:
                slots = slots.filter(
                    Q(date__icontains=query) | Q(start_time__icontains=query) | Q(end_time__icontains=query)
                )

        return self.render_to_response({'slots': slots, 'query': query})
    
    
# Start meeting view
class SlotStartMeeting(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        doctor_id = data.get('doctor_id')
        appointment_slot_id = data.get('appointment_id')
        is_doctor = False
        
        slot = get_object_or_404(AppointmentSlot, id=appointment_slot_id)
        doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        
        if self.request.user.user_type == 'Doctor':
            user_name = doctor.full_name
            is_doctor = True
        else:
            appointment_request = slot.appointmentrequest_set.first()
            user_name = appointment_request.patient_info.patient_name
        
        if slot.room_id:
            return JsonResponse({'success': True, 'user_name': user_name, 'meeting_id': slot.room_id, 'apiKey': VIDEO_SDK_API_KEY, 'is_doctor': is_doctor})
            
        try:
            payload = {
                "apikey": VIDEO_SDK_API_KEY,
                "permissions": ["allow_join", "allow_mod"],
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=30),
            }
            token = jwt.encode(payload, VIDEO_SDK_API_SECRET, algorithm="HS256")
            
            headers = {
                "authorization": token,
                "Content-Type": "application/json"
            }
            
            response = requests.post(VIDEO_SDK_API_URL, headers=headers)
            response_data = response.json()
            
            if response.status_code == 200:
                room_id = response_data["roomId"]
                slot.room_id = room_id
                slot.save()
            
                return JsonResponse({'success': True, 'user_name': user_name, 'meeting_id': room_id, 'apiKey': VIDEO_SDK_API_KEY, 'is_doctor': is_doctor})
            else:
                return JsonResponse({'success': False, 'error': "Failed to create a meeting"})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f"Error while creating meeting: {e}"})
            
            
# Patient attachments download view
class DownloadAttachmentsView(View):
    def get(self, request, *args, **kwargs):
        patient_id = kwargs.get('patient_id')
        
        patient_info = get_object_or_404(PatientInfo, id=patient_id)
        attachments = PatientAttachments.objects.filter(patient_info=patient_info)
        
        if attachments.count() == 1:
            attachment = attachments.first()
            file_path = attachment.file.path 
            response = FileResponse(open(file_path, 'rb'), as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for attachment in attachments:
                file_path = attachment.file.path 
                zip_file.write(file_path, os.path.basename(file_path)) 

        zip_buffer.seek(0)

        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{patient_info.patient_name}_attachments.zip"'
        return response
                    
                    
# To show notifications
class NotificationPageView(TemplateView):
    template_name = 'notification_doctor.html'
    
    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        
        notifications = Notification.objects.filter(user=self.request.user).order_by('created_at')
        grouped_notifications = defaultdict(list)
        
        for notification in notifications:
            notification_date = localtime(notification.created_at).date()
            today = now().date()
            yesterday = (now() - timedelta(days=1)).date()

            if notification_date == today:
                group_key = "Today"
            elif notification_date == yesterday:
                group_key = "Yesterday"
            else:
                group_key = notification_date.strftime('%d %b, %Y')

            grouped_notifications[group_key].append(notification)
        
        context['grouped_notifications'] = grouped_notifications
        print(grouped_notifications)
        return context            

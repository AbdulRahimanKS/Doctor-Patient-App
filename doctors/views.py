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
from patients.models import AppointmentSlot, DoctorProfile, PatientInfo, PatientAttachments, Notification, Category, Specialization
from accounts.models import CustomUser
from django.contrib import messages
from django.db.models import Q
from datetime import datetime, timedelta
from DoctorApp.settings import VIDEO_SDK_API_KEY, VIDEO_SDK_API_SECRET, VIDEO_SDK_API_URL
from patients.utils import get_india_timezone
from accounts.utils import generate_jwt_token, validate_jwt_token
from django.contrib.auth import login, logout 
from doctors.models import Prescription
from doctors.forms import PrescriptionForm
from django.utils.html import strip_tags    
import re
from accounts.mixins import DoctorLoginRequiredMixin


# Doctor home page view
class DoctorHomeView(DoctorLoginRequiredMixin, TemplateView):
    template_name = 'doctor_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_date, current_time_obj = get_india_timezone()

        doctor = get_object_or_404(DoctorProfile.objects.select_related('specialization'), user=self.request.user)

        today_appointments = AppointmentSlot.objects.filter(
            doctor=doctor, is_available=True, is_booked=True, date=current_date).filter(
                end_time__gte=current_time_obj).exclude(slot__status='Approved').order_by('-start_time')
        
        for slot in today_appointments:
            confirmed_appointment = slot.slots.filter(status='Confirmed').first()
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
class SlotAddView(DoctorLoginRequiredMixin, TemplateView):
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
class SlotListView(DoctorLoginRequiredMixin, TemplateView):
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
        user=self.request.user
        
        slot = get_object_or_404(AppointmentSlot, id=appointment_slot_id)
        doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        
        if self.request.user.user_type == 'Doctor':
            user_name = doctor.full_name
            is_doctor = True
        else:
            appointment_request = slot.slots.first()
            user_name = appointment_request.patient_info.patient_name
            
        token = generate_jwt_token(user)
        user.jwt_token = token
        user.save()
        
        if slot.room_id:
            return JsonResponse({'success': True, 'user_name': user_name, 'meeting_id': slot.room_id, 'apiKey': VIDEO_SDK_API_KEY, 'is_doctor': is_doctor, 'token': token})
            
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
            
                return JsonResponse({'success': True, 'user_name': user_name, 'meeting_id': room_id, 'apiKey': VIDEO_SDK_API_KEY, 'is_doctor': is_doctor, 'token': token})
            else:
                return JsonResponse({'success': False, 'error': "Failed to create a meeting"})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f"Error while creating meeting: {e}"})
            
            
# Patient attachments download view
class DownloadAttachmentsView(DoctorLoginRequiredMixin, View):
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
class NotificationDoctorView(DoctorLoginRequiredMixin, TemplateView):
    template_name = 'notification_doctor.html'
    
    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        
        notifications = Notification.objects.filter(user=self.request.user).order_by('-created_at')        
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
            time_diff = now() - notification.created_at
            notification.is_just_now = time_diff < timedelta(minutes=1)
            
        context['grouped_notifications'] = dict(grouped_notifications)
        
        return context  
    

# To read notifications
class NotificationsReadView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        
        if self.request.user.is_authenticated:
            notification = Notification.objects.get(id=notification_id, user=self.request.user)
            notification.is_read = True
            notification.save()
            
            return JsonResponse({'status': 'success'})
        
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'})    
    
    
# Doctor profile page view
class DoctorProfilePageView(DoctorLoginRequiredMixin, TemplateView):
    template_name = 'doctor_profile_page.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor_profile = get_object_or_404(DoctorProfile.objects.select_related('user'), user=self.request.user)
        context['doctor_profile'] = doctor_profile
        
        return context
    
    
# API request to get specialization names
class GetSpecializationsView(DoctorLoginRequiredMixin, View):
    def get(self, request, category_id, *args, **kwargs):
        specializations = Specialization.objects.filter(category__id=category_id)
        data = {
            'specializations': [{'id': specialization.id, 'name': specialization.name} for specialization in specializations]
        }
        
        return JsonResponse(data)
    
    
# Doctor profile edit view
class DoctorProfileEditView(DoctorLoginRequiredMixin, TemplateView):
    template_name = 'edit_doctor_profile.html'
              
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor_profile_id = kwargs.get('id')
        doctor_profile = get_object_or_404(DoctorProfile.objects.select_related('user', 'specialization__category'), id=doctor_profile_id)
        categories = Category.objects.prefetch_related('specializations').all()
        
        selected_category = doctor_profile.specialization.category
        filtered_specializations = selected_category.specializations.all() if selected_category else None
        
        context['doctor_profile'] = doctor_profile
        context['categories'] = categories
        context['filtered_specializations'] = filtered_specializations
        
        return context
    
    def post(self, request, *args, **kwargs):
        doctor_profile_id = request.POST.get('doctor_profile_id')
        profile_picture = request.FILES.get('profile_picture')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        gender = request.POST.get('gender')
        dob = request.POST.get('dob')
        country = request.POST.get('country') 
        countryCode = request.POST.get('country_code')
        specialization_category_id = request.POST.get('specialization_category')
        specialization_name_id = request.POST.get('specialization_name')
        qualification = request.POST.get('qualification')
        college = request.POST.get('college')
        experience_years = request.POST.get('experience_years')
        consultation_fee = request.POST.get('consultation_fee')
        about = request.POST.get('about')
        clinic_address = request.POST.get('clinic_address')
        remove_profile_picture = request.POST.get('remove_profile_picture') == 'true'

        doctor_profile = get_object_or_404(DoctorProfile.objects.select_related('user'), id=doctor_profile_id)
        user = doctor_profile.user
        
        user.email = email
        user.country = country
        user.countryCode = countryCode
        user.mobile = mobile
        user.save()

        doctor_profile.first_name = first_name
        doctor_profile.last_name = last_name
        doctor_profile.gender = gender
        doctor_profile.qualification = qualification
        doctor_profile.college = college
        doctor_profile.experience_years = experience_years
        doctor_profile.consultation_fee = consultation_fee
        doctor_profile.about = about
        doctor_profile.clinic_address = clinic_address
        
        if dob:
            doctor_profile.dob = dob 
        else:
            doctor_profile.dob = None
            
        if remove_profile_picture:
            doctor_profile.profile_picture = None
        elif profile_picture:
            doctor_profile.profile_picture = profile_picture
            
        if specialization_name_id:
            specialization_obj = get_object_or_404(Specialization, id=specialization_name_id)
            doctor_profile.specialization = specialization_obj
                
            doctor_profile.specialization = specialization_obj
        
        if specialization_category_id:
            specialization_category_obj = get_object_or_404(Category, id=specialization_category_id)
            if doctor_profile.specialization and doctor_profile.specialization.category != specialization_category_obj:
                doctor_profile.specialization.category = specialization_category_obj
                doctor_profile.specialization.save()
            
        doctor_profile.save()

        return redirect('doctor_profile_page')
        
    
# Doctor video page
class DoctorVideoPageView(DoctorLoginRequiredMixin, TemplateView):
    template_name = 'video_page.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_date, current_time_obj = get_india_timezone()

        doctor = get_object_or_404(DoctorProfile, user=self.request.user)

        upcoming_appointments = AppointmentSlot.objects.filter(
            doctor=doctor, is_available=True, is_booked=True).filter(Q(date=current_date, end_time__gte=current_time_obj) | Q(date__gt=current_date)
        ).exclude(slot__status='Approved').order_by('date', 'start_time')
        
        for slot in upcoming_appointments:
            confirmed_appointment = slot.slots.filter(status='Confirmed').first()
            slot.confirmed_appointment = confirmed_appointment

            if confirmed_appointment:
                patient_info = PatientInfo.objects.filter(appointment=confirmed_appointment).first()
                slot.patient_info = patient_info
                
                if patient_info:
                    patient_attachments = PatientAttachments.objects.filter(patient_info=patient_info)
                    slot.patient_attachments = patient_attachments
                    
        context['today_appointments'] = upcoming_appointments
        
        return context
    
    
# Prescription page view
class PrescriptionPageView(DoctorLoginRequiredMixin, TemplateView):
    template_name = 'prescription.html' 
    
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        doctor = get_object_or_404(DoctorProfile, user=self.request.user)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        current_date, current_time_obj = get_india_timezone()
        
        attended_patients = AppointmentSlot.objects.filter(doctor=doctor, is_booked=True, slots__status='Confirmed', 
                                                           room_id__isnull=False).exclude(slot__prescription_text__isnull=False)
        
        for appointment_slot in attended_patients:
            appointment_requests = appointment_slot.slots.all()
            confirmed_appointment_request = appointment_requests.filter(status='Confirmed').first()
            
            if confirmed_appointment_request: 
                patient = confirmed_appointment_request.patient_info 
                Prescription.objects.get_or_create(patient=patient, doctor=doctor, slot=appointment_slot, status='Pending')

        prescriptions = Prescription.objects.filter(doctor=doctor, date__gte=thirty_days_ago).filter(
            Q(slot__date__lt=current_date) | (Q(slot__date=current_date) & Q(slot__start_time__lte=current_time_obj))
            ).prefetch_related('patient', 'slot').order_by('-slot__date')

        if query:
            prescriptions = prescriptions.filter(
                Q(patient__patient_name__icontains=query) | Q(status__icontains=query) | Q(slot__date__icontains=query)
            )
            
        return self.render_to_response({'prescriptions': prescriptions, 'query': query})


# Prescription detail page view
class PrescriptionDetailPageView(DoctorLoginRequiredMixin, TemplateView):
    template_name = 'prescription_detail.html'
    
    def dispatch(self, request, *args, **kwargs):
        token = request.GET.get('token')
        if token:
            user_data = validate_jwt_token(token)
            if user_data:
                user = CustomUser.objects.filter(id=user_data['user_id']).first()
                if user:
                    login(request, user)
                else:
                    logout(request)
                    return redirect('sign_in')
            else:
                logout(request)
                return redirect('sign_in')
        elif not request.user.is_authenticated:
            return redirect('sign_in')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_meeting_id(self):
        meeting_id = self.request.GET.get('meeting_id') 
        return meeting_id
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting_id = self.kwargs.get('meeting_id')
        
        if not meeting_id:
            meeting_id = self.get_meeting_id()
        user = self.request.user
        doctor = get_object_or_404(DoctorProfile, user=user)

        appointment_slot = AppointmentSlot.objects.get(is_booked=True, room_id=meeting_id)
        request_instance = appointment_slot.slots.get(status='Confirmed', doctor=doctor)
        patient = request_instance.patient_info
        
        prescription, created = Prescription.objects.get_or_create(patient=patient, doctor=doctor, slot=appointment_slot)
        form = PrescriptionForm(instance=prescription)
        
        context['form'] = form
        context['patient'] = patient
        context['meeting_id'] = meeting_id
        
        return context
    
    def post(self, request, *args, **kwargs):
        meeting_id = request.POST.get('meeting_id')
        user = self.request.user
        doctor = get_object_or_404(DoctorProfile, user=user)

        appointment_slot = AppointmentSlot.objects.get(is_booked=True, room_id=meeting_id)
        request_instance = appointment_slot.slots.get(status='Confirmed', doctor=doctor)
        patient = request_instance.patient_info

        prescription = get_object_or_404(Prescription, patient=patient, doctor=doctor, slot=appointment_slot)

        form = PrescriptionForm(request.POST, instance=prescription)

        if form.is_valid():
            prescription_text = form.cleaned_data.get('prescription_text', '')
            stripped_text = strip_tags(prescription_text).strip()
            stripped_text = re.sub(r'(&nbsp;|\s)+', '', stripped_text)
            
            if not stripped_text:
                messages.error(request, "Prescription cannot be empty")
                return self.render_to_response(self.get_context_data(form=form))
            
            prescription.status = 'Approved'
            form.save()

            return redirect('prescription_page')

        messages.error(request, "An error occurred. Please try again")
        return self.render_to_response(self.get_context_data(form=form))
    
    

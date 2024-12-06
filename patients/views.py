from collections import defaultdict
from datetime import datetime, timedelta
import json
from django.utils.timezone import now, localtime
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
from patients.models import DoctorProfile, AppointmentSlot, AppointmentRequest, PatientInfo, PatientAttachments, Notification
from accounts.models import UserProfile, CustomUser
from doctors.models import Prescription
from django.utils.timezone import now
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from zoneinfo import ZoneInfo
from patients.utils import get_india_timezone
from django.contrib.auth import login, logout
from accounts.utils import validate_jwt_token
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from accounts.mixins import PatientLoginRequiredMixin


# Home page view
class HomeView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'home.html'
    
    def dispatch(self, request, *args, **kwargs):
        token = request.GET.get('token')
        if token:
            user_data = validate_jwt_token(token)
            if user_data:
                user = CustomUser.objects.filter(pk=user_data['user_id']).first()
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_date, current_time_obj = get_india_timezone()
        
        doctors = DoctorProfile.objects.filter(is_active=True).select_related('specialization').order_by('?')
        appointments = AppointmentRequest.objects.filter(user=self.request.user, slot__is_available=True, slot__is_booked=True, status="Confirmed").filter(
            Q(slot__date=current_date, slot__end_time__gte=current_time_obj) | Q(slot__date__gt=current_date)
        ).exclude(slot__slot__patient__user=self.request.user, slot__slot__status='Approved').order_by('slot__date', 'slot__start_time')
                
        notification_count = Notification.objects.filter(user=self.request.user, is_read=False).count()
        
        context['doctors'] = doctors
        context['appointments'] = appointments
        context['notification_count'] = notification_count

        return context


# Doctors list page view
class DoctorsListView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'doctors_list.html'
    
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        doctors = DoctorProfile.objects.filter(is_active=True).select_related('specialization').order_by('?')
        
        if query:
            doctors = doctors.filter(
                Q(full_name__icontains=query) | Q(specialization__name__icontains=query)
            )
        
        return self.render_to_response({'doctors': doctors, 'query': query})


# Doctor profile page view
class DoctorProfileView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'doctor_profile.html'
    
    def get_object(self, doctor_id):
        return get_object_or_404(DoctorProfile.objects.prefetch_related('experiences'), id=doctor_id)
        
    def get(self, request, *args, **kwargs):
        doctor_id = kwargs.get('doctor_id')
        doctor = self.get_object(doctor_id)
        
        return self.render_to_response({'doctor': doctor})
        
        
# To request an appointment
class RequestAppointmentView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'request_appointment.html'
    
    def get_object(self, doctor_id):
        return get_object_or_404(DoctorProfile, id=doctor_id)
    
    def get(self, request, *args, **kwargs):
        doctor_id = kwargs.get('doctor_id')
        doctor = self.get_object(doctor_id)
        
        current_date, current_time_obj = get_india_timezone()
        
        all_slots = AppointmentSlot.objects.filter(doctor=doctor, is_available=True
        ).filter(
            Q(date=current_date, start_time__gte=current_time_obj) | Q(date__gt=current_date)
        ).order_by('date', 'start_time')
        
        unique_dates = []
        for slot in all_slots:
            if len(unique_dates) < 6 and slot.date not in unique_dates:
                unique_dates.append(slot.date)
        
        filtered_slots = all_slots.filter(date__in=unique_dates)
        
        available_slots = defaultdict(lambda: defaultdict(lambda: {'morning': [], 'afternoon': [], 'evening': []}))
        
        for slot in filtered_slots:
            month = slot.date.strftime('%B')  
            year = slot.date.year
            day_number = slot.date.day
            day_name = slot.date.strftime('%a')
            
            time_label = ''
            if slot.start_time < timezone.datetime.strptime('12:00 PM', '%I:%M %p').time():
                time_label = 'morning'
            elif slot.start_time < timezone.datetime.strptime('05:00 PM', '%I:%M %p').time():
                time_label = 'afternoon'
            else:
                time_label = 'evening'
            
            slot_time = slot.start_time.strftime('%I:%M %p')
            available_slots[month][(day_number, day_name, year)][time_label].append({'time': slot_time, 'is_booked': slot.is_booked})
        
        filtered_slots = {
            month: {
                day: {time: times for time, times in time_slots.items() if times}
                for day, time_slots in days.items()
            }
            for month, days in available_slots.items()
        }
        
        js_slots = {
            month: {
                f"{day[0]}-{day[1]}-{day[2]}": {time: times for time, times in time_slots.items() if times}
                for day, time_slots in days.items()
            }
            for month, days in available_slots.items()
        }
        
        first_day_slots = None
        for month, days in filtered_slots.items():
            for day, times in days.items():
                first_day_slots = times
                break 
            if first_day_slots:
                break
        
        return self.render_to_response({'doctor': doctor, 'filtered_slots':filtered_slots, 'first_day_slots':first_day_slots, 'js_slots':json.dumps(js_slots)})
    
    def post(self, request, *args, **kwargs):
        date_str = request.POST.get('btnradio')
        time_str = request.POST.get('btnradio1')
        doctor_id = request.POST.get('doctor_id')
        
        day_str, month_str, year_str = date_str.split('-')
        day = int(day_str.strip())
        month = datetime.strptime(month_str.strip(), "%B").month
        year = int(year_str.strip())
        
        date_obj = datetime(year, month, day).date() 
        time_obj = datetime.strptime(time_str, "%I:%M %p").time()
        
        doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        slot = AppointmentSlot.objects.filter(doctor=doctor, date=date_obj, start_time=time_obj).first()
        
        if slot.is_booked==True:
            messages.info(request, 'Slot is already booked. Please choose another slot!')
            return redirect('request_appointment', doctor_id=doctor.id)
        
        return redirect('book_appointment', doctor_id=doctor.id, slot_id=slot.id)
            

# To book an appointment
class BookAppointmentView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'book_appointment.html'
    
    def get(self, request, *args, **kwargs):
        doctor_id = kwargs.get('doctor_id')
        slot_id = kwargs.get('slot_id')
        doctor = get_object_or_404(DoctorProfile.objects.select_related('specialization'), id=doctor_id)
        slot = get_object_or_404(AppointmentSlot, id=slot_id)
        
        return self.render_to_response({'doctor': doctor, 'slot': slot})
    
    def post(self, request, *args, **kwargs):
        doctor_id = request.POST.get('doctor_id')
        slot_id = request.POST.get('slot_id')
        doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        slot = get_object_or_404(AppointmentSlot, id=slot_id)
        
        appointment, _ = AppointmentRequest.objects.get_or_create(user=self.request.user, doctor=doctor, slot=slot)

        return redirect('patient_info', appointment_id=appointment.id, doctor_id = doctor.id)
    

# To add patient information
class PatientInfoView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'patient_info.html'
    
    def get(self, request, *args, **kwargs):
        doctor_id = kwargs.get('doctor_id')
        appointment_id = kwargs.get('appointment_id')
        doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        appointment = get_object_or_404(AppointmentRequest, id=appointment_id)
        
        return self.render_to_response({'doctor': doctor, 'appointment': appointment})
    
    def post(self, request, *args, **kwargs):
        patient_name = request.POST.get('patient-name')
        patient_address = request.POST.get('patient-address')
        patient_age = request.POST.get('patient-age')
        patient_gender = request.POST.get('gender')
        patient_mobile = request.POST.get('patient-mobile')
        patient_weight = request.POST.get('patient-weight')
        patient_description = request.POST.get('patient-description')
        attachments = request.FILES.getlist('attachments')
        appointment_id = request.POST.get('appointment-id')
        doctor_id = request.POST.get('doctor-id')
        
        appointment = get_object_or_404(AppointmentRequest, id=appointment_id)
        doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        
        if not patient_name or not patient_age or not patient_gender or not patient_mobile:
            messages.error(request, "Patient details are missing or incomplete")
            return self.render_to_response({'doctor': doctor, 'appointment': appointment, 'patient_name': patient_name, 'patient_gender': patient_gender,
                                            'patient_address': patient_address, 'patient_age': patient_age, 'patient_mobile': patient_mobile,
                                            'patient_weight': patient_weight, 'patient_description': patient_description})
        
        patient_info, created = PatientInfo.objects.update_or_create(user=self.request.user, appointment=appointment,
            defaults = {
                'patient_name': patient_name, 'address': patient_address, 'mobile': patient_mobile, 'age': patient_age,
                'gender': patient_gender, 'weight': patient_weight, 'description': patient_description
            }
        )
        
        PatientAttachments.objects.filter(patient_info=patient_info).delete()
        
        for attachment in attachments:
            if attachment.content_type.startswith('image/'):
                filetype = 'image'
            elif attachment.content_type.startswith('application/pdf'):
                filetype = 'document'
            else:
                filetype = 'other'
                
            PatientAttachments.objects.create(patient_info=patient_info, file=attachment, file_type=filetype)

        appointment.status = 'Confirmed'
        appointment.save()
        appointment.slot.is_booked = True
        appointment.slot.save()
        
        return redirect('home')
        
    
# Appointment page view
class AppointmentPageView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'appointment_page.html'
    
    def get(self, request, *args, **kwargs):
        doctors = DoctorProfile.objects.filter(is_active=True).select_related('specialization').order_by('?')
        
        return self.render_to_response({'doctors': doctors})


# Profile page view
class ProfilePageView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'my_profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)     
        user_profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        
        context['user_profile'] = user_profile
        
        return context
    
    
# Appointments page view
class AppointmentsPageView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'my_appointment.html'
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_date, current_time_obj = get_india_timezone()
        
        upcoming_appointments = AppointmentRequest.objects.filter(user=self.request.user, slot__is_available=True, slot__is_booked=True, status="Confirmed").filter(
            Q(slot__date=current_date, slot__end_time__gte=current_time_obj) | Q(slot__date__gt=current_date)
        ).exclude(slot__slot__patient__user=self.request.user, slot__slot__status='Approved').order_by('slot__date', 'slot__start_time')
        
        past_appointments = AppointmentRequest.objects.filter(user=self.request.user, slot__is_available=True, slot__is_booked=True, status="Confirmed").filter(
            Q(slot__date__lt=current_date) | 
            Q(slot__date=current_date, slot__end_time__lt=current_time_obj) | 
            Q(
                slot__date=current_date,
                slot__start_time__lt=current_time_obj,
                slot__end_time__gte=current_time_obj,
                slot__slot__status='Approved'
            )
        ).order_by('-slot__date', '-slot__end_time')
        
        context['upcoming_appointments'] = upcoming_appointments
        context['past_appointments'] = past_appointments
        
        return context
    
    
# Appointment detail page view
class AppointmentDetailView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'appointment_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appointment_id = kwargs.get('appointment_id')
        india_timezone = ZoneInfo('Asia/Kolkata')
        current_time = now().astimezone(india_timezone)
        appointment = get_object_or_404(AppointmentRequest.objects.select_related('slot', 'patient_info'), id=appointment_id)
        
        appointment_start_datetime = datetime.combine(appointment.slot.date, appointment.slot.start_time, tzinfo=india_timezone)
        appointment_end_datetime = datetime.combine(appointment.slot.date, appointment.slot.end_time, tzinfo=india_timezone)
        
        is_past = (
            appointment_end_datetime < current_time or
            (
                appointment_start_datetime < current_time <= appointment_end_datetime and
                appointment.slot.slot.status == 'Approved'  
            )
        )
        context['appointment'] = appointment
        context['is_past'] = is_past
        
        return context
    

# Video page view
class VideoPageView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'video.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctors = DoctorProfile.objects.filter(is_active=True).select_related('specialization').order_by('?')
        context['doctors'] = doctors
        return context
        
        
# Profile update page view
class ProfileUpdateView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'edit_profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile_id = kwargs.get('id')
        user_profile = get_object_or_404(UserProfile.objects.select_related('user'), id=user_profile_id)

        context['user_profile'] = user_profile
        
        return context
    
    def post(self, request, *args, **kwargs):
        user_profile_id = request.POST.get('user_profile_id')
        profile_picture = request.FILES.get('profile_picture')
        name = request.POST.get('name')
        email = request.POST.get('email')
        gender = request.POST.get('gender')
        dob = request.POST.get('dob')
        country = request.POST.get('country') 
        countryCode = request.POST.get('country_code')
        mobile = request.POST.get('mobile')
        remove_profile_picture = request.POST.get('remove_profile_picture') == 'true'
        
        user_profile = get_object_or_404(UserProfile.objects.select_related('user'), id=user_profile_id)
        user = user_profile.user
        
        user.name = name
        user.email = email
        user.country = country
        user.countryCode = countryCode
        user.mobile = mobile
        user.save()
    
        user_profile.gender = gender
        if dob:
            user_profile.dob = dob
        else:
            user_profile.dob = None
            
        if remove_profile_picture:
            user_profile.profile_image = None
        elif profile_picture:
            user_profile.profile_image = profile_picture
        
        user_profile.save()

        return redirect('profile_page')
      
                 
# To show notifications
class NotificationPatientView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'notification_patient.html'
    
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
    

# Prescription view page
class PrescriptionView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'prescription_view.html'
    
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        prescriptions = Prescription.objects.filter(patient__user=self.request.user, status='Approved').prefetch_related('doctor', 'slot').order_by('-slot__date')
        
        if query:
            prescriptions = prescriptions.filter(
                Q(patient__patient_name__icontains=query) | Q(doctor__full_name__icontains=query) | Q(slot__date__icontains=query)
            )
            
        return self.render_to_response({'prescriptions': prescriptions, 'query': query})
    
    
# Prescription patient page view
class PrescriptionPatientView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'prescription_patient_view.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prescription_id = kwargs.get('prescription_id')
        prescription = get_object_or_404(Prescription, id=prescription_id)
        
        context['prescription'] = prescription
        context['for_pdf'] = True
        
        return context
        

# Prescription download view
class DownloadPrescriptionView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'prescription_patient_view.html'
    
    def get(self, request, *args, **kwargs):
        prescription_id = kwargs.get('prescription_id')
        prescription = get_object_or_404(Prescription, id=prescription_id)
        
        html_content = render_to_string(self.template_name, {'prescription': prescription})
        pdf = HTML(string=html_content).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="prescription_{prescription.patient.patient_name}_{prescription.slot.date}.pdf"'
        
        return response
        

# Hair Analyzer Page view
class HairAnalyzerPageView(PatientLoginRequiredMixin, TemplateView):
    template_name = 'hair_analyzer.html'
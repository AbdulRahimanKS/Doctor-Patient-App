from django.urls import path
from patients.views import HomeView, DoctorsListView, DoctorProfileView, RequestAppointmentView, BookAppointmentView, PatientInfoView, AppointmentPageView, ProfilePageView, ProfileUpdateView, AppointmentsPageView, AppointmentDetailView, VideoPageView, NotificationPatientView


urlpatterns = [
    path('home/', HomeView.as_view(), name='home'),
    path('doctors_list/', DoctorsListView.as_view(), name='doctors_list'),
    path('doctor_profile/<int:doctor_id>/', DoctorProfileView.as_view(), name='doctor_profile'),
    path('request_appointment/<int:doctor_id>/', RequestAppointmentView.as_view(), name='request_appointment'),
    path('book_appointment/<int:doctor_id>/<int:slot_id>/', BookAppointmentView.as_view(), name='book_appointment'),
    path('patient_info/<int:doctor_id>/<int:appointment_id>/', PatientInfoView.as_view(), name='patient_info'),
    path('appointment_page/', AppointmentPageView.as_view(), name='appointment_page'),
    path('profile_page/', ProfilePageView.as_view(), name='profile_page'),
    path('profile_update/<int:id>/', ProfileUpdateView.as_view(), name='profile_update'),
    path('appointments_page/', AppointmentsPageView.as_view(), name='appointments_page'),
    path('appointment_detail/<int:appointment_id>/', AppointmentDetailView.as_view(), name='appointment_detail'),
    path('video_page/', VideoPageView.as_view(), name='video_page'),
    path('notification_patient_view/', NotificationPatientView.as_view(), name='notification_patient_view'),
]


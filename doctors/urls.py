from django.urls import path
from doctors.views import DoctorHomeView, SlotAddView, SlotListView, SlotStartMeeting, DownloadAttachmentsView, NotificationDoctorView, NotificationsReadView, DoctorProfilePageView, DoctorProfileEditView, GetSpecializationsView, DoctorVideoPageView


urlpatterns = [
    path('doctor_home/', DoctorHomeView.as_view(), name='doctor_home'),
    path('add_slot/', SlotAddView.as_view(), name='add_slot'),    
    path('list_slots/', SlotListView.as_view(), name='list_slots'),
    path('start_meeting/', SlotStartMeeting.as_view(), name='start_meeting'), 
    path('download_attachments/<int:patient_id>/', DownloadAttachmentsView.as_view(), name='download_attachments'),
    path('notification_doctor_view/', NotificationDoctorView.as_view(), name='notification_doctor_view'),
    path('read_notifications/', NotificationsReadView.as_view(), name='read_notifications'),
    path('doctor_profile_page/', DoctorProfilePageView.as_view(), name='doctor_profile_page'),
    path('doctor_profile_edit/<int:id>/', DoctorProfileEditView.as_view(), name='doctor_profile_edit'),
    path('get_specializations/<int:category_id>/', GetSpecializationsView.as_view(), name='get_specializations'),
    path('doctor_video_page/', DoctorVideoPageView.as_view(), name='doctor_video_page'),
]


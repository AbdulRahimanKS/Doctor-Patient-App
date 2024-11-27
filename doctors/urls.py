from django.urls import path
from doctors.views import DoctorHomeView, SlotAddView, SlotListView, SlotStartMeeting, DownloadAttachmentsView, NotificationPageView


urlpatterns = [
    path('doctor_home/', DoctorHomeView.as_view(), name='doctor_home'),
    path('add_slot/', SlotAddView.as_view(), name='add_slot'),    
    path('list_slots/', SlotListView.as_view(), name='list_slots'),
    path('start_meeting/', SlotStartMeeting.as_view(), name='start_meeting'), 
    path('download_attachments/<int:patient_id>/', DownloadAttachmentsView.as_view(), name='download_attachments'),
    path('notification_view/', NotificationPageView.as_view(), name='notification_view'),
]


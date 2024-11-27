from django.contrib import admin
from patients.models import DoctorProfile, Category, Specialization, DoctorExperiences, AppointmentRequest, AppointmentSlot, PatientInfo, PatientAttachments, Banner, Notification

class DoctorInfoAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'specialization', 'user__email', 'user__mobile', 'is_active', 'date_joined', 'date_updated')
    search_fields = ('first_name', 'last_name', 'user__email', 'user__mobile', 'specialization')
    list_filter = ('specialization', 'is_active')
    readonly_fields = ('date_joined', 'date_updated')
    ordering = ('-date_joined',)
    
class AppointmentSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'is_available', 'is_booked', 'in_progress')
    list_filter = ('doctor', 'date', 'is_booked')
    list_editable = ('is_available', 'is_booked', 'in_progress')
    search_fields = ('doctor__full_name', 'is_available', 'is_booked', 'in_progress')
    
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'banner_type', 'is_active', 'created_at')
    list_filter = ('banner_type', 'is_active', 'created_at')
    list_editable = ('is_active',)
    search_fields = ('title',)

admin.site.register(DoctorProfile, DoctorInfoAdmin)
admin.site.register(AppointmentSlot, AppointmentSlotAdmin)
admin.site.register(Banner, BannerAdmin)
admin.site.register([Category, Specialization, DoctorExperiences, AppointmentRequest, PatientInfo, PatientAttachments, Notification])


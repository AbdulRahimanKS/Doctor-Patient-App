from django.db import models
from accounts.models import CustomUser
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
    

class Specialization(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='specializations')
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class DoctorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='doctor_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, default='')
    full_name = models.CharField(max_length=100, editable=False)
    about = models.TextField()
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    dob = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='doctor_images/', null=True, blank=True)
    specialization = models.OneToOneField(Specialization, on_delete=models.CASCADE)
    experience_years = models.PositiveIntegerField(default=0)
    qualification = models.CharField(max_length=150)
    college = models.CharField(max_length=150)
    clinic_address = models.TextField(null=True, blank=True)
    consultation_fee = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        self.full_name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.full_name} - {self.specialization.name}"
    
    
class DoctorExperiences(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='experiences')  
    hospital = models.CharField(max_length=150) 
    designation = models.CharField(max_length=150)
    department = models.CharField(max_length=150)
    employed_from = models.DateField(null=True, blank=True)
    employed_to = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.hospital} - {self.designation} ({self.department})"


class AppointmentSlot(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="available_slots")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    is_booked = models.BooleanField(default=False)
    in_progress = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    room_id = models.CharField(max_length=255, blank=True, null=True)

    @property
    def month(self):
        return self.date.strftime('%B')

    def __str__(self):
        return f"{self.doctor.full_name} - {self.month} {self.date} {self.start_time.strftime('%I:%M %p')} to {self.end_time.strftime('%I:%M %p')}"

    class Meta:
        unique_together = ('doctor', 'date', 'start_time')


class AppointmentRequest(models.Model):
    appointment_status = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True)
    slot = models.ForeignKey(AppointmentSlot, on_delete=models.SET_NULL, null=True)
    date_requested = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, choices=appointment_status, default='Pending')

    def __str__(self):
        doctor_name = self.doctor.full_name if self.doctor else "Unknown Doctor"
        slot_date = self.slot.date.strftime('%A, %b %d, %Y') if self.slot else "Unknown Date"
        slot_time = self.slot.start_time.strftime('%I:%M %p') if self.slot else "Unknown Time"
        return f"Appointment request for {doctor_name} on {slot_date} at {slot_time}"
    
    class Meta:
        unique_together = ('user', 'doctor', 'slot')
        

class PatientInfo(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='patient_info')
    appointment = models.OneToOneField(AppointmentRequest, on_delete=models.CASCADE, related_name='patient_info')
    patient_name = models.CharField(max_length=150)
    address = models.TextField(default="")
    mobile = models.CharField(max_length=15)
    age = models.PositiveIntegerField()
    weight = models.CharField(max_length=10, blank=True, null=True)
    description = models.TextField(default="")
    
    def __str__(self):
        return f"{self.patient_name} - Appointment on {self.appointment.slot.date} {self.appointment.slot.start_time}"
    
    
class PatientAttachments(models.Model):
    patient_info = models.ForeignKey(PatientInfo, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="patient_attachments/%Y/%m/%d/")
    file_type = models.CharField(max_length=50, blank=True, null=True) 
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attachment for {self.patient_info.patient_name} - {self.file.name}"


class Banner(models.Model):
    BANNER_TYPES = (
        ('doctor_profile', 'Doctor Profile'),
        ('doctor_list', 'All Doctors'),
        ('custom_url', 'Custom URL'),
    )
    
    title = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="banners/")
    banner_type = models.CharField(max_length=50, choices=BANNER_TYPES, default='custom_url')
    doctor = models.ForeignKey('DoctorProfile', null=True, blank=True, on_delete=models.SET_NULL, related_name='banners')
    custom_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_redirect_url(self):
        if self.banner_type == 'doctor_profile' and self.doctor:
            return reverse('doctor_profile', kwargs={'doctor_id': self.doctor.pk})
        elif self.banner_type == 'doctor_list':
            return reverse('doctors_list')
        elif self.banner_type == 'custom_url' and self.custom_url:
            return self.custom_url
        return reverse('home')

    def __str__(self):
        return self.title or f"Banner {self.id}"
    

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'Notification for {self.user.name}: {self.message}'
    

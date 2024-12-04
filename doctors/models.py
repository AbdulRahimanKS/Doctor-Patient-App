from django.db import models
from patients.models import PatientInfo, DoctorProfile, AppointmentSlot
from django_ckeditor_5.fields import CKEditor5Field


class Prescription(models.Model):
    patient = models.OneToOneField(PatientInfo, on_delete=models.CASCADE, related_name='patient')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='doctor')
    slot = models.ForeignKey(AppointmentSlot, on_delete=models.SET_NULL, null=True, related_name='slot')
    prescription_text = CKEditor5Field(config_name='extends')
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved')], default='Pending')

    def __str__(self):
        return f"Prescription for {self.patient.patient_name} by {self.doctor.full_name}"

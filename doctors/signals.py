from django.db.models.signals import post_save
from patients.models import Notification
from doctors.models import Prescription
from django.dispatch import receiver


@receiver(post_save, sender=Prescription)
def notify_prescription_approval(sender, instance, created, **kwargs):
    if instance.status == 'Approved':
        doctor_message = (
            f"Prescription for {instance.patient.patient_name} has been approved."
        )
        patient_message = (
            f"Your prescription from {instance.doctor.full_name} has been approved."
            f" You can now view the prescription details."
        )
        Notification.objects.create(user=instance.doctor.user, message=doctor_message)
        Notification.objects.create(user=instance.patient.user, message=patient_message)
        
        
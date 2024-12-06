from django.db.models.signals import post_save
from patients.models import Notification, AppointmentSlot
from django.dispatch import receiver


@receiver(post_save, sender=AppointmentSlot)
def notify_slot_booking(sender, instance, created, **kwargs):
    if instance.is_booked and not instance.room_id:
        doctor_message = (
            f"A new appointment has been booked with you on {instance.date} "
            f"at {instance.start_time}."
        )
        patient_message = (
            f"Your appointment with Dr. {instance.doctor.full_name} has been successfully booked "
            f"on {instance.date} at {instance.start_time}."
        )
        Notification.objects.create(user=instance.doctor.user, message=doctor_message)
        Notification.objects.create(user=instance.slots.first().user, message=patient_message)
        
        
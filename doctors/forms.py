from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from doctors.models import Prescription


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ("prescription_text",)
        widgets = {
            "prescription_text": CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"}, config_name="extends"
            )
        }


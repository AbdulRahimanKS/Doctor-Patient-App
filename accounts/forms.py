from django import forms
from django.contrib.auth.hashers import make_password
from .models import CustomUser

class CustomUserAdminForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = '__all__'

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password.startswith("pbkdf2_"):
            return make_password(password)
        return password

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class DoctorLoginRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='Doctor').exists():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PatientLoginRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='Patient').exists():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
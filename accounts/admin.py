from django.contrib import admin
from accounts.models import CustomUser, UserProfile
from accounts.forms import CustomUserAdminForm


class CustomUserAdmin(admin.ModelAdmin):
    form = CustomUserAdminForm
    list_display = ('name', 'email', 'mobile', 'is_staff', 'user_type')
    search_fields = ('name', 'email', 'mobile')
    list_filter = ('is_staff', 'is_active', 'user_type')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserProfile)


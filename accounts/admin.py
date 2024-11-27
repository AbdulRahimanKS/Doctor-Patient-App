from django.contrib import admin
from accounts.models import CustomUser, UserProfile

admin.site.register([CustomUser, UserProfile])

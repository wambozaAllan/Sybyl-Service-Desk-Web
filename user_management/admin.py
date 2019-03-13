from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import User, UserGroup

admin.site.register(UserGroup)

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ['first_name', 'last_name', 'gender', 'company'
              , 'branch', 'department', 'user_group', 'category'
              , 'username', 'password',]
admin.site.register(User, CustomUserAdmin)
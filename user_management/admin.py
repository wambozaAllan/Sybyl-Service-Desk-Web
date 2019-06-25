from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import User


class CustomUserAdmin(UserAdmin):

    model = User

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'first_name',
                           'last_name', 'is_active', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {

            'classes': ('wide',),

            'fields': ('email', 'password1', 'password2'),

        }),
    )

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff',)

    list_filter = ('is_superuser', 'is_active', 'groups',)

    search_fields = ('email', 'first_name', 'last_name',)

    ordering = ('email',)


admin.site.register(User, CustomUserAdmin)

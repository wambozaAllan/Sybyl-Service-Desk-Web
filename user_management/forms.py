from .models import User, UserGroup, UserTeamMember
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = User
        fields = ['first_name', 'last_name', 'gender', 'company'
              , 'branch', 'department', 'user_group', 'category'
              , 'username', 'email']

class CreateUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'gender', 'company'
              , 'branch', 'department', 'user_group', 'category'
              , 'username', 'password', 'email','is_superuser','is_staff', 'is_active',]
        widgets = {
            'password': forms.PasswordInput()
        }

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'gender', 'company'
              , 'branch', 'department', 'user_group', 'category'
              , 'username', 'password', 'email','is_superuser','is_staff', 'is_active',]

class UserGroupForm(forms.ModelForm):

    class Meta:
        model = UserGroup
        fields = ('name',)

class UserTeamMeamberForm(forms.ModelForm):

    class Meta:
        model = UserTeamMember
        fields = ('user','user_team')
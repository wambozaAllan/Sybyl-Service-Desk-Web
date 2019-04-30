from .models import User, UserTeamMember, GroupExtend
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from django.forms.models import modelformset_factory

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = User
        fields = ['first_name', 'last_name', 'gender', 'company'
            , 'department', 'category'
            , 'username', 'email']


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'gender', 'company'
                  , 'branch', 'department', 'group', 'category'
                  , 'username', 'password', 'email', 'is_superuser', 'is_staff', 'is_active',)
        widgets = {'password': forms.PasswordInput()}


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'gender', 'company'
            , 'branch', 'department', 'group', 'category'
            , 'username', 'password', 'email', 'is_superuser', 'is_staff', 'is_active', ]


class GroupExtendForm(forms.ModelForm):
    class Meta:
        model = GroupExtend
        fields = ('company', 'description', 'active')


class UserTeamMeamberForm(forms.ModelForm):
    class Meta:
        model = UserTeamMember
        fields = ('user', 'user_team')

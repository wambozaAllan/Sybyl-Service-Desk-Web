from django.db import models
from django.contrib.auth.models import AbstractBaseUser, Group, Permission, PermissionsMixin
from django.utils import timezone
from datetime import datetime
from django.contrib.sessions.models import Session

from company_management.models import Company, Branch, Department
from django.http import HttpRequest
from .managers import UserManager

# CustomUser
class User(AbstractBaseUser, PermissionsMixin):
    groups = models.ManyToManyField(Group, related_name='groups')
    company = models.ForeignKey(Company, default=1, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    created_by = models.CharField(max_length=100)
    modified_by = models.CharField(max_length=100)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)
    GENDER_CHOICES = (('Male', 'Male'), ('Female', 'Female'))
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, default='Male')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)

    city = models.CharField(max_length=100, null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    secondary_email = models.EmailField(blank=True, null=True)
    user_type = models.CharField(max_length=100, null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    EMAIL_FIELD = 'email'


    def __str__(self):
        return self.first_name + ' ' + self.last_name

    class Meta():
        db_table = 'user_management_user'

    # @property
    # def user_email(self):
    #     return self.email


class UserTeam(models.Model):
    name = models.CharField(max_length=100, default='TeamName')
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# UserTeamMember
class UserTeamMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_team = models.ForeignKey(UserTeam, on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)


# UserPhoneContact
class UserPhoneContact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_contact = models.CharField(max_length=13)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.phone_contact


# UserEmailAddress
class UserEmailAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email_address = models.CharField(max_length=45)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)


class GroupExtend(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def get_permissions_count(self):
        return Permission.objects.filter(group=self.group).count()

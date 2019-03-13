from django.contrib import admin
from . models import Branch, CompanyCategory, Department

admin.site.register(Department)
admin.site.register(Branch)
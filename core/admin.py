from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from company_management.models import *
from user_management.models import *
# from . models import Privilege, Section, Submenu, Menu

from django.utils.translation import ugettext_lazy as _

#admin.site.register(User, UserAdmin)
# admin.site.register(Company)
# admin.site.register(Submenu)
# admin.site.register(Section)
# admin.site.register(Privilege)
# admin.site.register(Menu)

admin.site.site_header = _("Sybyl Administration Portal")
admin.site.site_title = _("Admin")
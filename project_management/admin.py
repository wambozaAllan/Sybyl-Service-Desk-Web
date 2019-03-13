from django.contrib import admin
from .models import Project, ProjectTeam, ProjectTeamMember

# Register your models here.
admin.site.register(Project)
admin.site.register(ProjectTeam)
admin.site.register(ProjectTeamMember)

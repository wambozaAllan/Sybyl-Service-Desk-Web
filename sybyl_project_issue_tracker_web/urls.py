from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from project_management import tasks
from datetime import datetime
from background_task.models import Task
import pytz

urlpatterns = [
    path('', include('core.urls')),
    path('core/', include('core.urls')),
    path('userManagement/', include('user_management.urls')),
    path('companyManagement/', include('company_management.urls')),
    path('projectManagement/', include('project_management.urls')),
    path('chat/', include('chat.urls')),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

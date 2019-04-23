from django.urls import path
from . import views

urlpatterns = [
    path('', views.Login.as_view(),name='login'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'),
    path('signup/', views.SignUp.as_view(), name='signup'),
]

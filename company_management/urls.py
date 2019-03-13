from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListCompanies.as_view(), name='listCompanies'),
    path('addCompany/', views.AddCompany.as_view(), name='addCompany'),
    path('listCompanies/', views.ListCompanies.as_view(), name='listCompanies'),
    path('detailsCompany/<int:pk>/', views.DetailsCompany.as_view(), name='detailsCompany'),
    path('updateCompany/<int:pk>/', views.UpdateCompany.as_view(), name='updateCompany'),
    path('addDepartment/', views.AddDepartment.as_view(), name='addDepartment'),
    path('listDepartments/', views.ListDepartments.as_view(), name='listDepartments'),
    path('detailsDepartment/<int:pk>/', views.DetailsDepartment.as_view(), name='detailsDepartment'),
    path('updateDepartment/<int:pk>/', views.UpdateDepartment.as_view(), name='updateDepartment'),
    path('addBranch/', views.AddBranch.as_view(), name='addBranch'),
    path('listBranches/', views.ListBranches.as_view(), name='listBranches'),
    path('detailsBranch/<int:pk>/', views.DetailsBranch.as_view(), name='detailsBranch'),
    path('updateBranch/<int:pk>/', views.UpdateBranch.as_view(), name='updateBranch'),
]

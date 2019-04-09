from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListCompanies.as_view(), name='listCompanies'),
    path('addCompany/', views.AddCompany.as_view(), name='addCompany'),
    path('listCompanies/', views.ListCompanies.as_view(), name='listCompanies'),
    path('detailsCompany/<int:pk>/', views.DetailsCompany.as_view(), name='detailsCompany'),
    path('updateCompany/<int:pk>/', views.UpdateCompany.as_view(), name='updateCompany'),
    path('addDepartment/', views.AddDepartment.as_view(), name='add-department'),
    path('listDepartments/', views.ListDepartments.as_view(), name='list-departments'),
    path('detailsDepartment/<int:pk>/', views.DetailsDepartment.as_view(), name='details-department'),
    path('updateDepartment/<int:pk>/', views.UpdateDepartment.as_view(), name='update-department'),
    path('addBranch/', views.AddBranch.as_view(), name='add-branch'),
    path('listBranches/', views.ListBranches.as_view(), name='list-branches'),
    path('detailsBranch/<int:pk>/', views.DetailsBranch.as_view(), name='details-branch'),
    path('updateBranch/<int:pk>/', views.UpdateBranch.as_view(), name='update-branch'),
    path('addBranchContact/', views.AddBranchContacts.as_view(), name='add-branch-contact'),
    path('listBranchContacts/', views.ListBranchContacts.as_view(), name='list-branch-contacts'),
    path('detailsBranchContact/<int:pk>/', views.DetailsBranchContact.as_view(), name='details-branch-contact'),
    path('updateBranchContact/<int:pk>/', views.UpdateBranchContact.as_view(), name='update-branch-contact'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListCompanies.as_view(), name='listCompanies'),
    path('addCompany/', views.AddCompany.as_view(), name='addCompany'),
    path('listCompanies/', views.ListCompanies.as_view(), name='listCompanies'),
    # path('detailsCompany/<int:pk>/', views.DetailsCompany.as_view(), name='detailsCompany'),
    path('updateCompany/<int:pk>/', views.UpdateCompany.as_view(), name='updateCompany'),
    path('companyBranchList/<int:pk>', views.companyBranchList.as_view(), name="companyBranchList"),
    path('validateCompanyName', views.validatCompanyName, name='validateCompanyName'),
    path('listCompanyBranches/<int:pk>/', views.ListCompanyBranches.as_view(), name='listCompanyBranches'),

    path('addDepartment/', views.AddDepartment.as_view(), name='addDepartment'),
    path('listDepartments/', views.ListDepartments.as_view(), name='listDepartments'),
    path('detailsDepartment/<int:pk>/', views.DetailsDepartment.as_view(), name='detailsDepartment'),
    path('updateDepartment/<int:pk>/', views.UpdateDepartment.as_view(), name='updateDepartment'),
    path('addBranch/', views.AddBranch.as_view(), name='addBranch'),
    path('listBranches/', views.ListBranches.as_view(), name='listBranches'),
    path('detailsBranch/<int:pk>/', views.DetailsBranch.as_view(), name='detailsBranch'),
    path('updateBranch/<int:pk>/', views.UpdateBranch.as_view(), name='updateBranch'),

    path('listDomains/', views.ListCompanyDomains.as_view(), name='listDomains'),
    path('addDomain/', views.AddCompanyDomain.as_view(), name='addDomain'),
    path('updateDomain/<int:pk>/', views.UpdateDomain.as_view(), name='updateDomain'),
    path('deleteDomain/<int:pk>', views.DeleteDomain.as_view(), name="deleteDomain"),
    path('companies/<int:pk>', views.DomainCompanyList.as_view(), name="companies"),
    path('validateDomainName', views.validateDomainName, name='validateDomainName'),

    path('listCategories/', views.ListCompanyCategories.as_view(), name='listCategories'),
    path('addCategory/', views.AddCompanyCategory.as_view(), name='addCategory'),
    path('updateCategory/<int:pk>/', views.UpdateCategory.as_view(), name='updateCategory'),
    path('deleteCategory/<int:pk>', views.DeleteCategory.as_view(), name="deleteCategory"),
    path('categoryCompany/<int:pk>', views.CompanyCategoryList.as_view(), name="categoryCompany"),
    path('validateCategoryName', views.validateCategoryName, name='validateCategoryName'),
]

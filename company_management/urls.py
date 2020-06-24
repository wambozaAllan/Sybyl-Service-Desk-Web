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
    path('saveCompany', views.save_company, name='saveCompany'),
    path('saveCompanyUpdate', views.save_company_update, name='saveCompanyUpdate'),

    path('addDepartment/', views.AddDepartment.as_view(), name='addDepartment'),
    path('listDepartments/', views.ListDepartments.as_view(), name='listDepartments'),
    path('detailsDepartment/<int:pk>/', views.DetailsDepartment.as_view(), name='detailsDepartment'),
    path('updateDepartment/<int:pk>/', views.UpdateDepartment.as_view(), name='updateDepartment'),

    path('addBranch/', views.create_branch, name='addBranch'),
    path('listBranches/', views.ListBranches.as_view(), name='listBranches'),
    path('detailsBranch/<int:pk>/', views.DetailsBranch.as_view(), name='detailsBranch'),
    path('updateBranch/<int:pk>/', views.branch_update, name='updateBranch'),

    path('addBranchContacts/', views.AddBranchContacts.as_view(), name='addBranchContacts'),
    path('listBranchContactaddCompanys/', views.ListBranchContacts.as_view(), name='listBranchContacts'),
    path('detailBranchContacts/<int:pk>/', views.DetailBranchContacts.as_view(), name='detailBranchContacts'),
    path('updateBranchContacts/<int:pk>/', views.UpdateBranchContacts.as_view(), name='updateBranchContacts'),

    path('addBranchEmails/', views.AddBranchEmails.as_view(), name='addBranchEmails'),
    path('listBranchEmails/', views.ListBranchEmails.as_view(), name='listBranchEmails'),
    path('detailBranchEmails/<int:pk>/', views.DetailBranchEmails.as_view(), name='detailBranchEmails'),
    path('updateBranchEmails/<int:pk>/', views.UpdateBranchEmails.as_view(), name='updateBranchEmails'),

    path('listDomains/', views.ListCompanyDomains.as_view(), name='listDomains'),
    path('addDomain/', views.AddCompanyDomain.as_view(), name='addDomain'),
    path('addDomain2/', views.add_select_company_domain, name='addDomains2'),
    path('updateDomain/<int:pk>/', views.UpdateDomain.as_view(), name='updateDomain'),
    path('deleteDomain/<int:pk>', views.DeleteDomain.as_view(), name="deleteDomain"),
    path('companies/<int:pk>', views.DomainCompanyList.as_view(), name="companies"),
    path('validateDomainName', views.validateDomainName, name='validateDomainName'),
    path('fetchDomainList/', views.fetch_domain_list, name='fetchDomainList'),

    path('listCategories/', views.ListCompanyCategories.as_view(), name='listCategories'),
    path('addCategory/', views.AddCompanyCategory.as_view(), name='addCategory'),
    path('updateCategory/<int:pk>/', views.UpdateCategory.as_view(), name='updateCategory'),
    path('deleteCategory/<int:pk>', views.DeleteCategory.as_view(), name="deleteCategory"),
    path('categoryCompany/<int:pk>', views.CompanyCategoryList.as_view(), name="categoryCompany"),
    path('validateCategoryName', views.validateCategoryName, name='validateCategoryName'),

    path('listSlaContracts/', views.customer_sla_list, name='listSlaContracts'),

    path('addSLA/', views.AddSla.as_view(), name='addSla'),
    path('saveSLA/', views.save_sla, name='saveSLA'),
    path('updateSLA/<int:pk>/', views.UpdateSLA.as_view(), name='updateSLA'),
    path('update2SLA/', views.save_sla_update, name='saveSLAupdate'),
]

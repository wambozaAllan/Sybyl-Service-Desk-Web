from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy

from .forms import CompanyForm, DepartmentForm

from .models import Company, Department, Branch, BranchContact, BranchPhoneContact

class AddCompany(CreateView):
    model = Company
    fields = ['name', 'category']
    template_name = 'company_management/addCompany.html'
    success_url = reverse_lazy('listCompanies')


# All companies list view
class ListCompanies(generic.ListView):
    template_name = 'company_management/listCompanies.html'
    context_object_name = 'all_companies'

    def get_queryset(self):
        return Company.objects.all()


# Detailed view of a specific company
class DetailsCompany(generic.DetailView):
    model = Company
    context_object_name = 'company'
    template_name = 'company_management/detailsCompany.html'


class UpdateCompany(UpdateView):
    model = Company
    fields = ['name', 'category']
    template_name = 'company_management/updateCompany.html'
    success_url = reverse_lazy('listCompanies')


# Adding departments view
class AddDepartment(CreateView):
    model = Department
    template_name = 'company_management/add_department.html'
    fields = ['name', 'company']
    success_url = reverse_lazy('list-departments')


# All departments list view
class ListDepartments(generic.ListView):
    template_name = 'company_management/list_departments.html'
    context_object_name = 'all_departments'

    def get_queryset(self):
        return Department.objects.all()


# Detailed view of a specific department
class DetailsDepartment(generic.DetailView):
    model = Department
    context_object_name = 'department'
    template_name = 'company_management/details_department.html'


class UpdateDepartment(UpdateView):
    model = Department
    fields = ['name', 'company']
    template_name = 'company_management/update_department.html'
    success_url = reverse_lazy('list-departments')

#Branches 
class AddBranch(CreateView):
    model = Branch
    fields = ['name', 'company', 'location']
    template_name = 'company_management/add_branch.html'
    success_url = reverse_lazy('list-branches')


# All Branch list view
class ListBranches(generic.ListView):
    template_name = 'company_management/list_branches.html'
    context_object_name = 'all_branches'

    def get_queryset(self):
        return Branch.objects.all()


# Detailed view of a specific branch
class DetailsBranch(generic.DetailView):
    model = Branch
    context_object_name = 'branch'
    template_name = 'company_management/details_branch.html'


class UpdateBranch(UpdateView):
    model = Branch
    fields = ['name', 'company', 'location']
    template_name = 'company_management/update_branch.html'
    success_url = reverse_lazy('list-branches')


# Branches_Contacts
class AddBranchContacts(CreateView):
    model = BranchPhoneContact
    fields = ['phone_number', 'secondary_number', 'branch']
    template_name = 'company_management/add_branch_contact.html'
    success_url = reverse_lazy('list-branch-contacts')


# All Branch list view
class ListBranchContacts(generic.ListView):
    template_name = 'company_management/list_branch_contact.html'
    context_object_name = 'branch_phone_contacts'

    def get_queryset(self):
        return BranchPhoneContact.objects.all()


# Detailed view of a specific branch
class DetailsBranchContact(generic.DetailView):
    model = BranchPhoneContact
    context_object_name = 'branch_phone_contact'
    template_name = 'company_management/details_branch_contact.html'


class UpdateBranchContact(UpdateView):
    model = BranchPhoneContact
    fields = ['phone_number', 'secondary_number', 'branch']
    template_name = 'company_management/update_branch_contact.html'
    success_url = reverse_lazy('list-branch-contacts')


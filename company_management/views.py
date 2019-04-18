from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse

from .forms import CompanyForm, DepartmentForm

from .models import Company, Department, Branch, CompanyDomain, CompanyCategory


class AddCompanyDomain(CreateView):
    model = CompanyDomain
    fields = ['name', 'description']
    template_name = 'company_management/add_domain.html'
    success_url = reverse_lazy('listDomains')


class UpdateDomain(UpdateView):
    model = CompanyDomain
    fields = ['name', 'description']
    template_name = 'company_management/update_domain.html'
    success_url = reverse_lazy('listDomains')


class UpdateDomain(UpdateView):
    model = CompanyDomain
    fields = ['name', 'description']
    template_name = 'company_management/update_domain.html'
    success_url = reverse_lazy('listDomains')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        domainid = int(self.request.GET['domainid'])
        context['domainid'] = domainid
        return context


class DeleteDomain(DeleteView):
    model = CompanyDomain
    success_url = reverse_lazy('listDomains')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class ListCompanyDomains(generic.ListView):
    template_name = 'company_management/list_domains.html'
    context_object_name = 'list_domains'

    def get_queryset(self):
        return CompanyDomain.objects.all()


class DomainCompanyList(generic.ListView):
    model = CompanyDomain
    template_name = 'company_management/domain_companies_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        domainid = int(self.request.GET['domainid'])
        context['company_list'] = Company.objects.all().filter(domain=domainid)
        return context


class ListCompanyCategories(generic.ListView):
    template_name = 'company_management/list_categories.html'
    context_object_name = 'list_categories'

    def get_queryset(self):
        return CompanyCategory.objects.all()


class AddCompanyCategory(CreateView):
    model = CompanyCategory
    fields = ['category_value', 'description']
    template_name = 'company_management/add_category.html'
    success_url = reverse_lazy('listCategories')


class UpdateCategory(UpdateView):
    model = CompanyCategory
    fields = ['category_value', 'description']
    template_name = 'company_management/update_category.html'
    success_url = reverse_lazy('listCategories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categoryid = int(self.request.GET['categoryid'])
        context['categoryid'] = categoryid
        return context


class DeleteCategory(DeleteView):
    model = CompanyCategory
    success_url = reverse_lazy('listCategories')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class CompanyCategoryList(generic.ListView):
    model = CompanyCategory
    template_name = 'company_management/category_companies_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = int(self.request.GET['categoryid'])
        context['company_list'] = Company.objects.all().filter(category=category)
        return context


class AddCompany(CreateView):
    model = Company
    fields = ['name', 'category', 'domain', 'owner', 'description']
    template_name = 'company_management/add_company.html'
    success_url = reverse_lazy('listCompanies')


# All companies list view
class ListCompanies(generic.ListView):
    template_name = 'company_management/list_companies.html'
    context_object_name = 'all_companies'

    def get_queryset(self):
        return Company.objects.all()


class companyBranchList(generic.ListView):
    model = Company
    template_name = 'company_management/company_branch_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companyid = int(self.request.GET['companyid'])
        context['branch_list'] = Branch.objects.all().filter(company=companyid)
        return context


class ListCompanyBranches(generic.ListView):
    model = Company
    template_name = 'company_management/branches/branch_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companyid = int(self.request.GET['companyid'])
        context['company_branch_list'] = Branch.objects.all().filter(company=companyid)
        return context


def validatCompanyName(request):
    company_name = request.GET.get('companyname', None)
    data = {
        'is_taken': Company.objects.filter(name=company_name).exists()
    }
    return JsonResponse(data)


def validateDomainName(request):
    domain_name = request.GET.get('domainname', None)
    data = {
        'is_taken': CompanyDomain.objects.filter(name=domain_name).exists()
    }
    return JsonResponse(data)


def validateCategoryName(request):
    category_name = request.GET.get('categoryname', None)
    data = {
        'is_taken': CompanyCategory.objects.filter(category_value=category_name).exists()
    }
    return JsonResponse(data)


class UpdateCompany(UpdateView):
    model = Company
    fields = ['name', 'category', 'domain', 'owner', 'description']
    template_name = 'company_management/update_company.html'
    success_url = reverse_lazy('listCompanies')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companyid = int(self.request.GET['companyid'])
        context['companyid'] = companyid
        return context


# Adding departments view
class AddDepartment(CreateView):
    model = Department
    template_name = 'company_management/addDepartment.html'
    fields = ['name', 'company']
    success_url = reverse_lazy('listDepartments')


# All departments list view
class ListDepartments(generic.ListView):
    template_name = 'company_management/listDepartments.html'
    context_object_name = 'all_departments'

    def get_queryset(self):
        return Department.objects.all()


# Detailed view of a specific department
class DetailsDepartment(generic.DetailView):
    model = Department
    context_object_name = 'department'
    template_name = 'company_management/detailsDepartment.html'


class UpdateDepartment(UpdateView):
    model = Department
    fields = ['name', 'company']
    template_name = 'company_management/updateDepartment.html'
    success_url = reverse_lazy('listDepartments')


class AddBranch(CreateView):
    model = Branch
    fields = ['name', 'company', 'location']
    template_name = 'company_management/addBranch.html'
    success_url = reverse_lazy('listBranches')


# All Branch list view
class ListBranches(generic.ListView):
    template_name = 'company_management/listBranches.html'
    context_object_name = 'all_branches'

    def get_queryset(self):
        return Branch.objects.all()


# Detailed view of a specific branch
class DetailsBranch(generic.DetailView):
    model = Branch
    context_object_name = 'branch'
    template_name = 'company_management/detailsBranch.html'


class UpdateBranch(UpdateView):
    model = Branch
    fields = ['name', 'company', 'location']
    template_name = 'company_management/updateBranch.html'


success_url = reverse_lazy('listBranches')

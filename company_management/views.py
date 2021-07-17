import datetime
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import DetailView
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.hashers import make_password
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import CompanyForm, DepartmentForm, BranchForm, BranchContactForm, BranchEmailForm

from .models import Company, Department, Branch, CompanyDomain, CompanyCategory, BranchPhoneContact, \
    BranchEmailAddresses, ServiceLevelAgreement

from user_management.models import User
from project_management.models import Project, Status, ProjectCode

from django.core import serializers
from django.template import loader


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
    fields = ['name', 'category', 'domain', 'owner', 'description', 'has_domain']
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
    fields = ['name', 'category', 'domain', 'owner', 'description', 'has_domain']
    template_name = 'company_management/update_company.html'
    success_url = reverse_lazy('listCompanies')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companyid = int(self.request.GET['companyid'])
        status = Company.objects.get(pk=int(self.kwargs['pk'])).has_domain
        context['status'] = status
        context['pk'] = self.kwargs['pk']
        context['companyid'] = companyid
        return context


# Adding departments view
class AddDepartment(CreateView):
    model = Department
    template_name = 'company_management/add_department.html'
    fields = ['name', 'company']
    success_url = reverse_lazy('listDepartments')


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
    success_url = reverse_lazy('listDepartments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        deptid = int(self.request.GET['deptid'])
        context['deptid'] = deptid
        return context


# creating branch
def create_branch(request):
    if request.method == 'POST':
        branch_form = BranchForm(request.POST)
        contact_form = BranchContactForm(request.POST)
        email_form = BranchEmailForm(request.POST)

        if all([branch_form.is_valid()]):
            branch = branch_form.save()
            branch_id = Branch.objects.get(pk=branch.id)

            if branch:
                form = request.POST.copy()
                phone_number = form.get('phone_number')
                email_address = form.get('email_address')
                contact = BranchPhoneContact(branch_id=branch_id.id, phone_number=phone_number)
                email = BranchEmailAddresses(branch_id=branch_id.id, email_address=email_address)
                contact.save()
                email.save()
            return redirect('listBranches')
    else:
        branch_form = BranchForm()
        contact_form = BranchContactForm()
        email_form = BranchEmailForm()

    return render(request, 'company_management/add_branch.html', {
        'branch_form': branch_form,
        'contact_form': contact_form,
        'email_form': email_form,
    })


# All Branch list view
class ListBranches(LoginRequiredMixin, generic.ListView):
    template_name = 'company_management/list_branches.html'
    context_object_name = 'all_branches'

    def get_queryset(self):
        return Branch.objects.all()


# Detailed view of a specific branch
class DetailsBranch(generic.DetailView):
    model = Branch
    context_object_name = 'branch'
    template_name = 'company_management/details_branch.html'


# update branch
class UpdateBranch(UpdateView):
    model = Branch
    fields = ['name', 'company', 'location']
    template_name = 'company_management/update_branch.html'
    success_url = reverse_lazy('listBranches')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branchid = int(self.request.GET['branchid'])
        context['branchid'] = branchid
        return context


# BRANCH PHONE CONTACTS
class AddBranchContacts(CreateView):
    model = BranchPhoneContact
    fields = ['phone_number', 'secondary_number', 'branch']
    template_name = 'company_management/add_branch_contact.html'
    success_url = reverse_lazy('listBranchContacts')


# # All Branch list view
class ListBranchContacts(generic.ListView):
    template_name = 'company_management/list_branch_contact.html'
    context_object_name = 'branch_phone_contacts'

    def get_queryset(self):
        return BranchPhoneContact.objects.all()


# Detailed view of a specific branch
class DetailBranchContacts(generic.DetailView):
    model = BranchPhoneContact
    context_object_name = 'branch_phone_contacts'
    template_name = 'company_management/details_branch_contact.html'


# Update view of branch
class UpdateBranchContacts(UpdateView):
    model = BranchPhoneContact
    fields = ['phone_number', 'secondary_number', 'branch']
    template_name = 'company_management/update_branch_contact.html'
    success_url = reverse_lazy('listBranchContacts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contactid = int(self.request.GET['contactid'])
        context['contactid'] = contactid
        return context


# BRANCH EMAIL CONTACTS
class AddBranchEmails(CreateView):
    model = BranchEmailAddresses
    fields = ['email_address', 'secondary_email', 'branch']
    template_name = 'company_management/add_branch_email.html'
    success_url = reverse_lazy('listBranchEmails')


# # All branch email list view
class ListBranchEmails(generic.ListView):
    template_name = 'company_management/list_branch_email.html'
    context_object_name = 'branch_emails'

    def get_queryset(self):
        return BranchEmailAddresses.objects.all()


# Detailed view of a specific branch
class DetailBranchEmails(generic.DetailView):
    model = BranchEmailAddresses
    context_object_name = 'branch_emails'
    template_name = 'company_management/details_branch_email.html'


# Update view of branch
class UpdateBranchEmails(UpdateView):
    model = BranchEmailAddresses
    fields = ['email_address', 'secondary_email', 'branch']
    template_name = 'company_management/update_branch_email.html'
    success_url = reverse_lazy('listBranchEmails')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        emailid = int(self.request.GET['emailid'])
        context['emailid'] = emailid
        return context


def fetch_domain_list(request):
    domain_list = CompanyDomain.objects.all()

    data = {
        'perm': serializers.serialize("json", domain_list)
    }
    return JsonResponse(data)


def add_select_company_domain(request):
    dname = request.GET.get('dname')
    desc = request.GET.get('description')

    if desc != "":
        company_domain = CompanyDomain(name=dname, description=desc)
    else:
        company_domain = CompanyDomain(name=dname)
    company_domain.save()

    return JsonResponse({})


def save_company(request):
    has_domain = request.GET.get('has_domain')
    id_domain = request.GET.get('id_domain')
    category = request.GET.get('category')
    company_name = request.GET.get('company_name')
    owner = request.GET.get('id_owner')
    description = request.GET.get('description')

    if int(has_domain) == 1:
        save_company = Company(name=company_name, domain_id=int(id_domain), category_id=int(category),
                               description=description, owner=owner, has_domain=has_domain)
    else:
        save_company = Company(name=company_name, category_id=int(category), description=description, owner=owner)
    save_company.save()

    all_companies = Company.objects.all()
    template = loader.get_template('company_management/list_companies2.html')
    context = {
        'all_companies': all_companies,
    }

    return HttpResponse(template.render(context, request))


def save_company_update(request):
    has_domain = request.GET.get('has_domain')

    id_domain = request.GET.get('id_domain')
    category = request.GET.get('category')
    company_name = request.GET.get('company_name')
    owner = request.GET.get('id_owner')
    description = request.GET.get('description')
    pk = request.GET.get('pk')

    if int(has_domain) == 1:
        Company.objects.filter(pk=int(pk)).update(name=company_name, domain_id=int(id_domain), category_id=int(category)
        , description=description, owner=owner, has_domain=has_domain)
    else:
        Company.objects.filter(pk=int(pk)).update(name=company_name, domain_id=None
        ,category_id=int(category), description=description, owner=owner, has_domain=has_domain)

    all_companies = Company.objects.all()
    template = loader.get_template('company_management/list_companies2.html')
    context = {
        'all_companies': all_companies,
    }

    return HttpResponse(template.render(context, request))


def customer_sla_list(request):
    company_id = request.session['company_id']

    template = loader.get_template('company_management/list_customer_sla_pane.html')
    sla_obj = ServiceLevelAgreement.objects.filter(company_id=int(company_id))

    context = {
        'sla_obj': sla_obj
    }
    
    return HttpResponse(template.render(context, request))


class AddSla(CreateView):
    model = ServiceLevelAgreement
    fields = ['name', 'customer','description', 'company']

    template_name = 'company_management/add_sla.html'
    success_url = reverse_lazy('listSlaContracts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # SHOULD FILTER BY SESSION COMPANY CUTOMERS AFTER THEY ADD THE PARENT COLUMN
        context['customer_list'] = Company.objects.all()
        return context


def save_sla(request):
    sla_name = request.GET.get('sla_name')
    id_description = request.GET.get('id_description')
    id_customer = request.GET.get('id_customer')
    company_id = request.session['company_id']

    obj = ServiceLevelAgreement(name=sla_name, customer_id=int(id_customer), description=id_description, company_id=company_id)
    obj.save()

    template = loader.get_template('company_management/list_slas.html')
    sla_obj = ServiceLevelAgreement.objects.filter(company_id=int(company_id))

    context = {
        'sla_obj': sla_obj
    }

    return HttpResponse(template.render(context, request))

    
# CUSTOMERS
class AddCustomer(CreateView):
    model = Company
    fields = ['name', 'category', 'domain', 'owner', 'description', 'has_domain']
    template_name = 'company_management/add_customer.html'
    success_url = reverse_lazy('listCustomers')

    
def list_customers(request):
    """Return list of customers"""
    category_value = CompanyCategory.objects.get(category_value="client")
    category_id = category_value.id
    all_customers = Company.objects.filter(category_id=category_id)
    template = loader.get_template('company_management/list_customers.html')
    context = {
        'all_customers': all_customers
    }

    return HttpResponse(template.render(context, request))


def add_customer(request):
    template = loader.get_template('company_management/add_customer.html')
    context = {

    }
    return HttpResponse(template.render(context, request))


def return_client_company(request):
    client = CompanyCategory.objects.filter(category_value="client")

    data = {
        'clients': serializers.serialize("json", client),
        'success': True,

    }

    return JsonResponse(data)


def save_customer(request):
    """save customer"""
    has_domain = request.GET.get('has_domain')
    id_domain = request.GET.get('id_domain')
    category = request.GET.get('category')
    company_name = request.GET.get('company_name')
    owner = request.GET.get('id_owner')
    description = request.GET.get('description')
    parent = request.session['company_id']

    if int(has_domain) == 1:
        save_company = Company(name=company_name, domain_id=int(id_domain), category_id=int(category),
                               description=description, owner=owner, has_domain=has_domain, parent=1)
    else:
        save_company = Company(name=company_name, category_id=int(category), description=description, owner=owner, parent=parent)
    save_company.save()

    category_value = CompanyCategory.objects.get(category_value="client")
    category_id = category_value.id
    all_customers = Company.objects.filter(category_id=category_id)
    template = loader.get_template('company_management/list_customers.html')
    context = {
        'all_customers': all_customers,
    }

    return HttpResponse(template.render(context, request))


class UpdateSLA(UpdateView):
    model = ServiceLevelAgreement
    fields = ['name', 'customer','description', 'company']
    template_name = 'company_management/update_sla.html'
    success_url = reverse_lazy('listSlaContracts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sla_id = self.kwargs['pk']
        int_customer_id = self.get_object().customer_id
        context['sla_id'] = sla_id
        context['customer'] = int_customer_id
        return context


def save_sla_update(request):
    sla_name = request.GET.get('sla_name')
    id_description = request.GET.get('id_description')
    id_customer = request.GET.get('id_customer')
    sla_id = request.GET.get('sla_id')
    company_id = request.session['company_id']

    ServiceLevelAgreement.objects.filter(pk=int(sla_id)).update(name=sla_name, description=id_description, customer_id=id_customer)
    
    template = loader.get_template('company_management/list_slas.html')
    sla_obj = ServiceLevelAgreement.objects.filter(company_id=int(company_id))

    context = {
        'sla_obj': sla_obj
    }

    return HttpResponse(template.render(context, request))

    
def customer_list_pane(request):
    template = loader.get_template('company_management/customer_list_container.html')
    context = {

    }
    return HttpResponse(template.render(context, request))


class UpdateCustomer(UpdateView):
    model = Company
    fields = ['name', 'description']
    template_name = 'company_management/update_customer.html'
    success_url = reverse_lazy('listCustomers')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companyid = int(self.request.GET['companyid'])
        status = Company.objects.get(pk=int(self.kwargs['pk']))
        context['status'] = status
        context['pk'] = self.kwargs['pk']
        context['companyid'] = companyid
        return context


def save_customer_update(request):
    company_name = request.GET.get('company_name')
    description = request.GET.get('description')
    pk = request.GET.get('pk')
    parent = parent = request.session['company_id']

    Company.objects.filter(pk=int(pk)).update(name=company_name, description=description, parent=parent)

    all_customers = Company.objects.filter(category_id=1)
    template = loader.get_template('company_management/list_customers.html')
    context = {
        'all_customers': all_customers,
    }

    return HttpResponse(template.render(context, request))


class DetailCustomer(DetailView):
    model = Company
    context_object_name = 'company'
    template_name = 'company_management/details_customer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.kwargs['pk']
        context['company_id'] = company_id
        return context


def validateEmail(request):
    email_address = request.GET.get('email_address', None)

    data = {
        'is_taken': BranchEmailAddresses.objects.filter(email_address=email_address).exists()
    }

    return JsonResponse(data)


def validateDepartment(request):
    department = request.GET.get('dept_name', None)
    print(department)

    data = {
        'is_taken': Department.objects.filter(name=department).exists()
    }

    return JsonResponse(data)

from django import forms

from .models import Company, Department, Branch, CompanyCategory, CompanyDomain


class CompanyDomainForm(forms.ModelForm):
    class Meta:
        model = CompanyDomain
        fields = ('name', 'description',)
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control input-flat'})}


class CompanyCategoryForm(forms.ModelForm):
    class Meta:
        model = CompanyCategory
        fields = ('category_value', 'description',)
        widgets = {'category_value': forms.TextInput(attrs={'class': 'form-control input-flat'})}


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ('name', 'category', 'domain', 'owner', 'description',)
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control input-flat'})}


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ('name', 'company',)
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control input-flat'})}


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ('name', 'company', 'location')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control input-flat'}),
            'location': forms.TextInput(attrs={'class': 'form-control input-flat'}),
        }

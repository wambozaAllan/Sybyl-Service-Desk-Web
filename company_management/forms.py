from django import forms

from .models import Company, Department, Branch

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ('name','category',)
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control input-flat'})}
        
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ('name','company',)
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control input-flat'})}

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ('name', 'company' , 'location')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control input-flat'}),
            'location': forms.TextInput(attrs={'class': 'form-control input-flat'}),
        }



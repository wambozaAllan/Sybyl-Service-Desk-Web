from django import forms
from django.db import models
from .models import Project, Milestone, Task, ProjectDocument
from company_management.models import Company
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from ckeditor.widgets import CKEditorWidget

class OldProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('name', 'description', 'client', 'vendor', 'estimated_cost', 'startdate', 'enddate','project_manager',
                    'project_assignee', 'project_team')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'client' in self.data:
            try:
                country_id = int(self.data.get('client'))
            except (ValueError, TypeError):
                pass

class CreateProjectForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorWidget())
    class Meta:
        model = Project
        fields = ('name', 'description', 'client', 'vendor', 'estimated_cost', 'startdate', 'enddate','project_manager',
                 'project_assignee', 'project_team', 'project_status','logo')

        # widgets = {
        #     'description': forms.Textarea(attrs={'class':'richtexteditor'})
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Project'))

class ProjectUpdateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('description', 'client', 'vendor', 'estimated_cost', 'startdate', 'enddate','project_manager',
                    'project_assignee', 'project_team', 'final_cost', 'project_status','actual_startdate',
                     'actual_enddate')

        widgets = {
            'actual_startdate': forms.DateTimeInput(attrs={'type':'date', 'placeholder':'Select a date'}, format='%d/%m/%Y'),
            'actual_enddate': forms.DateTimeInput(attrs={'type':'date', 'placeholder':'Select a date'}, format='%d/%m/%Y')
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Project'))

class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ('name', 'project', 'description', 'status', 'startdate', 'enddate')

        widgets = {
            'description': forms.Textarea(attrs={'rows':2, 'cols':15})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save person'))

class MilestoneUpdateForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ('name', 'project', 'description', 'status', 'startdate', 'enddate', 'actual_startdate', 'actual_enddate')

        widgets = {
            'actual_startdate': forms.DateTimeInput(attrs={'type':'date', 'placeholder':'Select a date'}, format='%d/%m/%Y'),
            'actual_enddate': forms.DateTimeInput(attrs={'type':'date', 'placeholder':'Select a date'}, format='%d/%m/%Y'),
            'description': forms.Textarea(attrs={'rows':2, 'cols':15})
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save person'))

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('name', 'description', 'project', 'milestone', 'start_date', 'end_date', 'status')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Task'))

class TaskUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('name', 'description', 'project', 'milestone', 'start_date', 'end_date', 'status')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Task'))

class DocumentForm(forms.ModelForm):
    class Meta:
        model = ProjectDocument
        fields = ('title', 'description', 'document', 'project')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Document'))

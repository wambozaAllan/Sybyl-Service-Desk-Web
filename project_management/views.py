import csv, io, xlwt
import xlsxwriter
import datetime
import calendar
from datetime import date, timezone, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, F
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, HttpResponse
from django.template.loader import get_template
from django.core.mail import EmailMessage
from static.fusioncharts import FusionCharts
from django.template import loader
from django.core import serializers
from operator import itemgetter
import operator
from .forms import MilestoneForm


from django.contrib.auth.decorators import user_passes_test, permission_required, login_required

from .models import Project, Milestone, Task, ProjectDocument, Incident, Priority, Status, ProjectTeam, ProjectTeamMember, ProjectForumMessages, ProjectForum, ProjectForumMessageReplies, IncidentComment, IncidentComment, Timesheet, ResubmittedTimesheet, ProjectCode, CustomerRequest, Trackstatus, TaskTimesheetExtend, RequestTimesheetExtend, IssueType, CustomerRequestActivity, CustomerRequestTeamMembers
from user_management.models import User
from company_management.models import Company, CompanyCategory, CompanyDomain, Department, ServiceLevelAgreement
from .forms import CreateProjectForm, MilestoneForm, TaskForm, DocumentForm, ProjectUpdateForm, MilestoneUpdateForm, ProjectForm, IncidentForm, ProjectTeamForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.db.models import Count
import json
import time
from django.db.models import Sum

from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import Paragraph, SimpleDocTemplate, TableStyle, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from background_task import background
from django.contrib.auth import hashers


# Custom Views
class ProjectCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'project_management.add_project'
    model = Project
    form_class = CreateProjectForm
    success_url = reverse_lazy('full_project_list')


def load_all_projects(request):
    projects = Project.objects.all()
    return render(request, 'project_management/project_list.extended.html', {'projects': projects})


def load_selected_projects(request):
    project_status = request.GET.get('project')
    projects = Project.objects.all().filter(project_status=project_status)
    return render(request, 'project_management/project_dropdown_list_options.html', {'projects': projects})


class ProjectListView(ListView):
    model = Project
    context_object_name = 'projects'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ongoing_projects_list'] = Project.objects.all().filter(project_status='New')
        return context


def model_form_upload(request):
    print('Attempting to Upload...')
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            # title             = form.cleaned_data['title']
            project = form.cleaned_data['project'].id
            form.save()
            return redirect('%d/' % project)
    else:
        form = DocumentForm()
    return render(request, 'project_management/model_form_upload.html', {
        'form': form
    })


def load_project_documents(request):
    project_id = int(request.GET.get('project'))
    documents = ProjectDocument.objects.all()
    return render(request, 'project_management/document_dropdown_list_options.html', {'documents': documents})


class ProjectDetailView(DetailView):
    model = Project

    def get_queryset(self):
        return Project.objects.all()

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        context['milestones'] = Milestone.objects.filter(project_id=self.kwargs.get('pk'))
        context['tasks'] = Task.objects.filter(project_id=self.kwargs.get('pk'))
        context['incidents'] = Incident.objects.filter(project_id=self.kwargs.get('pk'))
        return context


class CompleteProjectListView(ListView):
    model = Project
    context_object_name = 'projects'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ongoing_projects_list'] = Project.objects.all().filter(project_status='Completed')
        return context


class TerminatedProjectListView(ListView):
    model = Project
    context_object_name = 'projects'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ongoing_projects_list'] = Project.objects.all().filter(project_status=2)
        return context


class ProjectUpdateView(UpdateView):
    model = Project
    template_name = 'project_management/project_update_form.html'
    form_class = ProjectUpdateForm
    success_url = reverse_lazy('project_list')


def projects_download(request):
    items = Project.objects.all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="projects.csv"'

    writer = csv.writer(response)
    writer.writerow(
        ['Project Name', 'Description', 'Client', 'Start Date', 'End Date', 'Project Manager', 'Status', 'Vendor',
         'Completion', 'Cost'])

    for obj in items:
        writer.writerow(
            [obj.name, obj.description, obj.client, obj.startdate, obj.enddate, obj.project_manager, obj.project_status,
             obj.vendor, obj.completion, obj.estimated_cost])

    return response


def export_projects_xls(request):
    import xlwt
    queryset = Project.objects.all()
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Projects.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("Projects")

    row_num = 1

    columns = [(u"Project Name", 5000), (u"Description", 5000), (u"Client", 5000),
               (u"Start Date", 5000), (u"End Date", 5000), (u"Project Manager", 5000),
               (u"Status", 5000), (u"Vendor", 5000), (u"Cost", 5000)
               ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        # set column width
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1

    for obj in queryset:
        row_num += 1

        row = [
            obj.name,
            obj.description,
            obj.client,
            obj.startdate,
            obj.enddate,
            obj.project_manager,
            obj.project_status,
            obj.vendor,
            obj.estimated_cost,
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)

    wb.save(response)
    return response


class MilestoneCreateView(LoginRequiredMixin, CreateView):
    model = Milestone
    form_class = MilestoneForm

    def form_valid(self, form):
        milestone_name = form.cleaned_data['name']
        project = form.cleaned_data['project']
        status = form.cleaned_data['status']
        start = form.cleaned_data['startdate']
        finish = form.cleaned_data['enddate']
        current_user = self.request.user
        name = current_user.username
        
        milestone = Milestone(name=milestone_name, project=project, status=status, startdate=start, enddate=finish, creator=current_user)
        milestone.save()

        context = {
            'name': name,
            'milestone_name': milestone_name,
            'project': project,
            'status': status,
            'startdate': start,
            'enddate': finish,
        }

        subject = 'New Milestone | Action Required'
        message = get_template('mails/new_milestone_email.html').render(context)
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [current_user.email, 'ampumuzadickson@gmail.com']
        mail_to_send = EmailMessage(subject, message, to=recipient_list, from_email=email_from)
        mail_to_send = EmailMessage(subject, message, to=recipient_list, from_email=email_from)
        mail_to_send.content_subtype = 'html'
        mail_to_send.send()

        return HttpResponseRedirect('/projectManagement/milestones')

    success_url = reverse_lazy('milestones')


class MilestoneListView(ListView, LoginRequiredMixin):
    context_object_name = 'milestones'

    def get_queryset(self):
        user = self.request.user
        members = ProjectTeamMember.objects.filter(member=user)
        team_list = []
        for value in members:  
            team_members = ProjectTeamMember.project_team.through.objects.filter(projectteammember=value.id)

            for obj in team_members:
                team_name = obj.projectteam
                team_list.append(team_name)
        
        project_list = []
        milestone_list = []
        for team in team_list:
            project_id = team.project_id
            
            project = Project.objects.get(id=project_id)

            milestone = Milestone.objects.filter(project_id=project.id)
            milestone_list.append(milestone)
       
            return milestone

@login_required
def project_milestones_by_user(request):
    user = request.user
    members = ProjectTeamMember.objects.filter(member=user)
    team_list = []
    for value in members:  
        team_members = ProjectTeamMember.project_team.through.objects.filter(projectteammember=value.id)

        for obj in team_members:
            team_name = obj.projectteam
            team_list.append(team_name)
    
    project_list = []
    milestone_list = []
    for team in team_list:
        project_id = team.project_id
        
        project = Project.objects.get(id=project_id)

        milestones = Milestone.objects.filter(project_id=project.id)
        for value in milestones:
            milestone_list.append(value)
    
    template = loader.get_template('project_management/milestone_list.html')
    context = {
        'milestones': milestone_list
    }

    return HttpResponse(template.render(context, request))


def load_add_milestone(request):
    """load page for milestones"""
    current_user = request.user.id
    members = ProjectTeamMember.objects.filter(member=current_user)
    team_list = []
    for value in members:  
        team_members = ProjectTeamMember.project_team.through.objects.filter(projectteammember=value.id)

        for obj in team_members:
            team_name = obj.projectteam
            team_list.append(team_name)
    
    project_list = []
    for team in team_list:
        project_id = team.project_id
        
        project = Project.objects.get(id=project_id)
        project_dict = {}
        project_dict['id'] = project.id
        project_dict['name'] = project.name

        project_list.append(project_dict)

    statuses = Status.objects.all()

    context = {
        "project_list": project_list,
        "statuses" : statuses
    }
    return render(request, 'project_management/milestone_form.html', context=context)


def populate_milestone_view(request):
    """
    populate project_milestone view
    """
    project_id = request.GET.get('project_id')
    project_name = request.GET.get('project_name')
    status = Status.objects.all()
      
    template = loader.get_template('project_management/add_project_milestone.html')
    context = {
        'project_id': project_id,
        'project_name': project_name
    }

    return HttpResponse(template.render(context, request))


def populate_milestone_status(request):
    """
    populate status field with status
    """
    project_id = request.GET.get('project_id')
    project_name = request.GET.get('project_name')    

    status = Status.objects.all()

    data = {
        'status': serializers.serialize("json", status)
    }

    return JsonResponse(data)


def validateMilestoneName(request):
    milestone_name = request.GET.get('milestoneName', None)
    project_id = int(request.GET.get('project_id'))
    project = Project.objects.get(id=project_id)

    data = {
        'is_taken': Milestone.objects.filter(name=milestone_name, project_id=project.id).exists()
    }
    return JsonResponse(data)


def check_milestone_status(request):
    status_id = request.GET.get('status_id', None);
    if Status.objects.filter(id=status_id).exists():
        status = Status.objects.get(id=status_id)
        data = {
            "status_name": status.name
        }

        return JsonResponse(data)


def save_milestone(request):
    """
    add milestone to database
    """
    project_id = int(request.GET.get('project_id'))
    # project_name = request.GET.get('project_name')
    name = request.GET.get('name')
    description = request.GET.get('description')
    status_id = int(request.GET.get('status_id'))
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')
    actual_start = request.GET.get('actual_start')
    actual_end = request.GET.get('actual_end')
    creator = request.user.id

    if status_id == "":
        status_id = None

    if description == "":
        description = None

    if end != "null":
        end = datetime.datetime.strptime(end, "%d/%m/%Y").strftime("%Y-%m-%d")
    else:
        end = None

    if start != "null":
        start = datetime.datetime.strptime(start, "%d/%m/%Y").strftime("%Y-%m-%d")
    else:
        start = None

    if actual_start != "null":
        actual_start = datetime.datetime.strptime(actual_start, "%d/%m/%Y").strftime("%Y-%m-%d")
    else:
        actual_start = None

    if actual_end != "null":
        actual_end = datetime.datetime.strptime(actual_end, "%d/%m/%Y").strftime("%Y-%m-%d")
    else:
        actual_end = None

    project = Project.objects.get(id=project_id)

    if Milestone.objects.filter(name=name, project_id=project.id).exists():
        milestone = Milestone.objects.get(name=name, project_id=project.id)
        response_data = {
            'error': "Milestone Name exists",
            'name': milestone.name,
            'state':False
        }
    
    else:
        milestone = Milestone(name=name, description=description, project_id=project_id, creator_id=creator, startdate=start, enddate=end, status_id=status_id, actual_startdate=actual_start, actual_enddate=actual_end )
        milestone.save()

        response_data = {
            'success': "Milestone saved successfully",
            'name': milestone.name,
            'state':True
        }

    return JsonResponse(response_data)

  
def save_update_milestone(request, pk):
    """update project milestone"""
    name = request.GET.get('name')
    description = request.GET.get('description')
    status_id = int(request.GET.get('status'))
    start_date = request.GET.get('startdate')
    end_date = request.GET.get('enddate')
    actual_start_date = request.GET.get('actual_startdate')
    actual_end_date = request.GET.get('actual_enddate')
    project_id = int(request.GET.get('project_id'))

    status = Status.objects.get(id=status_id)
    project = Project.objects.get(id=project_id)

    if start_date is not "":
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    else:
        start_date = None

    if end_date is not "":
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    else:
        end_date = None

    if actual_start_date is not "":
        actual_start_date = datetime.datetime.strptime(actual_start_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    else:
        actual_start_date = None

    if actual_end_date is not "":
        actual_end_date = datetime.datetime.strptime(actual_end_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    else:
        actual_end_date = None

    milestone = Milestone.objects.get(id=int(pk))
    milestone.name = name
    milestone.status = status
    milestone.enddate = end_date
    milestone.startdate = start_date
    milestone.actual_startdate = actual_start_date
    milestone.actual_enddate = actual_end_date
    milestone.description = description
    milestone.project = project
    milestone.save()

    open_status = Status.objects.get(name="Open")
    onhold_status = Status.objects.get(name="Onhold")
    terminated_status = Status.objects.get(name="Terminated")
    completed_status = Status.objects.get(name="Completed")

    if status == completed_status:
        completed_milestones = Milestone.objects.filter(project_id=project_id, status=completed_status)
        open_count = Milestone.objects.filter(project_id=project.id, status=open_status).count()
        onhold_count = Milestone.objects.filter(project_id=project.id, status=onhold_status).count()
        terminated_count = Milestone.objects.filter(project_id=project.id, status=terminated_status).count()
        completed_count = Milestone.objects.filter(project_id=project_id, status=completed_status).count()
        
        template = loader.get_template('project_management/completed_milestones.html')
        context = {
            'project_id': project_id,
            'project_name': project.name,
            'completed_milestones': completed_milestones,
            'open_count': open_count,
            'onhold_count': onhold_count,
            'terminated_count': terminated_count,
            'completed_count':completed_count
        }  

    elif status == terminated_status:
        terminated_milestones = Milestone.objects.filter(project_id=project.id, status=terminated_status)
        open_count = Milestone.objects.filter(project_id=project.id, status=open_status).count()
        onhold_count = Milestone.objects.filter(project_id=project.id, status=onhold_status).count()
        terminated_count = Milestone.objects.filter(project_id=project.id, status=terminated_status).count()
        completed_count = Milestone.objects.filter(project_id=project_id, status=completed_status).count()

        template = loader.get_template('project_management/terminated_milestones.html')
        context = {
            'project_id': project.id,
            'project_name': project.name,
            'terminated_milestones': terminated_milestones,
            'open_count': open_count,
            'onhold_count': onhold_count,
            'terminated_count': terminated_count,
            'completed_count':completed_count
        }

    elif status == onhold_status:
        onhold_milestones = Milestone.objects.filter(project_id=project.id, status=onhold_status)
        open_count = Milestone.objects.filter(project_id=project.id, status=open_status).count()
        onhold_count = Milestone.objects.filter(project_id=project.id, status=onhold_status).count()
        terminated_count = Milestone.objects.filter(project_id=project.id, status=terminated_status).count()
        completed_count = Milestone.objects.filter(project_id=project_id, status=completed_status).count()

        template = loader.get_template('project_management/onhold_milestones.html')
        context = {
            'project_id': project.id,
            'project_name': project.name,
            'onhold_milestones': onhold_milestones,
            'open_count': open_count,
            'onhold_count': onhold_count,
            'terminated_count': terminated_count,
            'completed_count':completed_count
        }

    elif status == open_status:
        open_milestones = Milestone.objects.filter(project_id=project.id, status=open_status)
        open_count = Milestone.objects.filter(project_id=project.id, status=open_status).count()
        onhold_count = Milestone.objects.filter(project_id=project.id, status=onhold_status).count()
        terminated_count = Milestone.objects.filter(project_id=project.id, status=terminated_status).count()
        completed_count = Milestone.objects.filter(project_id=project_id, status=completed_status).count()

        template = loader.get_template('project_management/open_milestones.html')
        context = {
            'project_id': project.id,
            'project_name': project.name,
            'open_milestones': open_milestones,
            'open_count': open_count,
            'onhold_count': onhold_count,
            'terminated_count': terminated_count,
            'completed_count':completed_count
        }

    else:
        context = {
            'project_id': project.id,
            'project_name': project.name,
        }

    return HttpResponse(template.render(context, request))


def update_project_milestone(request, pk):
    """
    update project_milestone view
    """
    milestone_id = request.GET.get('milestone_id')
    milestone_name = request.GET.get('milestone_name')
    project_id = request.GET.get('project_id')
    project_name = request.GET.get('project_name')
    template = loader.get_template('project_management/update_project_milestone.html')   

    milestone = get_object_or_404(Milestone, pk=milestone_id)
    
    form = MilestoneUpdateForm(request.POST, instance=milestone)
    if form.is_valid():
        form.save()
        context = {
            'milestone_id': milestone_id,
            'project_id': project_id
        }
        return render(request, 'project_management/list_project_milestones.html', context)


    context = {
        'form': form,
        'project_name': project_name,
        'project_id': project_id,
        'milestone_name': milestone_name,
        'milestone_id': milestone_id
    }

    return HttpResponse(template.render(context, request))


class UpdateProjectMilestone(UpdateView):
    model = Milestone
    fields = ['name', 'status', 'description', 'startdate', 'enddate', 'actual_startdate', 'actual_enddate', 'project' ]
    template_name = 'project_management/update_project_milestone.html'
    success_url = reverse_lazy('listProjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        milestone_id = int(self.kwargs['pk'])
        project_id = self.get_object().project_id
        context['project_id'] = project_id
        context['milestone_id'] = milestone_id
        return context


class UpdateOpenMilestone(UpdateView):
    model = Milestone
    fields = ['name', 'status', 'description', 'startdate', 'enddate', 'actual_startdate', 'actual_enddate', 'project' ]
    template_name = 'project_management/update_open_milestone.html'
    success_url = reverse_lazy('listProjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        milestone_id = int(self.kwargs['pk'])
        project_id = self.get_object().project_id
        context['project_id'] = project_id
        context['milestone_id'] = milestone_id
        return context


class UpdateOnholdMilestone(UpdateView):
    model = Milestone
    fields = ['name', 'status', 'description', 'startdate', 'enddate', 'actual_startdate', 'actual_enddate', 'project' ]
    template_name = 'project_management/update_onhold_milestone.html'
    success_url = reverse_lazy('listProjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        milestone_id = int(self.kwargs['pk'])
        project_id = self.get_object().project_id
        context['project_id'] = project_id
        context['milestone_id'] = milestone_id
        return context


class UpdateTerminatedMilestone(UpdateView):
    model = Milestone
    fields = ['name', 'status', 'description', 'startdate', 'enddate', 'actual_startdate', 'actual_enddate', 'project' ]
    template_name = 'project_management/update_terminated_milestone.html'
    success_url = reverse_lazy('listProjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        milestone_id = int(self.kwargs['pk'])
        project_id = self.get_object().project_id
        context['project_id'] = project_id
        context['milestone_id'] = milestone_id
        return context


class UpdateCompletedMilestone(UpdateView):
    model = Milestone
    fields = ['name', 'status', 'description', 'startdate', 'enddate', 'actual_startdate', 'actual_enddate', 'project' ]
    template_name = 'project_management/update_completed_milestone.html'
    success_url = reverse_lazy('listProjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        milestone_id = int(self.kwargs['pk'])
        project_id = self.get_object().project_id
        context['project_id'] = project_id
        context['milestone_id'] = milestone_id
        return context


def list_project_milestones(request):
    """
    list project specific milestones
    """
    project_id = request.GET.get('project_id')

    project = Project.objects.get(id=project_id)

    template = loader.get_template('project_management/list_project_milestones.html')
    
    open_status = Status.objects.get(name="Open")
    
    if Milestone.objects.filter(project_id=project.id, status=open_status).exists():
        open_milestones = Milestone.objects.filter(project_id=project.id, status=open_status)
        open_count = Milestone.objects.filter(project_id=project.id, status=open_status).count()
    else:
        open_milestones = ""
        open_count = 0

    onhold_status = Status.objects.get(name="Onhold")
    if Milestone.objects.filter(project_id=project.id, status=onhold_status).exists():
        onhold_count = Milestone.objects.filter(project_id=project.id, status=onhold_status).count()
    else:
        onhold_count = 0

    terminated_status = Status.objects.get(name="Terminated")
    if Milestone.objects.filter(project_id=project.id, status=terminated_status).exists():
        terminated_count = Milestone.objects.filter(project_id=project.id, status=terminated_status).count()
    else:
        terminated_count = 0

    completed_status = Status.objects.get(name="Completed")
    if Milestone.objects.filter(project_id=project.id, status=completed_status).exists():
        completed_count = Milestone.objects.filter(project_id=project.id, status=completed_status).count()
    else:
        completed_count = 0

    context = {
        'project_id': project.id,
        'project_name': project.name,
        'open_milestones': open_milestones,
        'completed_count': completed_count,
        'onhold_count': onhold_count,
        'terminated_count': terminated_count,
        'open_count': open_count
    }

    return HttpResponse(template.render(context, request)) 


def onhold_project_milestones(request):
    """
    list onhold project milestones
    """
    project_id = request.GET.get('project_id')

    project = Project.objects.get(id=int(project_id))

    d3 = date.today()
    today = d3.strftime("%m %d, %Y")

    template = loader.get_template('project_management/onhold_milestones.html')
    onhold_status = Status.objects.get(name="Onhold")

    milestones_exist = Milestone.objects.filter(project_id=project.id).exists()
    if milestones_exist: 
        onhold_milestones = Milestone.objects.filter(project_id=project.id, status=onhold_status)
        onhold_count = Milestone.objects.filter(project_id=project.id, status=onhold_status).count()

        context = {
            'project_id': project.id,
            'project_name': project.name,
            'onhold_milestones': onhold_milestones,
            'onhold_count': onhold_count,
            'today': today
        }

    else:
        context = {
            'project_id': project.id,
            'project_name': project.name,
            'milestones': ''
        }

    return HttpResponse(template.render(context, request))


def completed_project_milestones(request):
    """
    list completed project milestones
    """
    project_id = request.GET.get('project_id')
    project = Project.objects.get(id=int(project_id))

    template = loader.get_template('project_management/completed_milestones.html')

    d3 = date.today()
    today = d3.strftime("%m %d, %Y")

    completed_status = Status.objects.get(name="Completed")

    if Milestone.objects.filter(project_id=project.id, status=completed_status).exists():
        completed_milestones = Milestone.objects.filter(project_id=project.id, status=completed_status)
        completed_count = Milestone.objects.filter(project_id=project.id, status=completed_status).count()

        context = {
            'project_id': project.id,
            'project_name': project.name,
            'completed_milestones': completed_milestones,
            'completed_count': completed_count,
            'today': today
        }

    else:
        context = {
            'project_id': project.id,
            'project_name': project.name,
            'completed_milestones': ''
        }

    return HttpResponse(template.render(context, request))


def open_milestones(request):
    """
    list open project milestones
    """
    project_id = int(request.GET.get('project_id'))

    project = Project.objects.get(id=project_id)

    template = loader.get_template('project_management/open_milestones.html')
    d3 = date.today()
    today = d3.strftime("%m %d, %Y")
    
    open_status = Status.objects.get(name="Open")
    
    if Milestone.objects.filter(project_id=project.id, status=open_status).exists():
        open_milestones = Milestone.objects.filter(project_id=project.id, status=open_status)
        open_count = Milestone.objects.filter(project_id=project.id, status=open_status).count()
    else:
        open_milestones = ""
        open_count = 0

    onhold_status = Status.objects.get(name="Onhold")
    if Milestone.objects.filter(project_id=project.id, status=onhold_status).exists():
        onhold_count = Milestone.objects.filter(project_id=project.id, status=onhold_status).count()
    else:
        onhold_count = 0

    terminated_status = Status.objects.get(name="Terminated")
    if Milestone.objects.filter(project_id=project.id, status=terminated_status).exists():
        terminated_count = Milestone.objects.filter(project_id=project.id, status=terminated_status).count()
    else:
        terminated_count = 0

    completed_status = Status.objects.get(name="Completed")
    if Milestone.objects.filter(project_id=project.id, status=completed_status).exists():
        completed_count = Milestone.objects.filter(project_id=project.id, status=completed_status).count()
    else:
        completed_count = 0

    context = {
        'project_id': project.id,
        'project_name': project.name,
        'open_milestones': open_milestones,
        'completed_count': completed_count,
        'onhold_count': onhold_count,
        'terminated_count': terminated_count,
        'open_count': open_count,
        'today': today
    }

    return HttpResponse(template.render(context, request)) 


def terminated_project_milestones(request):
    """
    list terminated project milestones
    """
    project_id = request.GET.get('project_id')

    project = Project.objects.get(id=int(project_id))

    template = loader.get_template('project_management/terminated_milestones.html')
    d3 = date.today()
    today = d3.strftime("%m %d, %Y")

    terminated_status = Status.objects.get(name="Terminated")
    if Milestone.objects.filter(project_id=project.id, status=terminated_status).exists():
        terminated_milestones = Milestone.objects.filter(project_id=project.id, status=terminated_status)
        terminated_count = Milestone.objects.filter(project_id=project.id, status=terminated_status).count()

        context = {
            'project_id': project.id,
            'project_name': project.name,
            'terminated_milestones': terminated_milestones,
            'terminated_count': terminated_count,
            'today': today
        }

    else:
        context = {
            'project_id': project.id,
            'project_name': project.name,
            'terminated_milestones': ''
        }
        
    return HttpResponse(template.render(context, request))  


def milestone_count(request):
    """
    returning milestone count
    """

    project_id = int(request.GET.get('project_id'))
    project = Project.objects.get(id=project_id)
    open_status = Status.objects.get(name="Open")
    
    if Milestone.objects.filter(project_id=project.id, status=open_status).exists():
        open_milestones = Milestone.objects.filter(project_id=project.id, status=open_status)
        open_count = Milestone.objects.filter(project_id=project.id, status=open_status).count()
    else:
        open_milestones = ""
        open_count = 0

    onhold_status = Status.objects.get(name="Onhold")
    if Milestone.objects.filter(project_id=project.id, status=onhold_status).exists():
        onhold_count = Milestone.objects.filter(project_id=project.id, status=onhold_status).count()
    else:
        onhold_count = 0

    terminated_status = Status.objects.get(name="Terminated")
    if Milestone.objects.filter(project_id=project.id, status=terminated_status).exists():
        terminated_count = Milestone.objects.filter(project_id=project.id, status=terminated_status).count()
    else:
        terminated_count = 0

    completed_status = Status.objects.get(name="Completed")
    if Milestone.objects.filter(project_id=project.id, status=completed_status).exists():
        completed_count = Milestone.objects.filter(project_id=project.id, status=completed_status).count()
    else:
        completed_count = 0

    data = {
        'completed_count': completed_count,
        'onhold_count': onhold_count,
        'terminated_count': terminated_count,
        'open_count': open_count
    }
    
    return JsonResponse(data)


def view_tasks_under_milestone(request):
    """
    List of Tasks directly under milestone
    """
    
    milestone_id = request.GET.get('milestone_id')
    project_id = request.GET.get('project_id')

    template = loader.get_template('project_management/list_milestone_tasks.html')
    project = get_object_or_404(Project, pk=project_id)

    d3 = date.today()
    today = d3.strftime("%m %d, %Y")
    
    milestone_exists = Milestone.objects.filter(id=milestone_id, project_id=project.id).exists()
    if milestone_exists:
        milestone = Milestone.objects.get(id=milestone_id)
        milestone_tasks = Task.objects.filter(milestone_id=milestone.id).annotate(assigned=Count('assigned_to'))
        statuses = Status.objects.all()

        context = {
            'milestone_name': milestone.name,
            'milestone_id': milestone.id,
            'milestone_tasks': milestone_tasks,
            'project_id': project.id,
            'statuses': statuses,
            'today': today
        }
    else:
        context = {
            'milestone_name': milestone.name,
            'milestone_id': milestone.id,
            'milestone_tasks': '',
            'project_id': project.id,
            'statuses': statuses
        }

    return HttpResponse(template.render(context, request))


def add_milestone_tasks(request):
    """returning json data of members for tasks under milestone"""

    project_id = request.GET.get('project_id')
    project_name = request.GET.get('project_name')
    
    project = Project.objects.get(id=int(project_id))

    status = Status.objects.all()
    milestones = Milestone.objects.filter(project_id=project.id)
    team = ProjectTeam.objects.get(project_id=project.id)
    project_team = team.id
    team_members = ProjectTeamMember.objects.filter(project_team=project_team)
    member_list = list(team_members)
    old = []

    if len(member_list) != 0:
        for member in member_list:
            old_user = User.objects.get(id=member.member_id)
            old.append(old_user)

    data = {
        'statuses': serializers.serialize("json", status),
        'success': True,
        'members': serializers.serialize('json', old)
    }

    return JsonResponse(data)


def add_milestone_specific_task(request):
    """Adding tasks under given milestone"""

    project_id = request.GET.get('project_id')
    milestone_id = request.GET.get('milestone_id')

    project = Project.objects.get(id=project_id)

    milestone = Milestone.objects.get(id=milestone_id)

    status = Status.objects.all()
    milestones = Milestone.objects.filter(project_id=project.id)

    if ProjectTeam.objects.filter(project_id=project.id).exists():
        team = ProjectTeam.objects.get(project_id=project.id)
        project_team = team.id
        team_members = ProjectTeamMember.objects.filter(project_team=project_team)
        member_list = list(team_members)
        old_members = []

        if len(member_list) != 0:
            for member in member_list:
                old_user = User.objects.get(id=member.member_id)
                old_members.append(old_user)

        template = loader.get_template('project_management/add_milestone_task.html')
        context = {
            'project_id': project_id,
            'project_name':project.name,
            'milestone_id': milestone_id,
            'milestone_name': milestone.name,
            'statuses': status,
            'members': old_members
        }

    else:
        template = loader.get_template('project_management/add_milestone_task.html')
        context = {
            'project_id': project_id,
            'project_name':project.name,
            'milestone_id': milestone_id,
            'milestone_name': milestone.name,
            'statuses': status,
            'members': ""
        }

    return HttpResponse(template.render(context, request))


def delete_project_milestone(request):
    """
    delete project milestone
    """
    milestone_name = request.GET.get('milestone_name')
    milestone_id = int(request.GET.get('milestone_id'))
    project_id = int(request.GET.get('project_id'))

    milestone = Milestone.objects.get(id=milestone_id)
    project = Project.objects.get(id=project_id)
    milestone.delete()

    onhold_status = Status.objects.get(name="Onhold")
    onhold_count = Milestone.objects.filter(id=milestone.id, project_id=project.id, status=onhold_status).count()

    response_data = {
        "success": True,
        "onhold_count": onhold_count,
        "message": "Successfully deleted",
    }

    return JsonResponse(response_data)


class MilestoneDetailView(DetailView):
    model = Milestone
    context_object_name = 'milestone'
    template_name = 'project_management/milestone_detail.html'

    def get_queryset(self):
        return Milestone.objects.all()


class DetailsProjectMilestone(DetailView):
    model = Milestone
    context_object_name = 'milestone'
    template_name = 'project_management/details_project_milestones.html'


class MilestoneUpdateView(UpdateView):
    model = Milestone
    template_name = 'project_management/milestone_update_form.html'
    form_class = MilestoneUpdateForm
    success_url = reverse_lazy('milestone_list')


@login_required
def milestone_container(request):
    """milestone container"""
    template = loader.get_template('project_management/milestone_container.html')
    context = {}

    return HttpResponse(template.render(context, request))


# TASKS
class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    fields = ('name', 'description', 'project', 'milestone', 'start_date', 'end_date', 'status')
    template_name = 'project_management/task_form.html'
    success_url = reverse_lazy('listTasks')

    def form_valid(self, form):
        """auto registering loggedin user"""
        form.instance.creator = self.request.user
        return super().form_valid(form)


@login_required
def create_tasks_by_project(request):
    """return tasks by project"""
    current_user = request.user.id
    members = ProjectTeamMember.objects.filter(member=current_user)
    team_list = []
    for value in members:  
        team_members = ProjectTeamMember.project_team.through.objects.filter(projectteammember=value.id)

        for obj in team_members:
            team_name = obj.projectteam
            team_list.append(team_name)
    
    project_list = []
    old = []
    for team in team_list:
        project_id = team.project_id
        
        project = Project.objects.get(id=project_id)
        project_dict = {}
        project_dict['id'] = project.id
        project_dict['name'] = project.name

        project_list.append(project_dict)

    statuses = Status.objects.all()

    context = {
        "project_list": project_list,
        "statuses" : statuses
    }
    return render(request, 'project_management/task_form.html', context=context)


@login_required
def populate_task_view(request):
    """
    populate project_task view
    """
    project_id = request.GET.get('project_id')
    project_name = request.GET.get('project_name')
    template = loader.get_template('project_management/add_project_tasks.html')

    project = Project.objects.get(id=int(project_id))
    status = Status.objects.all()
    milestones = Milestone.objects.filter(project_id=project.id)
    if ProjectTeam.objects.filter(project_id=int(project_id)).exists():
        team = ProjectTeam.objects.get(project_id=project.id)
        project_team = team.id
        team_members = ProjectTeamMember.objects.filter(project_team=project_team)
        member_list = list(team_members)
    
        old = []

        if len(member_list) != 0:
            for member in member_list:
                old_user = User.objects.get(id=member.member_id)
                old.append(old_user)
 
        members = old

    else:
        members = ""

    template = loader.get_template('project_management/add_project_tasks.html')
    context = {
        'project_id': project_id,
        'project_name': project_name,
        'members': members,
        'milestones': milestones,
        'statuses': status
    }

    return HttpResponse(template.render(context, request))


@login_required
def validateTaskName(request):
    """
    check if name already exists
    """
    task_name = request.GET.get('task_name', None)
    milestone_id = int(request.GET.get('milestone_id'))
    milestone = Milestone.objects.get(id=milestone_id)

    data = {
        'is_taken': Task.objects.filter(name=task_name, milestone_id=milestone.id).exists()
    }

    return JsonResponse(data)


@login_required
def save_project_tasks(request):
    """
    save project tasks
    """
    project_id = int(request.GET.get('project_id'))
    name = request.GET.get('name')
    status_id = int(request.GET.get('status_id'))
    milestone_id = int(request.GET.get('milestone'))
    description = request.GET.get('description')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    actual_start = request.GET.get('actual_start')
    actual_end = request.GET.get('actual_end')
    created_by = request.user.id
    assigned_to = json.loads(request.GET['assigned_to'])

    response_data = {}

    if status_id == "":
        status_id = None

    if description == "":
        description = None

    if start_date != "null":
        start_date = datetime.datetime.strptime(start_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    else:
        start_date = None

    if actual_start != "null":
        actual_start = datetime.datetime.strptime(actual_start, "%d/%m/%Y").strftime("%Y-%m-%d")
    else:
        actual_start = None

    if actual_end != "null":
        actual_end = datetime.datetime.strptime(actual_end, "%d/%m/%Y").strftime("%Y-%m-%d")
    else:
        actual_end = None

    if end_date != "null":
        end_date = datetime.datetime.strptime(end_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    else:
        end_date = None

    project = Project.objects.get(id=project_id)
    team = ProjectTeam.objects.get(project_id= project_id)
    
    milestone = Milestone.objects.get(id=milestone_id, project_id=project.id)
    
    if Task.objects.filter(name=name, milestone_id=milestone.id).exists():
        response_data['error'] = "Name exists"
        response_data['state'] = False
    else:   
        task = Task(name=name, description=description, status_id=status_id, milestone_id=milestone.id, project_id=project.id, start_date=start_date, end_date=end_date, creator_id=created_by, actual_start_date=actual_start , actual_end_date=actual_end)
        task.save()
        
        for val in assigned_to:
            if val == "":
                project_member = None
            else:
                val = int(val)   
                project_member = ProjectTeamMember.objects.get(member_id=val, project_team=team)
                task.assigned_to.add(project_member)

        response_data['success'] = "Task created successfully"
        response_data['name'] = task.name
        response_data['state'] = True

    return JsonResponse(response_data)
    

def save_milestone_tasks(request):
    """
    save tasks under specific milestone
    """
    project_id = request.GET.get('project_id')
    project_name = request.GET.get('project_name')
    name = request.GET.get('name')
    status_id = request.GET.get('status_id')
    milestone_id = request.GET.get('milestone')
    description = request.GET.get('description')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    actual_start = request.GET.get('actual_start')
    actual_end = request.GET.get('actual_end')
    created_by = request.user.id
    assigned_to = json.loads(request.GET['assigned_to'])

    response_data = {}

    if status_id == "":
        status_id = None

    if description == "":
        description = None

    if start_date == "null":
        start_date = None
    else:
        start_date = datetime.datetime.strptime(start_date, "%m/%d/%Y").strftime("%Y-%m-%d")

    if end_date == "null":
        end_date = None
    else:
        end_date = datetime.datetime.strptime(end_date, "%m/%d/%Y").strftime("%Y-%m-%d")

    if actual_start == "null":
        actual_start = None
    else:
        actual_start = datetime.datetime.strptime(actual_start, "%m/%d/%Y").strftime("%Y-%m-%d")

    if actual_end == "null":
        actual_end = None
    else:
        actual_end = datetime.datetime.strptime(actual_end, "%m/%d/%Y").strftime("%Y-%m-%d")
    
    project = Project.objects.get(id=project_id)
    
    milestone = Milestone.objects.get(id=milestone_id, project_id=project.id)
    
    if Task.objects.filter(name=name, milestone_id=milestone.id).exists():
        response_data['error'] = "Name exists"
        response_data['state'] = False
    else:   
        task = Task(name=name, description=description, status_id=status_id, milestone_id=milestone.id, project_id=project.id, start_date=start_date, end_date=end_date, actual_start_date=actual_start, actual_end_date=actual_end, creator_id=created_by)
        task.save()

        for val in assigned_to:
            if val == "":
                project_member = None
            else:
                if ProjectTeam.objects.filter(project_id= project_id).exists():
                    team = ProjectTeam.objects.get(project_id= project_id)
                    val = int(val)   
                    project_member = ProjectTeamMember.objects.get(member_id=val, project_team=team)
                    task.assigned_to.add(project_member)

        response_data['success'] = "Task created successfully"
        response_data['name'] = task.name
        response_data['state'] = True

    return JsonResponse(response_data)


def save_team_project_tasks(request):
    """
    save team project tasks
    """
    project_id = request.GET.get('project_id')
    name = request.GET.get('name')
    status_id = request.GET.get('status_id')
    milestone_id = request.GET.get('milestone')
    description = request.GET.get('description')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    actual_start = request.GET.get('actual_start')
    actual_end = request.GET.get('actual_end')
    created_by = request.user.id
    assigned_to = json.loads(request.GET['assigned_to'])

    response_data = {}

    if status_id == "":
        status_id = None

    if description == "":
        description = None

    if start_date != "null":
        start_date = datetime.datetime.strptime(start_date, "%m/%d/%Y").strftime("%Y-%m-%d")
    else:
        start_date = None

    if actual_start != "null":
        actual_start = datetime.datetime.strptime(actual_start, "%m/%d/%Y").strftime("%Y-%m-%d")
    else:
        actual_start = None

    if actual_end != "null":
        actual_end = datetime.datetime.strptime(actual_end, "%m/%d/%Y").strftime("%Y-%m-%d")
    else:
        actual_end = None

    if end_date != "null":
        end_date = datetime.datetime.strptime(end_date, "%m/%d/%Y").strftime("%Y-%m-%d")
    else:
        end_date = None

    project = Project.objects.get(id=project_id)
    team = ProjectTeam.objects.get(project_id= project_id)
    
    milestone = Milestone.objects.get(id=milestone_id, project_id=project.id)
    
    if Task.objects.filter(name=name, milestone_id=milestone.id).exists():
        response_data['error'] = "Name exists"
        response_data['state'] = False
    else:   
        task = Task(name=name, description=description, status_id=status_id, milestone_id=milestone.id, project_id=project.id, start_date=start_date, end_date=end_date, creator_id=created_by, actual_start_date=actual_start , actual_end_date=actual_end)
        task.save()
        
        for val in assigned_to:
            if val == "":
                project_member = None
            else:
                val = int(val)   
                project_member = ProjectTeamMember.objects.get(member_id=val, project_team=team)
                task.assigned_to.add(project_member)

        response_data['success'] = "Task created successfully"
        response_data['name'] = task.name
        response_data['state'] = True

    return JsonResponse(response_data)


class UpdateProjectTask(UpdateView, LoginRequiredMixin):
    model = Task
    fields = ['name', 'status', 'description', 'start_date', 'end_date', 'actual_start_date', 'actual_end_date']
    template_name = 'project_management/update_project_task.html'
    success_url = reverse_lazy('listProjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_id = int(self.request.GET['task_id'])
        project_id = int(self.request.GET['project_id'])
        milestone_id = int(self.request.GET['milestone_id'])

        context['task_id'] = task_id
        context['project_id'] = project_id
        context['milestone_id'] = milestone_id
        team = ProjectTeam.objects.get(project_id=project_id)
        project_team = team.id
        team_members = ProjectTeamMember.objects.filter(project_team=project_team)
        member_list = list(team_members)
        old = []

        if len(member_list) != 0:
            for member in member_list:
                old_user = User.objects.get(id=member.member_id)
                old.append(old_user)

        context['members'] = old
        return context


class UpdateOpenTask(UpdateView):
    model = Task
    fields = ['name', 'status', 'description', 'start_date', 'end_date', 'actual_start_date', 'actual_end_date', 'milestone']
    template_name = 'project_management/update_open_task.html'
    success_url = reverse_lazy('listProjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_id = int(self.request.GET['task_id'])
        task_name = self.request.GET['task_name']
        project_id = int(self.request.GET['project_id'])
        project = Project.objects.get(id=project_id)
        milestone_id = self.get_object().milestone_id

        task = Task.objects.get(id=task_id)
        context['task_id'] = task_id
        context['project_id'] = project_id
        context['milestone_id'] = milestone_id
        context['task_name'] = task_name

        if ProjectTeam.objects.filter(project_id=project.id).exists():
            team = ProjectTeam.objects.get(project_id=project_id)
            project_team = team.id
            team_members = ProjectTeamMember.objects.filter(project_team=project_team)
            member_list = list(team_members)
            old = []

            if len(member_list) != 0:
                for member in member_list:
                    old_user = User.objects.get(id=member.member_id)
                    old.append(old_user)

            context['members'] = old
        
        else:
            context['members'] = ""    
        
        return context


class UpdateOnholdTask(UpdateView):
    model = Task
    fields = ['name', 'status', 'description', 'start_date', 'end_date', 'actual_start_date', 'actual_end_date', 'milestone']
    template_name = 'project_management/update_onhold_task.html'
    success_url = reverse_lazy('listProjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_id = int(self.request.GET['task_id'])
        task_name = self.request.GET['task_name']
        project_id = int(self.request.GET['project_id'])
        project = Project.objects.get(id=project_id)
        milestone_id = self.get_object().milestone_id

        context['task_id'] = task_id
        context['project_id'] = project_id
        context['milestone_id'] = milestone_id
        context['task_name'] = task_name

        if ProjectTeam.objects.filter(project_id=project.id).exists():
            team = ProjectTeam.objects.get(project_id=project_id)
            project_team = team.id
            team_members = ProjectTeamMember.objects.filter(project_team=project_team)
            member_list = list(team_members)
            old = []

            if len(member_list) != 0:
                for member in member_list:
                    old_user = User.objects.get(id=member.member_id)
                    old.append(old_user)

            context['members'] = old
        
        else:
            context['members'] = ""

        return context


class UpdateCompletedTask(UpdateView):
    model = Task
    fields = ['name', 'status', 'description', 'start_date', 'end_date', 'actual_start_date', 'actual_end_date', 'milestone']
    template_name = 'project_management/update_completed_task.html'
    success_url = reverse_lazy('listProjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_id = int(self.request.GET['task_id'])
        task_name = self.request.GET['task_name']
        project_id = int(self.request.GET['project_id'])
        project = Project.objects.get(id=project_id)
        milestone_id = self.get_object().milestone_id

        context['task_id'] = task_id
        context['project_id'] = project_id
        context['milestone_id'] = milestone_id
        context['task_name'] = task_name

        if ProjectTeam.objects.filter(project_id=project.id).exists():
            team = ProjectTeam.objects.get(project_id=project_id)
            project_team = team.id
            team_members = ProjectTeamMember.objects.filter(project_team=project_team)
            member_list = list(team_members)
            old = []

            if len(member_list) != 0:
                for member in member_list:
                    old_user = User.objects.get(id=member.member_id)
                    old.append(old_user)

            context['members'] = old
        else:
            context['members'] = ""

        return context


class UpdateTerminatedTask(UpdateView):
    model = Task
    fields = ['name', 'status', 'description', 'start_date', 'end_date', 'actual_start_date', 'actual_end_date', 'milestone']
    template_name = 'project_management/update_terminated_task.html'
    success_url = reverse_lazy('listProjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_id = int(self.request.GET['task_id'])
        task_name = self.request.GET['task_name']
        project_id = int(self.request.GET['project_id'])
        project = Project.objects.get(id=project_id)
        milestone_id = self.get_object().milestone_id

        context['task_id'] = task_id
        context['project_id'] = project_id
        context['milestone_id'] = milestone_id
        context['task_name'] = task_name

        if ProjectTeam.objects.filter(project_id=project.id).exists():
            team = ProjectTeam.objects.get(project_id=project_id)
            project_team = team.id
            team_members = ProjectTeamMember.objects.filter(project_team=project_team)
            member_list = list(team_members)
            old = []

            if len(member_list) != 0:
                for member in member_list:
                    old_user = User.objects.get(id=member.member_id)
                    old.append(old_user)

            context['members'] = old
        else:
            context['members'] = ""

        return context


@login_required
def save_update_task(request, pk):
    """update project task"""
    name = request.GET.get('name')
    description = request.GET.get('description')
    status_id = int(request.GET.get('status'))
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    actual_start_date = request.GET.get('actual_start_date')
    actual_end_date = request.GET.get('actual_end_date')

    project_id = int(request.GET.get('project_id'))
    milestone_id = int(request.GET.get('milestone_id'))

    status = Status.objects.get(id=status_id)
    project = Project.objects.get(id=project_id)
    milestone = Milestone.objects.get(id=milestone_id)
    team = ProjectTeam.objects.get(project_id= project_id)

    if start_date is not "":
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    else:
        start_date = None

    if end_date is not "":
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    else:
        end_date = None

    if actual_start_date is not "":
        actual_start_date = datetime.datetime.strptime(actual_start_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    else:
        actual_start_date = None

    if actual_end_date is not "":
        actual_end_date = datetime.datetime.strptime(actual_end_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    else:
        actual_end_date = None

    task = Task.objects.get(id=int(pk))

    task.name = name
    task.status = status
    task.end_date = end_date
    task.start_date = start_date
    task.actual_start_date = actual_start_date
    task.actual_end_date = actual_end_date
    task.description = description
    task.project = project
    task.milestone = milestone
    task.save()

    open_status = Status.objects.get(name="Open")
    onhold_status = Status.objects.get(name="Onhold")
    terminated_status = Status.objects.get(name="Terminated")
    completed_status = Status.objects.get(name="Completed")

    if status == completed_status:
        completed_tasks = Task.objects.filter(project_id=project.id, status=completed_status)
        open_count = Task.objects.filter(project_id=project.id, status=open_status).count()
        onhold_count = Task.objects.filter(project_id=project.id, status=onhold_status).count()
        terminated_count = Task.objects.filter(project_id=project.id, status=terminated_status).count()
        completed_count = Task.objects.filter(project_id=project_id, status=completed_status).count()
        
        template = loader.get_template('project_management/completed_tasks.html')
        context = {
            'project_id': project_id,
            'project_name': project.name,
            'completed_tasks': completed_tasks,
            'open_count': open_count,
            'onhold_count': onhold_count,
            'terminated_count': terminated_count,
            'completed_count':completed_count
        }  

    elif status == terminated_status:
        terminated_tasks = Task.objects.filter(project_id=project.id, status=terminated_status)
        open_count = Task.objects.filter(project_id=project.id, status=open_status).count()
        onhold_count = Task.objects.filter(project_id=project.id, status=onhold_status).count()
        terminated_count = Task.objects.filter(project_id=project.id, status=terminated_status).count()
        completed_count = Task.objects.filter(project_id=project_id, status=completed_status).count()

        template = loader.get_template('project_management/terminated_tasks.html')
        context = {
            'project_id': project.id,
            'project_name': project.name,
            'terminated_tasks': terminated_tasks,
            'open_count': open_count,
            'onhold_count': onhold_count,
            'terminated_count': terminated_count,
            'completed_count':completed_count
        }

    elif status == onhold_status:
        onhold_tasks = Task.objects.filter(project_id=project.id, status=onhold_status)
        open_count = Task.objects.filter(project_id=project.id, status=open_status).count()
        onhold_count = Task.objects.filter(project_id=project.id, status=onhold_status).count()
        terminated_count = Task.objects.filter(project_id=project.id, status=terminated_status).count()
        completed_count = Task.objects.filter(project_id=project_id, status=completed_status).count()

        template = loader.get_template('project_management/onhold_tasks.html')
        context = {
            'project_id': project.id,
            'project_name': project.name,
            'onhold_tasks': onhold_tasks,
            'open_count': open_count,
            'onhold_count': onhold_count,
            'terminated_count': terminated_count,
            'completed_count':completed_count
        }

    elif status == open_status:
        open_tasks = Task.objects.filter(project_id=project.id, status=open_status)
        open_count = Task.objects.filter(project_id=project.id, status=open_status).count()
        onhold_count = Task.objects.filter(project_id=project.id, status=onhold_status).count()
        terminated_count = Task.objects.filter(project_id=project.id, status=terminated_status).count()
        completed_count = Task.objects.filter(project_id=project_id, status=completed_status).count()

        template = loader.get_template('project_management/open_tasks.html')
        context = {
            'project_id': project.id,
            'project_name': project.name,
            'open_tasks': open_tasks,
            'open_count': open_count,
            'onhold_count': onhold_count,
            'terminated_count': terminated_count,
            'completed_count':completed_count
        }

    else:
        context = {
            'project_id': project.id,
            'project_name': project.name,
        }

    return HttpResponse(template.render(context, request))


def assigned_task_members(request):
    """view members assigned tasks"""

    task_id = int(request.GET.get('task_id'))
    project_id = int(request.GET.get('project_id'))
    task = Task.objects.get(id=task_id)
    project = Project.objects.get(id=project_id)

    assigned_members = task.assigned_to.all()

    context = {
        'assigned_members': assigned_members,
        'task': task,
        'project_id': project.id,
        'milestone_id': task.milestone.id
    }

    return render(request, 'project_management/assigned_task_members.html', context)


def assigned_task_members_milestone(request):
    """view members assigned tasks"""

    task_id = int(request.GET.get('task_id'))
    project_id = int(request.GET.get('project_id'))
    task = Task.objects.get(id=task_id)
    project = Project.objects.get(id=project_id)

    assigned_members = task.assigned_to.all()

    context = {
        'assigned_members': assigned_members,
        'task': task,
        'project_id': project.id,
        'milestone_id': task.milestone.id
    }

    return render(request, 'project_management/assigned_task_members_milestone.html', context)


def check_team_members(request):
    """check if project team has members yet"""

    project_id = int(request.GET.get('project_id'))
    project = Project.objects.get(id=project_id)

    if ProjectTeam.objects.filter(project_id=project.id).exists():
        team = ProjectTeam.objects.get(project_id=project.id)
        project_team = team.id
        team_members = ProjectTeamMember.objects.filter(project_team=project_team)
        member_list = list(team_members)  

        if len(member_list) == 0:
            state = False
        else:
            state = True
    else:
        state = False

    data = {
        "state": state
    }

    return JsonResponse(data)


def check_assigned_task_members(request):
    """check if member is already assigned to task"""

    task_id = int(request.GET.get('task_id'))
    project_id = int(request.GET.get('project_id'))

    task = Task.objects.get(id=task_id)
    assigned_members = task.assigned_to.all()
    project = Project.objects.get(id=project_id)

    team = ProjectTeam.objects.get(project_id=project.id)
    project_team = team.id
    team_members = ProjectTeamMember.objects.filter(project_team=project_team)
    member_list = list(team_members)
    old = []
    
    for member in member_list:
        old_user = User.objects.get(id=member.member_id)
        old.append(old_user)

    members = old 
    assigned_list = list(assigned_members)
    assigned = []

    for member in assigned_list:
        assigned_user = User.objects.get(id=member.member_id)
        assigned.append(assigned_user)
    
    members = set(old).difference(set(assigned))   
    
    diff = list(members)
    
    if len(diff) == 0:
        team_state = False
    else:
        team_state = True
    
    data = {
        'team_state': team_state
    }

    return JsonResponse(data)


def assign_task_members(request):
    """ assign tasks to members """

    task_id = int(request.GET.get('task_id'))
    project_id = int(request.GET.get('project_id'))
    milestone_id = int(request.GET.get('milestone_id'))
    task = Task.objects.get(id=task_id)
    assigned_members = task.assigned_to.all()
    project = Project.objects.get(id=project_id)

    team = ProjectTeam.objects.get(project_id=project.id)
    project_team = team.id
    team_members = ProjectTeamMember.objects.filter(project_team=project_team)
    member_list = list(team_members)
    old = []

    if len(member_list) != 0:
        for member in member_list:
            old_user = User.objects.get(id=member.member_id)
            old.append(old_user)

        members = old

    else:
        members = ""
    

    if assigned_members.count() == 0:
        members = old
    else:
        assigned_list = list(assigned_members)
        assigned = []

        if len(assigned_list) != 0:
            for member in assigned_list:
                assigned_user = User.objects.get(id=member.member_id)
                assigned.append(assigned_user)

            
            members = set(old).difference(set(assigned))   
        else:
            members = ""

    template = loader.get_template('project_management/assign_member_task.html')
    context = {
        'project_id': project.id,
        'project_name': project.name,
        'members': members,
        'task_id': task.id,
        'milestone_id': milestone_id
    }

    return HttpResponse(template.render(context, request))


def save_members_assigned_task(request):
    """saving member attached to task"""

    task_id = int(request.GET.get('task_id'))
    project_id = int(request.GET.get('project_id'))
    milestone_id = int(request.GET.get('milestone_id'))
    member_list = json.loads(request.GET['memberlist'])

    task = Task.objects.get(id=task_id)
    project = Project.objects.get(id=project_id)
    team = ProjectTeam.objects.get(project_id=project_id)
    team_member = ProjectTeamMember.objects.filter(project_team=team)

    team_list = list(team_member)
    for user in team_list:

        for member in member_list:
            if member == user.member_id:
                task.assigned_to.add(user.id)
    
    assigned_members = task.assigned_to.all()

    context = {
        'assigned_members': assigned_members,
        'task': task,
        'project_id': project.id,
        'milestone_id': task.milestone.id
    }

    return render(request, 'project_management/assigned_task_members.html', context)

    
def deassign_task_members(request):
    """deassign tasks from members"""

    task_id = int(request.GET.get('task_id'))
    project_id = int(request.GET.get('project_id'))
    milestone_id = int(request.GET.get('milestone_id'))
    assigned_id = int(request.GET.get('assigned_id'))

    task = Task.objects.get(id=task_id)
    project = Project.objects.get(id=project_id)
    team = ProjectTeam.objects.get(project_id=project_id)
    team_member = ProjectTeamMember.objects.filter(project_team=team)

    team_list = list(team_member)
    for user in team_list:
        if assigned_id == user.member_id:
            task.assigned_to.remove(user.id)
    
    assigned_members = task.assigned_to.all()
    context = {
        'assigned_members': assigned_members,
        'task': task,
        'project_id': project.id,
        'milestone_id': task.milestone.id
    }

    return render(request, 'project_management/assigned_task_members.html', context)


def deassign_task_members_milestone(request):
    """deassign tasks from members under specific milestone"""

    task_id = int(request.GET.get('task_id'))
    project_id = int(request.GET.get('project_id'))
    milestone_id = int(request.GET.get('milestone_id'))
    assigned_id = int(request.GET.get('assigned_id'))

    task = Task.objects.get(id=task_id)
    project = Project.objects.get(id=project_id)
    team = ProjectTeam.objects.get(project_id=project_id)
    team_member = ProjectTeamMember.objects.filter(project_team=team)

    team_list = list(team_member)
    for user in team_list:
        if assigned_id == user.member_id:
            task.assigned_to.remove(user.id)
    
    assigned_members = task.assigned_to.all()
    context = {
        'assigned_members': assigned_members,
        'task': task,
        'project_id': project.id,
        'milestone_id': task.milestone.id
    }

    return render(request, 'project_management/assigned_task_members_milestone.html', context)


class UpdateMilestoneTask(UpdateView):
    model = Task
    fields = ['name', 'status', 'description', 'start_date', 'end_date', 'actual_start_date', 'actual_end_date', 'assigned_to', 'milestone']
    template_name = 'project_management/update_milestone_task.html'
    # success_url = reverse_lazy('listProjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_id = int(self.request.GET['task_id'])
        task_name = self.request.GET['task_name']
        project_id = int(self.request.GET['project_id'])
        project = Project.objects.get(id=project_id)
        milestone_id = self.get_object().milestone_id

        context['task_id'] = task_id
        context['project_id'] = project_id
        context['milestone_id'] = milestone_id
        context['task_name'] = task_name

        if ProjectTeam.objects.filter(project_id=project.id).exists():
            team = ProjectTeam.objects.get(project_id=project_id)
            project_team = team.id
            team_members = ProjectTeamMember.objects.filter(project_team=project_team)
            member_list = list(team_members)
            old = []

            if len(member_list) != 0:
                for member in member_list:
                    old_user = User.objects.get(id=member.member_id)
                    old.append(old_user)

            context['members'] = old

        else:
            context['members'] = ""

        return context


def tasklist_by_project(request):
    """
    Tasks allocated to project
    """
    project_id = int(request.GET.get('project_id'))
    project = get_object_or_404(Project, pk=(project_id))

    template = loader.get_template('project_management/list_project_tasks.html')

    tasks = Task.objects.filter(project_id= project_id).exists()
    state = True

    if Milestone.objects.filter(project_id=project_id).exists():
        
        project_tasks = Task.objects.filter(project_id=project.id)
        open_status = Status.objects.get(name="Open")
        open_tasks = Task.objects.filter(project_id=project.id, status=open_status)

        open_count = Task.objects.filter(project_id=project.id, status=open_status).count()

        onhold_status = Status.objects.get(name="Onhold")
        if Task.objects.filter(project_id=project.id, status=onhold_status).exists():
            onhold_count = Task.objects.filter(project_id=project.id, status=onhold_status).count()
        else:
            onhold_count = 0
        
        terminated_status = Status.objects.get(name="Terminated")
        if Task.objects.filter(project_id=project.id, status=terminated_status).exists():
            terminated_count = Task.objects.filter(project_id=project.id, status=terminated_status).count()
        else:
            terminated_count = 0

        completed_status = Status.objects.get(name="Completed")
        if Task.objects.filter(project_id=project.id, status=completed_status).exists():
            completed_count = Task.objects.filter(project_id=project.id, status=completed_status).count()
        else:
            completed_count = 0

        context = {
            'project_name': project.name,
            'project_id': project.id,
            'open_tasks': open_tasks,
            'state': state,
            'open_count': open_count,
            'onhold_count': onhold_count,
            'terminated_count': terminated_count,
            'completed_count': completed_count
        }

    else:
        state = False
        context = {
            'project_name': project.name,
            'project_id': project.id,
            'open_tasks': '',
            'state': False
        }

    return HttpResponse(template.render(context, request))


def open_project_tasks(request):
    """open project tasks"""
    project_id = request.GET.get("project_id")
    project = Project.objects.get(id=int(project_id))

    template = loader.get_template('project_management/open_tasks.html')

    tasks = Task.objects.filter(project_id= project_id).exists()
    state = True

    d3 = date.today()
    today = d3.strftime("%m %d, %Y")

    if Milestone.objects.filter(project_id=project_id).exists():
        
        project_tasks = Task.objects.filter(project_id=project.id)
        open_status = Status.objects.get(name="Open")
        open_tasks = Task.objects.filter(project_id=project.id, status=open_status).annotate(assigned=Count('assigned_to'))

        open_count = Task.objects.filter(project_id=project.id, status=open_status).count()

        onhold_status = Status.objects.get(name="Onhold")
        if Task.objects.filter(project_id=project.id, status=onhold_status).exists():
            onhold_count = Task.objects.filter(project_id=project.id, status=onhold_status).count()
        else:
            onhold_count = 0
        
        terminated_status = Status.objects.get(name="Terminated")
        if Task.objects.filter(project_id=project.id, status=terminated_status).exists():
            terminated_count = Task.objects.filter(project_id=project.id, status=terminated_status).count()
        else:
            terminated_count = 0

        completed_status = Status.objects.get(name="Completed")
        if Task.objects.filter(project_id=project.id, status=completed_status).exists():
            completed_count = Task.objects.filter(project_id=project.id, status=completed_status).count()
        else:
            completed_count = 0

        context = {
            'project_name': project.name,
            'project_id': project.id,
            'open_tasks': open_tasks,
            'state': state,
            'open_count': open_count,
            'onhold_count': onhold_count,
            'terminated_count': terminated_count,
            'completed_count': completed_count,
            'today':today
        }

    else:
        state = False
        context = {
            'project_name': project.name,
            'project_id': project.id,
            'open_tasks': '',
            'state': False
        }

    return HttpResponse(template.render(context, request))


def onhold_tasks(request):
    project_id = request.GET.get("project_id")
    project = get_object_or_404(Project, pk=int(project_id))

    template = loader.get_template('project_management/onhold_tasks.html')
    d3 = date.today()
    today = d3.strftime("%m %d, %Y")

    state = True
    onhold_status = Status.objects.get(name="Onhold")
    if Milestone.objects.filter(project_id=project_id).exists():
        if Task.objects.filter(project_id=project.id, status=onhold_status).exists():
            onhold_tasks = Task.objects.filter(project_id=project.id, status=onhold_status).annotate(assigned=Count('assigned_to'))

            context = {
                'project_name': project.name,
                'project_id': project.id,
                'onhold_tasks': onhold_tasks,
                'state': state,
                'today':today
            }
        else:
            context = {
                'project_name': project.name,
                'project_id': project.id,
                'onhold_tasks': "",
                'state': state,
            }

    else:
        state = False
        context = {
            'project_name': project.name,
            'project_id': project.id,
            'onhold_tasks': '',
            'state': False
        }

    return HttpResponse(template.render(context, request))


def terminated_tasks(request):
    project_id = request.GET.get("project_id")
    project = get_object_or_404(Project, pk=int(project_id))

    template = loader.get_template('project_management/terminated_tasks.html')
    d3 = date.today()
    today = d3.strftime("%m %d, %Y")

    state = True
    terminated_status = Status.objects.get(name="Terminated")

    if Milestone.objects.filter(project_id=project_id).exists():
        if Task.objects.filter(project_id= project_id, status=terminated_status).exists():
            terminated_tasks = Task.objects.filter(project_id=project.id, status=terminated_status).annotate(assigned=Count('assigned_to'))
            context = {
                'project_name': project.name,
                'project_id': project.id,
                'terminated_tasks': terminated_tasks,
                'state': state,
                'today': today
            }

        else:
            context = {
                'project_name': project.name,
                'project_id': project.id,
                'terminated_tasks': "",
                'state': state,
            } 
    
    else:
        state = False
        context = {
            'project_name': project.name,
            'project_id': project.id,
            'tasks': '',
            'state': False
        }

    return HttpResponse(template.render(context, request))


def completed_tasks(request):
    project_id = request.GET.get("project_id")
    project = get_object_or_404(Project, pk=int(project_id))

    template = loader.get_template('project_management/completed_tasks.html')
    d3 = date.today()
    today = d3.strftime("%m %d, %Y")

    state = True
    completed_status = Status.objects.get(name="Completed")

    if Milestone.objects.filter(project_id=project_id).exists():
        if Task.objects.filter(project_id=project.id, status=completed_status).exists():
            completed_tasks = Task.objects.filter(project_id=project.id, status=completed_status).annotate(assigned=Count('assigned_to'))

            context = {
                'project_name': project.name,
                'project_id': project.id,
                'completed_tasks': completed_tasks,
                'state': state,
                'today': today
            }

        else:
            context = {
                'project_name': project.name,
                'project_id': project.id,
                'completed_tasks': "",
                'state': state
            }

    else:
        state = False
        context = {
            'project_name': project.name,
            'project_id': project.id,
            'completed_tasks': '',
            'state': False
        }

    return HttpResponse(template.render(context, request))


def task_count(request):
    """returning the task count based on status of task"""

    project_id = int(request.GET.get('project_id'))
    project = Project.objects.get(id=project_id)

    template = loader.get_template('project_management/open_tasks.html')

    tasks = Task.objects.filter(project_id= project_id).exists()
        
    project_tasks = Task.objects.filter(project_id=project.id)
    open_status = Status.objects.get(name="Open")
    if Task.objects.filter(project_id=project.id, status=open_status).exists():
        open_count = Task.objects.filter(project_id=project.id, status=open_status).count()
    else:
        open_count = 0

    onhold_status = Status.objects.get(name="Onhold")
    if Task.objects.filter(project_id=project.id, status=onhold_status).exists():
        onhold_count = Task.objects.filter(project_id=project.id, status=onhold_status).count()
    else:
        onhold_count = 0
    
    terminated_status = Status.objects.get(name="Terminated")
    if Task.objects.filter(project_id=project.id, status=terminated_status).exists():
        terminated_count = Task.objects.filter(project_id=project.id, status=terminated_status).count()
    else:
        terminated_count = 0

    completed_status = Status.objects.get(name="Completed")
    if Task.objects.filter(project_id=project.id, status=completed_status).exists():
        completed_count = Task.objects.filter(project_id=project.id, status=completed_status).count()
    else:
        completed_count = 0

    data = {
        'open_count': open_count,
        'onhold_count': onhold_count,
        'terminated_count': terminated_count,
        'completed_count': completed_count
    }

    return JsonResponse(data)


class DetailsProjectTask(DetailView):
    model = Task
    context_name = 'task'
    template_name = 'project_management/details_project_tasks.html'


def delete_task(request):
    """
    delete task
    """
    task_name = request.GET.get('task_name')
    task_id = int(request.GET.get('task_id'))

    task = Task.objects.filter(id=task_id)
    task.delete()

    response_data = {
        "success": True,
        "message": "Successfully deleted"
    }

    return JsonResponse(response_data)


class TaskListView(ListView, LoginRequiredMixin):
    template_name = 'project_management/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        user = self.request.user
        members = ProjectTeamMember.objects.filter(member=user)
        team_list = []
        for value in members:  
            team_members = ProjectTeamMember.project_team.through.objects.filter(projectteammember=value.id)

            for obj in team_members:
                team_name = obj.projectteam
                team_list.append(team_name)
        
        project_list = []
        task_list = []
        for team in team_list:
            project_id = team.project_id
            
            project = Project.objects.get(id=project_id)

            tasks = Task.objects.filter(project_id=project.id)
            
            for task in tasks:
                task_list.append(tasks)
            
            return task_list



@login_required
def task_list_by_users(request):
    """return tasks assigned to user"""
    user = request.user
    members = ProjectTeamMember.objects.filter(member=user)
    
    task_list = []
    team_list = []
    for value in members:  
        team_members = ProjectTeamMember.project_team.through.objects.filter(projectteammember=value.id)

        for obj in team_members:
            team_name = obj.projectteammember
            team_list.append(team_name)
    
    for team in team_list:
        assigned_to = Task.assigned_to.through.objects.filter(projectteammember_id=team.id).values()

        for value in assigned_to:
            task_id = value["task_id"]
            tasks = Task.objects.filter(id=task_id)

            for task in tasks:   
                task_list.append(task)

    template = loader.get_template('project_management/task_list.html')
    context = {
        'tasks': task_list
    }

    return HttpResponse(template.render(context, request))


def task_list_by_milestone(request, milestone_id):
    milestone_tasks = Task.objects.filter(milestone_id=milestone_id)
    return render(request, 'project_management/task_list.html', {'tasks': milestone_tasks})


class TaskUpdateView(UpdateView):
    model = Task
    template_name = 'project_management/task_update_form.html'
    form_class = TaskForm

    # id = self.request.GET.get('id',None)
    # task_id = self.kwargs['pk']
    # milestone_id =

    def get_object1(self, queryset=None):
        obj = Task.objects.get(id=self.kwargs['pk'])
        #     print('Milestone Id is : '+str(obj.milestone_id))
        #     milestone_obj = Model.objects.get(id=obj.milestone_id)
        #     milestone_obj.status = 'Completed'
        #     milestone_obj.save()
        #     return obj
        milestone_obj = Milestone.objects.get(id=obj.milestone_id)
        print(milestone_obj.completion)

    success_url = reverse_lazy('task_list')


class TaskDetailView(DetailView):

    def get_queryset(self):
        return Task.objects.all()


def load_task_milestones(request):
    project_id = request.GET.get('project')
    milestones = Milestone.objects.filter(project_id=project_id).order_by('name')
    return render(request, 'project_management/task_milestone_dropdown_list_options.html', {'milestones': milestones})


@login_required
def tasks_container(request):
    """return tasks assigned to user"""
    user = request.user
    members = ProjectTeamMember.objects.filter(member=user)
    
    task_list = []
    team_list = []
    for value in members:  
        team_members = ProjectTeamMember.project_team.through.objects.filter(projectteammember=value.id)

        for obj in team_members:
            team_name = obj.projectteammember
            team_list.append(team_name)
    
    for team in team_list:
        assigned_to = Task.assigned_to.through.objects.filter(projectteammember_id=team.id).values()

        for value in assigned_to:
            task_id = value["task_id"]
            tasks = Task.objects.filter(id=task_id)

            for task in tasks:   
                task_list.append(task)

    template = loader.get_template('project_management/task_list_container.html')
    context = {
        "tasks":task_list
    }

    return HttpResponse(template.render(context, request))


# INCIDENTS
class AddProjectIncident(LoginRequiredMixin, CreateView):
    model = Incident
    fields = ['project', 'name', 'description', 'status', 'priority', 'assigned_to', 'document', 'image',]
    template_name = 'project_management/add_project_incident.html'
    success_url = reverse_lazy('listProjects')

    def form_valid(self, form):
        """auto registering loggedin user"""
        form.instance.creator = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = int(self.request.GET['project_id'])
        project_name = self.request.GET['project_name']
        context['project_id'] = project_id
        context['project_name'] = project_name

        team = ProjectTeam.objects.get(project_id=project_id)
        project_team = team.id
        team_members = ProjectTeamMember.objects.filter(project_team=project_team)
        member_list = list(team_members)
        old = []

        if len(member_list) != 0:
            for member in member_list:
                old_user = User.objects.get(id=member.member_id)
                old.append(old_user)

        context['members'] = old

        return context


class AddIncident(LoginRequiredMixin, CreateView):
    model = Incident
    fields = ['project', 'name', 'description', 'status', 'priority', 'assigned_to', 'document', 'image',]
    template_name = 'project_management/add_incident.html'
    success_url = reverse_lazy('listIncidents')

    def form_valid(self, form):
        """auto registering loggedin user"""
        form.instance.creator = self.request.user
        return super().form_valid(form)


def list_project_incidents(request):
    """
    incident for specific project
    """
    project_id = request.GET.get('project_id')
    
    template = loader.get_template('project_management/list_project_incidents.html')

    project = Project.objects.get(id=project_id)
    state = True

    if ProjectTeam.objects.filter(project_id=project_id).exists():
        team = ProjectTeam.objects.get(project_id=project.id)
        team_id = team.id
        team_members = ProjectTeamMember.objects.filter(project_team=team_id)
        if team_members:
            if Incident.objects.filter(project_id=project.id).exists():
                team_member = ProjectTeamMember.objects.filter(member=request.user, project_team=team_id)

                open_status = Status.objects.get(name="Open")
                open_count = Incident.objects.filter(project_id=project.id, status=open_status).count()

                onhold_status = Status.objects.get(name="Onhold")
                onhold_count = Incident.objects.filter(project_id=project.id, status=onhold_status).count()

                terminated_status = Status.objects.get(name="Terminated") 
                terminated_count = Incident.objects.filter(project_id=project.id, status=terminated_status).count()

                completed_status = Status.objects.get(name="Completed")                
                completed_count = Incident.objects.filter(project_id=project.id, status=completed_status).count()

                open_incidents = Incident.objects.filter(Q(creator=request.user)|Q(assigned_to__in=team_member), project_id=project.id, status=open_status).annotate(assigned=Count('assigned_to', distinct=True))
                state = True
                context = {
                    'project_id': project.id,
                    'project_name': project.name,
                    'open_incidents': open_incidents,
                    'state': state,
                    'team_id': team_id,
                    'open_count': open_count,
                    'completed_count': completed_count,
                    'terminated_count': terminated_count,
                    'onhold_count': onhold_count
                }

                return HttpResponse(template.render(context, request))
        
            else:
                state=True
                context={
                    'project_id': project.id,
                    'project_name': project.name,
                    'incidents': '',
                    'state': state, 
                    'team_id': team_id
                }
                return HttpResponse(template.render(context, request))

        else:
            state = False
            context={
                    'project_id': project.id,
                    'project_name': project.name,
                    'state':state
                }
            return HttpResponse(template.render(context, request))
    else:
        state = False
        context={
                'project_id': project.id,
                'project_name': project.name,
                'state':state
            }
        return HttpResponse(template.render(context, request))


class DetailsIncident(DetailView):
    model = Incident
    context_object_name = 'incident'
    template_name = 'project_management/details_incident.html'


class DetailsProjectIncident(DetailView):
    model = Incident
    context_object_name = 'incident'
    template_name = 'project_management/details_project_incident.html'


class UpdateIncident(UpdateView):
    model = Incident
    fields = ['project', 'name', 'description', 'document', 'image', 'status', 'priority', 'assigned_to',]
    template_name = 'project_management/update_incident.html'
    success_url = reverse_lazy('listIncidents')


class UpdateProjectIncident(UpdateView):
    model = Incident
    fields = ['name', 'description', 'document', 'image', 'status', 'priority', 'assigned_to',]
    template_name = 'project_management/update_project_incident.html'
    success_url = reverse_lazy('listIncidents')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        incident_id = int(self.request.GET['incident_id'])
        project_id = int(self.request.GET['project_id'])
        context['incident_id'] = incident_id
        context['project_id'] = project_id

        team = ProjectTeam.objects.get(project_id=project_id)
        project_team = team.id
        team_members = ProjectTeamMember.objects.filter(project_team=project_team)
        member_list = list(team_members)
        old = []

        if len(member_list) != 0:
            for member in member_list:
                old_user = User.objects.get(id=member.member_id)
                old.append(old_user)

        context['members'] = old
        return context

    # def get_success_url(self):
    #     return reverse_lazy('listProjectIncidents', kwargs={'pk': self.object.project_id})


def completed_project_incidents(request):
    """
    incident for specific project
    """
    project_id = request.GET.get('project_id')
    
    template = loader.get_template('project_management/completed_incidents.html')

    project = Project.objects.get(id=project_id)
    state = True

    if ProjectTeam.objects.filter(project_id=project_id).exists():
        team = ProjectTeam.objects.get(project_id=project.id)
        team_id = team.id
        team_members = ProjectTeamMember.objects.filter(project_team=team_id)
        if team_members:
            if Incident.objects.filter(project_id=project.id).exists():
                team_member = ProjectTeamMember.objects.filter(member=request.user, project_team=team_id)
                completed_status = Status.objects.get(name="Completed")                
                completed_incidents = Incident.objects.filter(Q(creator=request.user)|Q(assigned_to__in=team_member), project_id=project.id, status=completed_status).annotate(assigned=Count('assigned_to', distinct=True))
                state = True
                context = {
                    'project_id': project.id,
                    'project_name': project.name,
                    'completed_incidents': completed_incidents,
                    'state': state,
                    'team_id': team_id
                }

                return HttpResponse(template.render(context, request))
        
            else:
                state=True
                context={
                    'project_id': project.id,
                    'project_name': project.name,
                    'incidents': '',
                    'state': state, 
                    'team_id': team_id
                }
                return HttpResponse(template.render(context, request))

        else:
            state = False
            context={
                    'project_id': project.id,
                    'project_name': project.name,
                    'state':state
                }
            return HttpResponse(template.render(context, request))
    else:
        state = False
        context={
                'project_id': project.id,
                'project_name': project.name,
                'state':state
            }
        return HttpResponse(template.render(context, request))


def onhold_project_incidents(request):
    """
    incident for specific project
    """
    project_id = request.GET.get('project_id')
    
    template = loader.get_template('project_management/onhold_incidents.html')

    project = Project.objects.get(id=project_id)
    state = True

    if ProjectTeam.objects.filter(project_id=project_id).exists():
        team = ProjectTeam.objects.get(project_id=project.id)
        team_id = team.id
        team_members = ProjectTeamMember.objects.filter(project_team=team_id)
        if team_members:
            if Incident.objects.filter(project_id=project.id).exists():
                team_member = ProjectTeamMember.objects.filter(member=request.user, project_team=team_id)
                onhold_status = Status.objects.get(name="Onhold")
                
                onhold_incidents = Incident.objects.filter(Q(creator=request.user)|Q(assigned_to__in=team_member), project_id=project.id, status=onhold_status).annotate(assigned=Count('assigned_to', distinct=True))
                state = True
                context = {
                    'project_id': project.id,
                    'project_name': project.name,
                    'onhold_incidents': onhold_incidents,
                    'state': state,
                    'team_id': team_id
                }

                return HttpResponse(template.render(context, request))
        
            else:
                state=True
                context={
                    'project_id': project.id,
                    'project_name': project.name,
                    'onhold_incidents': '',
                    'state': state, 
                    'team_id': team_id
                }
                return HttpResponse(template.render(context, request))

        else:
            state = False
            context={
                    'project_id': project.id,
                    'project_name': project.name,
                    'state':state
                }
            return HttpResponse(template.render(context, request))
    else:
        state = False
        context={
                'project_id': project.id,
                'project_name': project.name,
                'state':state
            }
        return HttpResponse(template.render(context, request))


def terminated_project_incidents(request):
    """
    incident for specific project
    """
    project_id = request.GET.get('project_id')
    
    template = loader.get_template('project_management/terminated_incidents.html')

    project = Project.objects.get(id=int(project_id))
    state = True

    if ProjectTeam.objects.filter(project_id=project_id).exists():
        team = ProjectTeam.objects.get(project_id=project.id)
        team_id = team.id
        team_members = ProjectTeamMember.objects.filter(project_team=team_id)
        if team_members:
            if Incident.objects.filter(project_id=project.id).exists():
                team_member = ProjectTeamMember.objects.filter(member=request.user, project_team=team_id)
                terminated_status = Status.objects.get(name="Terminated") 
                terminated_incidents = Incident.objects.filter(Q(creator=request.user)|Q(assigned_to__in=team_member), project_id=project.id, status=terminated_status).annotate(assigned=Count('assigned_to', distinct=True))
                state = True
                context = {
                    'project_id': project.id,
                    'project_name': project.name,
                    'terminated_incidents': terminated_incidents,
                    'state': state,
                    'team_id': team_id
                }

                return HttpResponse(template.render(context, request))
        
            else:
                state=True
                context={
                    'project_id': project.id,
                    'project_name': project.name,
                    'terminated_incidents': '',
                    'state': state, 
                    'team_id': team_id
                }
                return HttpResponse(template.render(context, request))

        else:
            state = False
            context={
                    'project_id': project.id,
                    'project_name': project.name,
                    'state':state
                }
            return HttpResponse(template.render(context, request))
    else:
        state = False
        context={
                'project_id': project.id,
                'project_name': project.name,
                'state':state
            }
        return HttpResponse(template.render(context, request))


def view_assigned_members(request):
    incident_id = request.GET.get('incident_id')
    project_id = request.GET.get('project_id')
    team_id = request.GET.get('team_id')

    team_members = Incident.assigned_to.through.objects.filter(id=incident_id)

    team = []
    users = []

    for member in team_members: 
        t = ProjectTeamMember.objects.get(id=member.projectteammember_id)
        team.append(t)

    for user in team:
        team_user = User.objects.get(id=user.member_id)
        users.append(team_user)

    context = {
        "team_members": users,
        "project_id": project_id
    }

    return render(request, 'project_management/assigned_incident_members.html', context)



@login_required
def incident_container(request):
    """return incidents assigned to user"""
    
    template = loader.get_template('project_management/list_incidents_container.html')
    context = {}

    return HttpResponse(template.render(context, request))


def create_incident(request):
    """create incident"""

    projects = Project.objects.all()
    template = loader.get_template('project_management/incident_form.html')
    context = {
        "projects":projects
    }

    return HttpResponse(template.render(context, request))


def save_incident(request):
    """save incident """
    project_id = int(request.GET.get('project_id'))
    name = request.GET.get('name')
    description = request.GET.get('description')
    created_by = request.user.id

    response_data = {}

    project = Project.objects.get(id=project_id)

    if description == "":
        description = None
    
    incident = Incident(name=name, description=description,  project_id=project.id, creator_id=created_by)
    incident.save()
    
    response_data['success'] = "Issue Has Been Submitted"
    response_data['name'] = incident.name
    response_data['state'] = True

    return JsonResponse(response_data)


def list_incidents_by_project(request):
    incidents = Incident.objects.all()
    template = loader.get_template('project_management/list_incidents.html')
    context = {
        "incidents":incidents
    }

    return HttpResponse(template.render(context, request))



# Add Incident Comments
def add_comment(request):
    if request.method == 'POST' and request.is_ajax():
        file_data = request.FILES.get('docs', None)
        data = request.POST.copy()
        incident = data.get('incident')
        comment = data.get('comment')
        created_by = request.user.id

        db_incident = Incident.objects.get(id=int(incident))
        creator = User.objects.get(id=created_by)
        new_comment = IncidentComment(comment=comment, incident=db_incident, created_by=creator, attachment=file_data)
        new_comment.save()

        data = {
            'success': True, 
            'message': 'Posted Successfully',
            'comment': new_comment.comment,
            'created_by': creator.first_name +" "+ creator.last_name,
            'time_created': new_comment.created_time
        }

        return JsonResponse(data)


def list_incident_comments(request):
    """
    list comments of given incident
    """
    incident_id = request.GET.get('incident_id')

    incident_comments = IncidentComment.objects.filter(incident_id=int(incident_id))

    data = {
        'all_comments': serializers.serialize("json", incident_comments),
    }

    return JsonResponse(data)


def get_team_members(request):
    """display team members on incident assigning"""

    project_id = request.GET.get('project')

    team = ProjectTeam.objects.filter(project_id=int(project_id)).exists()

    if team == True:
        project_team = ProjectTeam.objects.get(project_id=int(project_id))
        project_members_exist = ProjectTeamMember.objects.filter(project_team=project_team.id).exists()

        if project_members_exist == True:
            project_members = ProjectTeamMember.objects.filter(project_team=project_team.id)

            new_list = []

            for i in project_members:
                new_dict = {}
                new_dict['first_name'] = i.member.first_name
                new_dict['last_name'] = i.member.last_name
                new_dict['id'] = i.pk
                new_list.append(new_dict)

            data = {
                'team_members': new_list
            }
            return JsonResponse(data)

        else:
            data = {
                'team_members': ''
            }

    else:
        data = {
            'team_members': ''
        }

    return JsonResponse(data)


def set_priority_color_code(request):
    """ retrieving priority name"""

    priority_id = request.GET.get('priority')
    data = {}

    if priority_id is not None:
        priority = Priority.objects.get(id=int(priority_id))
        data['name'] = priority.name
        data['color'] = priority.color

    else:
        data['name'] = ''
        data['color'] = ''


    return JsonResponse(data)


def Milestone_progress():
    total_milestones = Milestone.objects.all()
    print(total_milestones)


def ongoingProjects(request):
    return render(request, 'project_management/ongoingprojects.html')


def listOfMilesoneIncidents(request):
    return render(request, 'project_management/milestoneincidents.html')


def listOfTaskIncidents(request):
    return render(request, 'project_management/taskincidents.html')


def previousProjects(request):
    return render(request, 'project_management/previousprojects.html')


def newProject(request):
    return render(request, 'project_management/newproject.html')


class ListAllPriorities(ListView):
    template_name = 'project_management/list_all_priorities.html'
    context_object_name = 'list_priorities'

    def get_queryset(self):
        return Priority.objects.all()


class AddPriority(CreateView):
    model = Priority
    fields = ['name', 'description', 'color']
    template_name = 'project_management/add_priority.html'
    success_url = reverse_lazy('listAllPriorities')


class UpdatePriority(UpdateView):
    model = Priority
    fields = ['name', 'description', 'color']
    template_name = 'project_management/update_priority.html'
    success_url = reverse_lazy('listAllPriorities')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        priorityid = int(self.request.GET['priorityid'])
        context['priorityid'] = priorityid
        return context


class DeletePriority(DeleteView):
    model = Priority
    success_url = reverse_lazy('listAllPriorities')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


def validatePriorityName(request):
    priority_name = request.GET.get('priorityname', None)
    data = {
        'is_taken': Priority.objects.filter(name=priority_name).exists()
    }
    return JsonResponse(data)


# STATUSES
class ListAllStatuses(ListView):
    template_name = 'project_management/list_all_statuses.html'
    context_object_name = 'list_status'

    def get_queryset(self):
        return Status.objects.all()


class AddStatus(CreateView):
    model = Status
    fields = ['name', 'description']
    template_name = 'project_management/add_status.html'
    success_url = reverse_lazy('listAllStatuses')


class UpdateStatus(UpdateView):
    model = Status
    fields = ['name', 'description']
    template_name = 'project_management/update_status.html'
    success_url = reverse_lazy('listAllStatuses')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        statusid = int(self.request.GET['statusid'])
        context['statusid'] = statusid
        return context


class DeleteStatus(DeleteView):
    model = Status
    success_url = reverse_lazy('listAllStatuses')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


def ValidateStatusName(request):
    status_name = request.GET.get('statusname', None)
    data = {
        'is_taken': Status.objects.filter(name=status_name).exists()
    }
    return JsonResponse(data)


# PROJECT LIST    
def addProject(request):
    if request.method == 'POST':
        project_form = ProjectForm(request.POST, request.FILES)
    
        if project_form.is_valid():
            data = request.POST.copy()
            name = data.get('name')
            description = data.get('description')
            project_code = data.get('project_code')
            estimated_cost = data.get('estimated_cost')
            company = data.getlist('company')
            department = data.getlist('department')
            logo = request.FILES.get('logo', None)
            start_date = data.get('estimated_start_date')
            end_date = data.get('estimated_end_date')
            project_status = data.get('project_status')
            created_by = request.user.id 

            project_count = Project.objects.all().count()            
            project_number = project_count + 1

            test_string = str(project_number)

            # only pick short year
            current_year_short = datetime.datetime.now().strftime('%y')
            str_date = str(current_year_short)
            
            result = ""
            final_result_code = ""

            # retrieve project code format from database
            codes = ProjectCode.objects.all().first()
            code = codes.project_code

            if len(project_code) != 0:
                final_result_code = project_code
            else:
                if len(test_string) ==  1:
                    N=2
                    result = test_string.zfill(N + len(test_string)) 
                    final_result_code = code + "/" + str_date + "/" + result
                elif len(test_string) == 2:
                    N=1
                    result = test_string.zfill(N + len(test_string)) 
                    final_result_code = code + "/"  + str_date + "/" + result
                else:
                    result = test_string
                    final_result_code = code + "/"  + str_date + "/" + result


            if estimated_cost == "":
                estimated_cost = 0;
            
            if start_date == "":
                start_date = None
                estimated_start_date = None
            else:
                estimated_start_date = datetime.datetime.strptime(start_date, "%m/%d/%Y").strftime("%Y-%m-%d")
                
            if end_date == "":
                end_date = None
                estimated_end_date = None
            else:
                estimated_end_date = datetime.datetime.strptime(end_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            
            if project_status == "":
                status = None
            else:            
                status = Status.objects.get(id=project_status)

            estimate = float(estimated_cost)
            user_id = User.objects.get(id=created_by)

            project = Project(name=name, description=description, project_code=final_result_code, estimated_cost=estimate,
            logo=logo, estimated_start_date=estimated_start_date, estimated_end_date=estimated_end_date,
            project_status=status, created_by=user_id)

            project.save()
            for value in company:
                p = project.company.add(value)

            for dept in department:
                d = project.department.add(dept)
                
            return redirect('listProjects')
    else:
        project_form = ProjectForm()

    return render(request, 'project_management/add_project.html', {
            'project_form': project_form,
    })


# class ListProjects(ListView):
#     template_name = 'project_management/list_projects.html'
#     context_object_name = 'all_projects'

#     def get_queryset(self):
#         return Project.objects.all()


def list_projects(request):
    company_id = request.session['company_id']

    # project_list = Project.objects.filter(company=int(company_id))
    project_list = Project.objects.all()
    
    template = loader.get_template('project_management/list_projects.html')
    context = {
        'all_projects': project_list
    }

    return HttpResponse(template.render(context, request))


class UpdateProject(UpdateView):
    model = Project
    fields = ['name', 'project_status', 'company', 'project_code', 'final_cost', 'estimated_start_date', 'estimated_end_date', 'actual_start_date', 'actual_end_date', 'description', 'logo', 'is_active']
    template_name = 'project_management/update_project.html'
    success_url = reverse_lazy('listProjects')


class DetailProject(DetailView):
    model = Project
    context_object_name = 'project'
    template_name = 'project_management/details_project.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs['pk']

        if ProjectTeam.objects.filter(project_id=project_id).exists():
            obj1 = ProjectTeam.objects.filter(project_id=project_id).values('id').first()
            project_team_id = obj1['id']

            if ProjectTeamMember.objects.filter(project_team=project_team_id, member_id=self.request.user.id).exists():
                forum_status = True
            else:
                forum_status = False
        else:
            forum_status = False

        context['forum_status'] = forum_status

        # total incident count
        incident_count = Incident.objects.filter(project_id=project_id).count()
        task_count = Task.objects.filter(project_id=project_id).count()
        milestone_count = Milestone.objects.filter(project_id=project_id).count()

        # status whether open, onhold, completed, or terminated
        open_status = Status.objects.get(name="Open")
        onhold_status = Status.objects.get(name="Onhold")
        complete_status = Status.objects.get(name="Completed")
        terminated_status = Status.objects.get(name="Terminated")

        # tasks
        open_tasks = Task.objects.filter(project_id=project_id, status_id=open_status.id).count()
        onhold_tasks = Task.objects.filter(project_id=project_id, status_id=onhold_status.id).count()
        completed_tasks = Task.objects.filter(project_id=project_id, status_id=complete_status.id).count()
        terminated_tasks = Task.objects.filter(project_id=project_id, status_id=terminated_status.id).count()

        # milestones
        open_milestones = Milestone.objects.filter(project_id=project_id, status_id=open_status.id).count()
        onhold_milestones = Milestone.objects.filter(project_id=project_id, status_id=onhold_status.id).count()
        completed_milestones = Milestone.objects.filter(project_id=project_id, status_id=complete_status.id).count()
        terminated_milestones = Milestone.objects.filter(project_id=project_id, status_id=terminated_status.id).count()

        # incidents
        open_incidents = Incident.objects.filter(project_id=project_id, status=open_status.id).count()
        onhold_incidents = Incident.objects.filter(project_id=project_id, status=onhold_status.id).count()
        completed_incidents = Incident.objects.filter(project_id=project_id, status=complete_status.id).count()
        terminated_incidents = Incident.objects.filter(project_id=project_id, status=terminated_status.id).count()

        # overall total count context
        context['incident_count'] = incident_count
        context['task_count'] = task_count
        context['milestone_count'] = milestone_count

        # task context
        context['open_tasks'] = open_tasks
        context['onhold_tasks'] = onhold_tasks
        context['completed_tasks'] = completed_tasks
        context['terminated_tasks'] = terminated_tasks

        # milestone context
        context['open_milestones'] = open_milestones
        context['onhold_milestones'] = onhold_milestones
        context['completed_milestones'] = completed_milestones
        context['terminated_milestones'] = terminated_milestones

        # incident context
        context['open_incidents'] = open_incidents
        context['onhold_incidents'] = onhold_incidents
        context['completed_incidents'] = completed_incidents
        context['terminated_incidents'] = terminated_incidents

        return context


def validateProjectName(request):
    project_name = request.GET.get('projectname', None)
    data = {
        'is_taken': Project.objects.filter(name=project_name).exists()
    }
    return JsonResponse(data)


class UploadDocument(LoginRequiredMixin, CreateView):
    model = ProjectDocument
    fields = ['title', 'document_description', 'document', 'project']
    success_url = reverse_lazy("listProjects")
    template_name = 'project_management/upload_document.html'

    def form_valid(self, form):
        """auto registering loggedin user"""
        form.instance.created_by = self.request.user
        return super().form_valid(form)


# PROJECT TEAMS
def add_project_team(request):
    """
    view to add a project_team
    """

    project_id = request.GET.get('project_id')
    project_name = request.GET.get('project_name')
    team_name = request.GET.get('team_name')

    template = loader.get_template('project_management/project_team.html')

    team = ProjectTeam(name=team_name, project_id=project_id)
    team.save()
    team_id = team.id

    context = {
        'team_name': team_name,
        'project_name': project_name,
        'project_id': project_id,
        'team_id': team_id,
        'state': True
    }

    return HttpResponse(template.render(context, request))


def list_project_team(request):
    """
    list team members on choosing project
    """
    project_id = request.GET.get('project_id')
    
    template = loader.get_template('project_management/project_team.html')

    project = Project.objects.get(id=project_id)

    if ProjectTeam.objects.filter(project_id=project.id).exists():
        team = ProjectTeam.objects.get(project_id=project.id)
        state = True
        project_team_id = team.id

        team_members = ProjectTeamMember.objects.filter(project_team=team.id)

        context = {
            'project_id': project.id,
            'project_name': project.name,
            'team_name': team.name,
            'team_id': project_team_id,
            'state': state,
            'members': team_members
        }

        return HttpResponse(template.render(context, request))
        
    else:
        state = False
        context = {
            'project_id': project.id,
            'project_name': project.name,
            'state': state
        }
        return render(request, 'project_management/project_team.html', context=context)

    return render(request, 'project_management/project_team.html', context=None)


class AdminAddProjectTeam(CreateView):
    model = ProjectTeam
    fields = ['name', 'project']
    template_name = 'project_management/add_project_team.html'
    success_url = reverse_lazy('listProjectTeams')


class ListProjectTeams(ListView):
    template_name = 'project_management/list_project_teams.html'
    context_object_name = 'project_teams'

    def get_queryset(self):
        return ProjectTeam.objects.annotate(num_members=Count('projectteammember'))


class UpdateProjectTeam(UpdateView):
    model = ProjectTeam
    fields = ['name', 'project']
    template_name = 'project_management/update_project_team.html'
    success_url = reverse_lazy('listProjectTeams')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teamid = int(self.request.GET['teamid'])
        context['teamid'] = teamid
        return context


class DeleteProjectTeam(DeleteView):
    model = ProjectTeam
    success_url = reverse_lazy('listProjectTeams')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


def validateProjectTeamName(request):
    team_name = request.GET.get('teamname', None)
    data = {
        'is_taken': ProjectTeam.objects.filter(name=team_name).exists()
    }
    return JsonResponse(data)


def validateProjectAssigned(request):
    """check to see if project already assigned team"""

    project = request.GET.get('project', None)
    team = ProjectTeam.objects.filter(project=project).exists()
    data = {
        'is_assigned': ProjectTeam.objects.filter(project=project).exists()
    }

    return JsonResponse(data)


def check_project_team(request):
    project_name = request.GET.get('projectname')
    project_id = request.GET.get('projectid')
    template = loader.get_template('project_management/project_team.html')


# PROJECT TEAM MEMBERS
def add_project_team_member(request):
    team_id = request.GET.get('team_id')
    team_name = request.GET.get('team_name')
    project_id = request.GET.get('project_id')
    project_name = request.GET.get('project_name')
    
    
    template = loader.get_template('project_management/add_team_member.html')
    context = {
        'team_name': team_name,
        'team_id': team_id,
        'project_id': project_id,
        'project_name': project_name
    }

    return HttpResponse(template.render(context, request))


def admin_add_project_team_member(request):
    team_id = request.GET.get('team_id')
    team_name = request.GET.get('team_name')
    project_id = request.GET.get('project_id')
    project_name = request.GET.get('project_name')
    
    
    template = loader.get_template('project_management/add_project_team_member.html')
    context = {
        'team_name': team_name,
        'team_id': team_id,
        'project_id': project_id,
        'project_name': project_name
    }

    return HttpResponse(template.render(context, request))


def save_team_member(request):
    team_id = request.GET.get('project_team')
    member = request.GET.get('member')
    project_id = request.GET.get('project_id')

    user = User.objects.get(id=member)
    team = ProjectTeam.objects.get(id=team_id)

    team_member = ProjectTeamMember(member=user)
    team_member.save()
    team_member.project_team.add(team)

    response_data = {
        'success': 'added successfully',
        'state': True,
        "name": user.first_name + " " + user.last_name
    }
    
    return JsonResponse(response_data)
    

class ListProjectTeamMembers(ListView):
    template_name = 'project_management/list_project_teams.html'
    context_object_name = 'project_teams'

    def get_queryset(self): 
        return ProjectTeam.objects.annotate(num_members=Count('projectteammember'))


def detail_team_member(request):
    team_id = request.GET.get('tid')
    team_name = request.GET.get('teamName')

    team_members = ProjectTeamMember.objects.filter(project_team=int(team_id))
    team = ProjectTeam.objects.get(id=team_id)

    context = {
        'team_member': team_members,
        'team': team
    }

    return render(request, 'project_management/details_team_member.html', context)


def admin_detail_team_member(request):
    team_id = request.GET.get('tid')
    team_name = request.GET.get('teamName')
    
    team_members = ProjectTeamMember.objects.filter(project_team=int(team_id))
    team = ProjectTeam.objects.get(id=team_id)

    context = {
        'team_member': team_members,
        'team': team
    }

    return render(request, 'project_management/admin_details_team_member.html', context)


def validateProjectTeamAssigned(request):
    """ Assign members not already in team """
    project_team_id = request.GET.get('project_team')
    projectteam = ProjectTeam.objects.get(id=project_team_id)

    members = ProjectTeamMember.objects.filter(project_team=projectteam)
    member_list = list(members)

    old = []
    new_users = set()

    if len(member_list) != 0:
        for member in member_list:
            old_user = User.objects.get(id=member.member_id)
            old.append(old_user)

        all_users = User.objects.filter()
        

        new_users = set(all_users).difference(set(old))
        data = {
            'users': serializers.serialize("json", new_users),
        }

        return JsonResponse(data)

    else:
        new_users = User.objects.all().filter()
        data = {
            'users': serializers.serialize("json", new_users),
        }

        return JsonResponse(data)


def remove_project_team_member(request):
    team_id = request.GET.get('teamid')
    team_name = request.GET.get('teamname')
    member_id = request.GET.get('memberid')

    teamid = ProjectTeam.objects.get(id=int(team_id))
    memberid = ProjectTeamMember.objects.get(id=int(member_id))
    memberid.project_team.remove(teamid)

    response_data = {
        'success': 'deleted successfully',
        'state': True,
    }

    return JsonResponse(response_data)


def project_forum(request):
    project_name = request.GET.get('projectname')
    project_id = request.GET.get('projectid')
    template = loader.get_template('project_management/project_team_forum.html')

    if ProjectForum.objects.filter(project_id=project_id).exists():
        obj3 = ProjectForum.objects.filter(project_id=project_id).values('forum_name', 'id').first()
        forum_name = obj3['forum_name']
        p_forum_id = obj3['id']
        state = True

        msg = ProjectForumMessages.objects.filter(projectforum_id=p_forum_id).annotate(count_replies=Count('projectforummessagereplies'))
        context = {
            'forum_name': forum_name,
            'msg': msg,
            'project_name': project_name,
            'project_id': project_id,
            'p_forum_id': p_forum_id,
            'state': state
        }
    else:
        state = False

        context = {
            'project_name': project_name,
            'project_id': project_id,
            'state': state
        }
    return HttpResponse(template.render(context, request))


def create_project_forum(request):
    project_id2 = request.GET['pid']
    forum_name2 = request.GET['fname']
    project_name2 = request.GET['pname']

    template = loader.get_template('project_management/project_team_forum.html')

    obj = ProjectForum(forum_name=forum_name2, project_id=project_id2)
    obj.save()
    p_forum_id = obj.id

    context = {
        'forum_name': forum_name2,
        'project_name': project_name2,
        'project_id': project_id2,
        'p_forum_id': p_forum_id,
        'state': True
    }

    return HttpResponse(template.render(context, request))


def manage_forum_replies(request):
    msg_id = request.GET['msg_id']
    msg_body = request.GET['msg_body']
    project_id = request.GET['project_id']
    project_name = request.GET['project_name']
    sender = request.GET['sender']
    forum_name = request.GET['forum_name']
    forum_id = request.GET['forum_id']

    template = loader.get_template('project_management/project_forum_replies.html')
    msg = ProjectForumMessageReplies.objects.filter(projectforummessage_id=msg_id)

    context = {
        'msg_id': msg_id,
        'msg_body': msg_body,
        'project_id': project_id,
        'project_name': project_name,
        'sender': sender,
        'msg_len': len(msg_body),
        'forum_name': forum_name,
        'msg': msg,
        'forum_id': forum_id,
    }

    return HttpResponse(template.render(context, request))


def delete_forum_message(request):
    project_name = request.GET.get('project_name')
    project_id = request.GET.get('project_id')
    forum_name = request.GET.get('forum_name')
    p_forum_id = request.GET.get('forum_id')
    count_replies = request.GET.get('count_replies')
    chat_id = request.GET.get('chat_id')
    state = True

    template = loader.get_template('project_management/project_team_forum.html')

    if int(count_replies) > 0:
        ProjectForumMessageReplies.objects.filter(projectforummessage_id=int(chat_id)).delete()
        ProjectForumMessages.objects.filter(id=int(chat_id)).delete()
    else:
        ProjectForumMessages.objects.filter(id=int(chat_id)).delete()

    msg = ProjectForumMessages.objects.filter(projectforum_id=p_forum_id).annotate(count_replies=Count('projectforummessagereplies'))
    context = {
        'forum_name': forum_name,
        'msg': msg,
        'project_name': project_name,
        'project_id': project_id,
        'p_forum_id': p_forum_id,
        'state': state
    }
    return HttpResponse(template.render(context, request))


def delete_forum_reply(request):
    msg_id = request.GET['chat_id']
    msg_body = request.GET['message']
    project_id = request.GET['project_id']
    project_name = request.GET['project_name']
    sender = request.GET['sender']
    forum_name = request.GET['forum_name']
    forum_id = request.GET['forum_id']
    reply_id = request.GET['reply_id']

    template = loader.get_template('project_management/project_forum_replies.html')
    ProjectForumMessageReplies.objects.filter(id=int(reply_id)).delete()
    msg = ProjectForumMessageReplies.objects.filter(projectforummessage_id=msg_id)

    context = {
        'msg_id': msg_id,
        'msg_body': msg_body,
        'project_id': project_id,
        'project_name': project_name,
        'sender': sender,
        'msg_len': len(msg_body),
        'forum_name': forum_name,
        'msg': msg,
        'forum_id': forum_id,
    }

    return HttpResponse(template.render(context, request))


def view_audit_logs(request):
    company_id = request.session['company_id']
    audit_logs = []
    
    startdate1 = str(date.today())
    enddate1 = str(date.today()) 

    startdate = datetime.datetime.strptime(startdate1, '%Y-%m-%d')
    enddate = datetime.datetime.strptime(enddate1, '%Y-%m-%d')

    min_dt = datetime.datetime.combine(startdate, datetime.time.min)
    max_dt = datetime.datetime.combine(enddate, datetime.time.max)

    obj_projects =  Project.history.filter(id=0, history_date__range=(min_dt, max_dt))
    obj_tasks = Task.history.filter(project_id=0, history_date__range=(min_dt, max_dt))
    obj_incidents = Incident.history.filter(project_id=0, history_date__range=(min_dt, max_dt))
    obj_milestones = Milestone.history.filter(project_id=0, history_date__range=(min_dt, max_dt))

    comp_projects = Project.objects.filter(company=int(company_id))
    for project_instance in comp_projects:
      
        obj_projects = obj_projects | Project.history.filter(id=project_instance.id, history_date__range=(min_dt, max_dt))
        obj_tasks = obj_tasks | Task.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))
        obj_incidents = obj_incidents | Incident.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))
        obj_milestones = obj_milestones | Milestone.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))
        
    for i in obj_tasks:
        tasks_hist = {'name': i.name, 'history_type': i.history_type, 'created_by': i.history_user, 'history_date': i.history_date, 'state': 'Task', 'project' : i.project}
        audit_logs.append(tasks_hist)

    for f in obj_projects:
        proj_hist = {'name': f.name, 'history_type': f.history_type, 'created_by': f.history_user, 'history_date': f.history_date, 'state': 'Project'}
        audit_logs.append(proj_hist)

    for j in obj_incidents:
        incid_hist = {'name': j.title, 'history_type': j.history_type, 'created_by': j.history_user, 'history_date': j.history_date, 'state': 'Incident', 'project' : j.project}
        audit_logs.append(incid_hist)

    for t in obj_milestones:
        milest_hist = {'name': t.name, 'history_type': t.history_type, 'created_by': t.history_user, 'history_date': t.history_date, 'state': 'Milestone', 'project' : t.project}
        audit_logs.append(milest_hist)
    
    sorted_audit_logs_list = sorted(audit_logs, key=operator.itemgetter('history_date'), reverse=True)
    template = loader.get_template('project_management/list_audit_logs.html')
    
    company_list = Company.objects.filter(~Q(id = int(company_id)))
    context = {
        'audit_logs': sorted_audit_logs_list,
        'company_list': company_list,
    }

    return HttpResponse(template.render(context, request))


def filter_audit_logs(request):
    company_id = request.GET.get('company_select_id')
    group_select_id = request.GET.get('group_select_id')
    action_select_id = request.GET.get('action_select_id')
    startdate1 = request.GET.get('start_audit_log')
    enddate1 = request.GET.get('end_audit_log')

    startdate = datetime.datetime.strptime(startdate1, '%d-%m-%Y')
    enddate = datetime.datetime.strptime(enddate1, '%d-%m-%Y')

    min_dt = datetime.datetime.combine(startdate, datetime.time.min)
    max_dt = datetime.datetime.combine(enddate, datetime.time.max)

    audit_logs = []
    obj_projects =  Project.history.filter(id=0, history_date__range=(min_dt, max_dt))
    obj_tasks = Task.history.filter(project_id=0, history_date__range=(min_dt, max_dt))
    obj_incidents = Incident.history.filter(project_id=0, history_date__range=(min_dt, max_dt))
    obj_milestones = Milestone.history.filter(project_id=0, history_date__range=(min_dt, max_dt))
    comp_projects = Project.objects.filter(company=int(company_id))

    if(group_select_id == 'all'):
        # all categories : milestones,projects,tasks,incidents
        if(action_select_id == 'all'):
            # all actions : update, delete, add
            for project_instance in comp_projects:
                obj_projects = obj_projects | Project.history.filter(id=project_instance.id, history_date__range=(min_dt, max_dt))
                obj_tasks = obj_tasks | Task.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))
                obj_incidents = obj_incidents | Incident.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))
                obj_milestones = obj_milestones | Milestone.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))
        else:
            # one actions : update/delete/add
            for project_instance in comp_projects:
                obj_projects = obj_projects | Project.history.filter(id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))
                obj_tasks = obj_tasks | Task.history.filter(project_id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))
                obj_incidents = obj_incidents | Incident.history.filter(project_id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))
                obj_milestones = obj_milestones | Milestone.history.filter(project_id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))

    else:
        # all categories : milestones,projects,tasks,incidents
        if(action_select_id == 'all'):
            # all actions : update, delete, add
            if(group_select_id == 'projects'):
                for project_instance in comp_projects:
                    obj_projects = obj_projects | Project.history.filter(id=project_instance.id, history_date__range=(min_dt, max_dt))
            
            elif(group_select_id == 'milestones'):
                for project_instance in comp_projects:
                    obj_milestones = obj_milestones | Milestone.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))

            elif(group_select_id == 'tasks'):
                for project_instance in comp_projects:
                    obj_tasks = obj_tasks | Task.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))
            else:
                for project_instance in comp_projects:
                    obj_incidents = obj_incidents | Incident.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))

        else:
            # one actions : update/delete/add
            if(group_select_id == 'projects'):
                for project_instance in comp_projects:
                    obj_projects = obj_projects | Project.history.filter(id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))
            
            elif(group_select_id == 'milestones'):
                for project_instance in comp_projects:
                    obj_milestones = obj_milestones | Milestone.history.filter(project_id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))

            elif(group_select_id == 'tasks'):
                for project_instance in comp_projects:
                    obj_tasks = obj_tasks | Task.history.filter(project_id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))
            else:
                for project_instance in comp_projects:
                    obj_incidents = obj_incidents | Incident.history.filter(project_id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))

    for i in obj_tasks:
        tasks_hist = {'name': i.name, 'history_type': i.history_type, 'created_by': i.history_user, 'history_date': i.history_date, 'state': 'Task', 'project' : i.project}
        audit_logs.append(tasks_hist)

    for f in obj_projects:
        proj_hist = {'name': f.name, 'history_type': f.history_type, 'created_by': f.history_user, 'history_date': f.history_date, 'state': 'Project'}
        audit_logs.append(proj_hist)

    for j in obj_incidents:
        incid_hist = {'name': j.name, 'history_type': j.history_type, 'created_by': j.history_user, 'history_date': j.history_date, 'state': 'Incident', 'project' : j.project}
        audit_logs.append(incid_hist)

    for t in obj_milestones:
        milest_hist = {'name': t.name, 'history_type': t.history_type, 'created_by': t.history_user, 'history_date': t.history_date, 'state': 'Milestone', 'project' : t.project}
        audit_logs.append(milest_hist)
    
    sorted_audit_logs_list = sorted(audit_logs, key=operator.itemgetter('history_date'), reverse=True)
        

    template = loader.get_template('project_management/list_audit_logs_filter.html')
    context = {
        'audit_logs': sorted_audit_logs_list,
    }

    return HttpResponse(template.render(context, request))


def all_companies_filter_auditlogs(request):
    group_select_id = request.GET.get('group_select_id')
    action_select_id = request.GET.get('action_select_id')

    startdate1 = request.GET.get('start_audit_log')
    enddate1 = request.GET.get('end_audit_log')

    startdate = datetime.datetime.strptime(startdate1, '%d-%m-%Y')
    enddate = datetime.datetime.strptime(enddate1, '%d-%m-%Y')

    min_dt = datetime.datetime.combine(startdate, datetime.time.min)
    max_dt = datetime.datetime.combine(enddate, datetime.time.max)

    audit_logs = []
    obj_projects =  Project.history.filter(id=0, history_date__range=(min_dt, max_dt))
    obj_tasks = Task.history.filter(project_id=0, history_date__range=(min_dt, max_dt))
    obj_incidents = Incident.history.filter(project_id=0, history_date__range=(min_dt, max_dt))
    obj_milestones = Milestone.history.filter(project_id=0, history_date__range=(min_dt, max_dt))
    comp_projects = Project.objects.all()

    if(group_select_id == 'all'):
        # all categories : milestones,projects,tasks,incidents
        if(action_select_id == 'all'):
            # all actions : update, delete, add
            for project_instance in comp_projects:
                obj_projects = obj_projects | Project.history.filter(id=project_instance.id, history_date__range=(min_dt, max_dt))
                obj_tasks = obj_tasks | Task.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))
                obj_incidents = obj_incidents | Incident.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))
                obj_milestones = obj_milestones | Milestone.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))
        else:
            # one actions : update/delete/add
            for project_instance in comp_projects:
                obj_projects = obj_projects | Project.history.filter(id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))
                obj_tasks = obj_tasks | Task.history.filter(project_id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))
                obj_incidents = obj_incidents | Incident.history.filter(project_id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))
                obj_milestones = obj_milestones | Milestone.history.filter(project_id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))

    else:
        # all categories : milestones,projects,tasks,incidents
        if(action_select_id == 'all'):
            # all actions : update, delete, add
            if(group_select_id == 'projects'):
                for project_instance in comp_projects:
                    obj_projects = obj_projects | Project.history.filter(id=project_instance.id, history_date__range=(min_dt, max_dt))
            
            elif(group_select_id == 'milestones'):
                for project_instance in comp_projects:
                    obj_milestones = obj_milestones | Milestone.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))

            elif(group_select_id == 'tasks'):
                for project_instance in comp_projects:
                    obj_tasks = obj_tasks | Task.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))
            else:
                for project_instance in comp_projects:
                    obj_incidents = obj_incidents | Incident.history.filter(project_id=project_instance.id, history_date__range=(min_dt, max_dt))

        else:
            # one actions : update/delete/add
            if(group_select_id == 'projects'):
                for project_instance in comp_projects:
                    obj_projects = obj_projects | Project.history.filter(id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))
            
            elif(group_select_id == 'milestones'):
                for project_instance in comp_projects:
                    obj_milestones = obj_milestones | Milestone.history.filter(project_id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))

            elif(group_select_id == 'tasks'):
                for project_instance in comp_projects:
                    obj_tasks = obj_tasks | Task.history.filter(project_id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))
            else:
                for project_instance in comp_projects:
                    obj_incidents = obj_incidents | Incident.history.filter(project_id=project_instance.id, history_type=action_select_id, history_date__range=(min_dt, max_dt))

    for i in obj_tasks:
        comp1 = Company.objects.filter(project=int(i.project_id)).first()
        tasks_hist = {'name': i.name, 'history_type': i.history_type, 'created_by': i.history_user, 'history_date': i.history_date, 'state': 'Task', 'project': i.project, 'company': comp1}
        audit_logs.append(tasks_hist)

    for f in obj_projects:
        comp2 = Company.objects.filter(project=int(f.id)).first()    
        proj_hist = {'name': f.name, 'history_type': f.history_type, 'created_by': f.history_user, 'history_date': f.history_date, 'state': 'Project', 'company': comp2}
        audit_logs.append(proj_hist)

    for j in obj_incidents:
        comp3 = Company.objects.filter(project=int(j.project_id)).first()  
        incid_hist = {'name': j.name, 'history_type': j.history_type, 'created_by': j.history_user, 'history_date': j.history_date, 'state': 'Incident', 'project': j.project, 'company': comp3}
        audit_logs.append(incid_hist)

    for t in obj_milestones:
        comp4 = Company.objects.filter(project=int(t.project_id)).first()  
        milest_hist = {'name': t.name, 'history_type': t.history_type, 'created_by': t.history_user, 'history_date': t.history_date, 'state': 'Milestone', 'project' : t.project, 'company': comp4}
        audit_logs.append(milest_hist)
    
    sorted_audit_logs_list = sorted(audit_logs, key=operator.itemgetter('history_date'), reverse=True)

    template = loader.get_template('project_management/list_all_comp_auditlogs_filter.html')
    context = {
        'audit_logs': sorted_audit_logs_list,
    }

    return HttpResponse(template.render(context, request))


@login_required
def daily_timesheets_pane(request):
    uid = request.user.id
    company_id = request.session['company_id']
    department_id = request.session['department_id']

    rejected_count = Timesheet.objects.filter(Q(status='REJECTED'), company_id=company_id, project_team_member_id=uid).count()

    timesheets_exist = Timesheet.objects.filter(status='INITIAL', project_team_member_id=uid, company_id=company_id).exists()

    if timesheets_exist == True:
        timesheet_list1 = Timesheet.objects.filter(status='INITIAL', project_team_member_id=uid, company_id=company_id)
        new_list = []

        for i in timesheet_list1:
	        new_list.append(i.log_day)            

        new_list2 = []
        new_list = set(new_list)
        new_list = sorted(new_list, reverse = True)
        for tm in new_list: 
            task_request_list_final = []           
            new_dict = {}
            new_dict['tim'] = tm
            daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__log_day=tm, timesheet__status='INITIAL', timesheet__project_team_member_id=uid, timesheet__company_id=company_id)
            daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__log_day=tm, timesheet__status='INITIAL', timesheet__project_team_member_id=uid, timesheet__company_id=company_id)
            
            for tsk in daily_tm_tasks:
                dict_tasks = {}
                dict_tasks['tm_id'] = tsk.timesheet.id
                dict_tasks['name'] = tsk.task
                dict_tasks['task_id'] = tsk.task_id
                dict_tasks['duration'] = tsk.timesheet.duration
                dict_tasks['log_day'] = tsk.timesheet.log_day
                dict_tasks['start_time'] = tsk.timesheet.start_time
                dict_tasks['end_time'] = tsk.timesheet.end_time
                dict_tasks['notes'] = tsk.timesheet.notes
                dict_tasks['created_time'] = tsk.timesheet.created_time
                dict_tasks['timesheet_type'] = 'task_type'
                dict_tasks['sla_name'] = ''
                dict_tasks['sla_id'] = ''
                task_request_list_final.append(dict_tasks)

            for req in daily_tm_requests:
                dict_requests = {}
                dict_requests['tm_id'] = req.timesheet.id
                dict_requests['name'] = req.customer_request
                dict_requests['task_id'] = req.customer_request_id
                dict_requests['duration'] = req.timesheet.duration
                dict_requests['log_day'] = req.timesheet.log_day
                dict_requests['start_time'] = req.timesheet.start_time
                dict_requests['end_time'] = req.timesheet.end_time
                dict_requests['notes'] = req.timesheet.notes
                dict_requests['timesheet_type'] = 'request_type'
                dict_requests['created_time'] = req.timesheet.created_time
                dict_requests['sla_name'] = req.customer_request.sla.name
                dict_requests['sla_id'] = req.customer_request.sla.id
                task_request_list_final.append(dict_requests)

            new_dict['dictt'] = task_request_list_final
            
            sum_duration = 0 
            for ii in daily_tm_tasks:
	            sum_duration = sum_duration + ii.timesheet.durationsec()

            for req in daily_tm_requests:
                sum_duration = sum_duration + req.timesheet.durationsec()

            new_dict['duration'] = compute_duration(sum_duration)
            new_list2.append(new_dict)
    else: 
        new_list2 = ''

    dept_users = User.objects.filter(Q(department_id=int(department_id)), ~Q(id = int(uid)))
    template = loader.get_template('project_management/daily_timesheets_pane.html')
    context = {
        'timesheet_list': new_list2,
        'rejected_count': rejected_count,
        'dept_users': dept_users,
        'user_id' : uid,
        'user_name' : User.objects.get(id=int(uid))
    }

    return HttpResponse(template.render(context, request))


def add_new_timesheet(request):
    company_id = request.session['company_id']
    id_user_dept = int(request.GET.get('id_user_dept'))

    # project_list = Project.objects.filter(company=int(company_id))
    members = ProjectTeamMember.objects.filter(member=id_user_dept)
    team_list = []
    for value in members:  
        team_members = ProjectTeamMember.project_team.through.objects.filter(projectteammember=value.id)

        for obj in team_members:
            team_name = obj.projectteam
            team_list.append(team_name)
    
    project_list = []
    for team in team_list:
        project_id = team.project_id
        
        project = Project.objects.get(id=project_id)
        project_dict = {}
        project_dict['id'] = project.id
        project_dict['name'] = project.name

        project_list.append(project_dict)
    
    template = loader.get_template('project_management/add_time_sheet.html')
    context = {
        'project_list': project_list,
        'user_id' : id_user_dept,
        'user_name' : User.objects.get(id=int(id_user_dept)),

        # PEDDING PLEASE ADD COMPANY ID (PARENT) FILTER need to fix save/attch parentid to customer then fix this
        # 'client_list' : Company.objects.filter(category__category_value='CLIENT', parent=company_id)
        'client_list' : Company.objects.filter(category__category_value='CLIENT')
    }

    return HttpResponse(template.render(context, request))

    
def fetch_milestones_by_project(request):
    project_id = request.GET.get('project_id')
    
    list_project_milestones = Milestone.objects.filter(project_id=int(project_id))
    data = {
        'mil': serializers.serialize("json", list_project_milestones)
    }
    return JsonResponse(data)


def fetch_tasks_by_milestone(request):
    id_milestone = request.GET.get('id_milestone')
    
    list_milestone_tasks = Task.objects.filter(milestone_id=int(id_milestone))
    data = {
        'task': serializers.serialize("json", list_milestone_tasks)
    }
    return JsonResponse(data)


def save_new_timesheet(request):
    structureRadioValue = request.GET.get('structureRadioValue')
    uid = request.user.id
    company_id = request.session['company_id']
    id_log_day = request.GET.get('id_log_day')
    dept_uid = int(request.GET.get('uid'))
    log_day = datetime.datetime.strptime(id_log_day, '%d-%m-%Y')

    if structureRadioValue == 'project':
        id_task = request.GET.get('id_task')
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')
        id_timesheet_notes = request.GET.get('notes')

        
        start_time1 = datetime.datetime.strptime(start_time, '%I:%M %p')
        end_time1 =   datetime.datetime.strptime(end_time, '%I:%M %p')
        
        obj = Timesheet(log_day=log_day, start_time=start_time1, end_time=end_time1, added_by_id=uid, project_team_member_id=dept_uid, company_id=int(company_id), last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=id_timesheet_notes, timesheet_category="TIMESHEET")
        obj.save()
        
        new_timesheet_id = obj.id
        if new_timesheet_id != "":
            TaskTimesheetExtend.objects.create(timesheet_id=new_timesheet_id, task_id=int(id_task))

    else:
        id_assigned_requests = request.GET.get('id_assigned_requests')

        start_time02 = request.GET.get('start_time2')
        end_time02 = request.GET.get('end_time2')
        id_timesheet_notes02 = request.GET.get('notes2')
        
        start_time003 = datetime.datetime.strptime(start_time02, '%I:%M %p')
        end_time003 =   datetime.datetime.strptime(end_time02, '%I:%M %p')

        obj2 = Timesheet(log_day=log_day, start_time=start_time003, end_time=end_time003, added_by_id=uid, project_team_member_id=dept_uid, company_id=int(company_id), last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=id_timesheet_notes02, timesheet_category="REQUEST")
        obj2.save()

        new_timesheet_id2 = obj2.id
        if new_timesheet_id2 != "":
            RequestTimesheetExtend.objects.create(timesheet_id=new_timesheet_id2, customer_request_id=int(id_assigned_requests))

    timesheets_exist = Timesheet.objects.filter(status='INITIAL', project_team_member_id=dept_uid, company_id=company_id).exists()
    uid = request.user.id

    if timesheets_exist == True:
        timesheet_list1 = Timesheet.objects.filter(status='INITIAL', project_team_member_id=dept_uid, company_id=company_id)
        new_list = []

        for i in timesheet_list1:
	        new_list.append(i.log_day)            

        new_list2 = []
        new_list = set(new_list)
        new_list = sorted(new_list, reverse = True)
        for tm in new_list: 
            task_request_list_final = []           
            new_dict = {}
            new_dict['tim'] = tm
            daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__log_day=tm, timesheet__status='INITIAL', timesheet__project_team_member_id=dept_uid, timesheet__company_id=company_id)
            daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__log_day=tm, timesheet__status='INITIAL', timesheet__project_team_member_id=dept_uid, timesheet__company_id=company_id)
            
            for tsk in daily_tm_tasks:
                dict_tasks = {}
                dict_tasks['tm_id'] = tsk.timesheet.id
                dict_tasks['name'] = tsk.task
                dict_tasks['task_id'] = tsk.task_id
                dict_tasks['duration'] = tsk.timesheet.duration
                dict_tasks['log_day'] = tsk.timesheet.log_day
                dict_tasks['start_time'] = tsk.timesheet.start_time
                dict_tasks['end_time'] = tsk.timesheet.end_time
                dict_tasks['notes'] = tsk.timesheet.notes
                dict_tasks['created_time'] = tsk.timesheet.created_time
                dict_tasks['timesheet_type'] = 'task_type'
                dict_tasks['sla_name'] = ''
                dict_tasks['sla_id'] = ''
                task_request_list_final.append(dict_tasks)

            for req in daily_tm_requests:
                dict_requests = {}
                dict_requests['tm_id'] = req.timesheet.id
                dict_requests['name'] = req.customer_request
                dict_requests['task_id'] = req.customer_request_id
                dict_requests['duration'] = req.timesheet.duration
                dict_requests['log_day'] = req.timesheet.log_day
                dict_requests['start_time'] = req.timesheet.start_time
                dict_requests['end_time'] = req.timesheet.end_time
                dict_requests['notes'] = req.timesheet.notes
                dict_requests['created_time'] = req.timesheet.created_time
                dict_requests['timesheet_type'] = 'request_type'
                dict_requests['sla_name'] = req.customer_request.sla.name
                dict_requests['sla_id'] = req.customer_request.sla.id
                task_request_list_final.append(dict_requests)

            new_dict['dictt'] = task_request_list_final
            
            sum_duration = 0 
            for ii in daily_tm_tasks:
	            sum_duration = sum_duration + ii.timesheet.durationsec()

            for req in daily_tm_requests:
                sum_duration = sum_duration + req.timesheet.durationsec()

            new_dict['duration'] = compute_duration(sum_duration)
            new_list2.append(new_dict)
    else: 
        new_list2 = False

    template = loader.get_template('project_management/list_timesheet.html')
    context = {
        'timesheet_list': new_list2,
    }

    return HttpResponse(template.render(context, request))


def update_timesheet(request):
    state = request.GET.get('state')
    company_id = request.session['company_id']
    log_day = request.GET.get('log_day')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    task = request.GET.get('task')
    timesheet_id = int(request.GET.get('timesheet_id'))
    task_id = int(request.GET.get('task_id'))
    notes = request.GET.get('notes')
    id_user_dept = request.GET.get('id_user_dept')

    if state == "task":
        obj_task = Task.objects.get(id=task_id)
        project_name = obj_task.project
        project_id = obj_task.project_id
        milestone_id = obj_task.milestone_id
        milestone_name = obj_task.milestone    

        project_list = Project.objects.filter(~Q(id = int(project_id)))
        list_project_milestones = Milestone.objects.filter(Q(project_id=int(project_id)), ~Q(id = int(milestone_id)))
        list_milestone_tasks = Task.objects.filter(Q(milestone_id=int(milestone_id)), ~Q(id = task_id))

        template = loader.get_template('project_management/update_timesheet.html')
        context = {
            'log_day': log_day,
            'start_time': start_time,
            'end_time': end_time,
            'task': task,
            'timesheet_id': timesheet_id,
            'project_list': project_list,
            'list_milestone_tasks': list_milestone_tasks,
            'list_project_milestones': list_project_milestones,
            'milestone_id': milestone_id,
            'milestone_name': milestone_name,
            'project_name': project_name,
            'project_id': project_id,
            'task_id': task_id,
            'notes': notes,
            'user_id' : id_user_dept,
            'user_name' : User.objects.get(id=int(id_user_dept))
        }
    else:
        sla_name = request.GET.get('sla_name')
        sla_id = int(request.GET.get('sla_id'))

        customer = ServiceLevelAgreement.objects.get(id=sla_id)
        curr_customer_id = customer.customer_id
        curr_customer_name = customer.customer.name

        client_list = Company.objects.filter(category__category_value='CLIENT', parent=company_id)
        sla_list = ServiceLevelAgreement.objects.filter(customer_id=curr_customer_id)

        list_sla_requests = CustomerRequest.objects.filter(sla_id=int(sla_id), assigned_member__assigned_member=id_user_dept)
        
        template = loader.get_template('project_management/update_timesheet_request.html')
        context = {
            'log_day': log_day,
            'start_time': start_time,
            'end_time': end_time,
            'req': task,
            'timesheet_id': timesheet_id,
            'req_id': task_id,
            'notes': notes,
            'user_id' : id_user_dept,
            'user_name' : User.objects.get(id=int(id_user_dept)),
            'client_list': client_list,
            'sla_id': sla_id,
            'sla_name': sla_name,
            'curr_customer_id': curr_customer_id,
            'curr_customer_name': curr_customer_name,
            'sla_list': sla_list,
            'request_list': list_sla_requests
        }
    

    return HttpResponse(template.render(context, request))


def update_timesheet_paginator(request):
    state = request.GET.get('state')
    company_id = request.session['company_id']
    log_day = request.GET.get('log_day')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    task = request.GET.get('task')
    timesheet_id = int(request.GET.get('timesheet_id'))
    task_id = int(request.GET.get('task_id'))
    notes = request.GET.get('notes')
    id_user_dept = request.GET.get('id_user_dept')

    if state == "project":
        obj_task = Task.objects.get(id=task_id)
        project_name = obj_task.project
        project_id = obj_task.project_id
        milestone_id = obj_task.milestone_id
        milestone_name = obj_task.milestone    

        project_list = Project.objects.filter(~Q(id = int(project_id)))
        list_project_milestones = Milestone.objects.filter(Q(project_id=int(project_id)), ~Q(id = int(milestone_id)))
        list_milestone_tasks = Task.objects.filter(Q(milestone_id=int(milestone_id)), ~Q(id = task_id))

        template = loader.get_template('project_management/update_timesheet_paginator_view.html')
        context = {
            'log_day': log_day,
            'start_time': start_time,
            'end_time': end_time,
            'task': task,
            'timesheet_id': timesheet_id,
            'project_list': project_list,
            'list_milestone_tasks': list_milestone_tasks,
            'list_project_milestones': list_project_milestones,
            'milestone_id': milestone_id,
            'milestone_name': milestone_name,
            'project_name': project_name,
            'project_id': project_id,
            'task_id': task_id,
            'notes': notes,
            'user_id' : id_user_dept,
            'user_name' : User.objects.get(id=int(id_user_dept))
        }
    else:
        sla_name = request.GET.get('sla_name')
        sla_id = int(request.GET.get('sla_id'))

        customer = ServiceLevelAgreement.objects.get(id=sla_id)
        curr_customer_id = customer.customer_id
        curr_customer_name = customer.customer.name

        client_list = Company.objects.filter(Q(category__category_value='CLIENT'), ~Q(id = curr_customer_id), Q(parent=company_id))
        sla_list = ServiceLevelAgreement.objects.filter(Q(customer_id=curr_customer_id), ~Q(id = sla_id))

        list_sla_requests = CustomerRequest.objects.filter(Q(sla_id=int(sla_id)), Q(assigned_member__assigned_member=id_user_dept), ~Q(id = task_id))
        
        template = loader.get_template('project_management/update_timesheet_requests_paginator_view.html')
        context = {
            'log_day': log_day,
            'start_time': start_time,
            'end_time': end_time,
            'req': task,
            'timesheet_id': timesheet_id,
            'req_id': task_id,
            'notes': notes,
            'user_id' : id_user_dept,
            'user_name' : User.objects.get(id=int(id_user_dept)),
            'client_list': client_list,
            'sla_id': sla_id,
            'sla_name': sla_name,
            'curr_customer_id': curr_customer_id,
            'curr_customer_name': curr_customer_name,
            'sla_list': sla_list,
            'request_list': list_sla_requests
        }

    return HttpResponse(template.render(context, request))


def resubmit_timesheet(request):
    state = request.GET.get('state')
    company_id = request.session['company_id']
    log_day = request.GET.get('log_day')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    task = request.GET.get('task')
    timesheet_id = int(request.GET.get('timesheet_id'))
    task_id = int(request.GET.get('task_id'))
    notes = request.GET.get('notes')
    id_user_dept = int(request.GET.get('id_user_dept'))

    if state == "project":
        obj_task = Task.objects.get(id=int(task_id))
        project_name = obj_task.project
        project_id = obj_task.project_id
        milestone_id = obj_task.milestone_id
        milestone_name = obj_task.milestone    

        project_list = Project.objects.filter(~Q(id = int(project_id)))
        list_project_milestones = Milestone.objects.filter(Q(project_id=int(project_id)), ~Q(id = int(milestone_id)))
        list_milestone_tasks = Task.objects.filter(Q(milestone_id=int(milestone_id)), ~Q(id = task_id))

        template = loader.get_template('project_management/resubmit_timesheet.html')
        context = {
            'log_day': log_day,
            'start_time': start_time,
            'end_time': end_time,
            'task': task,
            'timesheet_id': timesheet_id,
            'project_list': project_list,
            'list_milestone_tasks': list_milestone_tasks,
            'list_project_milestones': list_project_milestones,
            'milestone_id': milestone_id,
            'milestone_name': milestone_name,
            'project_name': project_name,
            'project_id': project_id,
            'task_id': task_id,
            'notes': notes,
            'user_id' : id_user_dept,
            'user_name' : User.objects.get(id=id_user_dept)
        }

    else: 
        sla_name = request.GET.get('sla_name')
        sla_id = int(request.GET.get('sla_id'))

        customer = ServiceLevelAgreement.objects.get(id=sla_id)
        curr_customer_id = customer.customer_id
        curr_customer_name = customer.customer.name

        client_list = Company.objects.filter(category__category_value='CLIENT', parent=company_id)
        sla_list = ServiceLevelAgreement.objects.filter(customer_id=curr_customer_id)

        list_sla_requests = CustomerRequest.objects.filter(sla_id=int(sla_id), assigned_member__assigned_member=id_user_dept)
        
        template = loader.get_template('project_management/resubmit_request_timesheet.html')
        context = {
            'log_day': log_day,
            'start_time': start_time,
            'end_time': end_time,
            'req': task,
            'timesheet_id': timesheet_id,
            'req_id': task_id,
            'notes': notes,
            'user_id' : id_user_dept,
            'user_name' : User.objects.get(id=int(id_user_dept)),
            'client_list': client_list,
            'sla_id': sla_id,
            'sla_name': sla_name,
            'curr_customer_id': curr_customer_id,
            'curr_customer_name': curr_customer_name,
            'sla_list': sla_list,
            'request_list': list_sla_requests
        }

    return HttpResponse(template.render(context, request))


def paginator_resubmit_timesheet(request):
    state = request.GET.get('state')
    company_id = request.session['company_id']
    log_day = request.GET.get('log_day')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    task = request.GET.get('task')
    timesheet_id = int(request.GET.get('timesheet_id'))
    task_id = int(request.GET.get('task_id'))
    notes = request.GET.get('notes')
    id_user_dept = int(request.GET.get('id_user_dept'))

    if state == "project":
        obj_task = Task.objects.get(id=int(task_id))
        project_name = obj_task.project
        project_id = obj_task.project_id
        milestone_id = obj_task.milestone_id
        milestone_name = obj_task.milestone    

        project_list = Project.objects.filter(~Q(id = int(project_id)))
        list_project_milestones = Milestone.objects.filter(Q(project_id=int(project_id)), ~Q(id = int(milestone_id)))
        list_milestone_tasks = Task.objects.filter(Q(milestone_id=int(milestone_id)), ~Q(id = task_id))

        template = loader.get_template('project_management/paginator_resubmit_timesheet.html')
        context = {
            'log_day': log_day,
            'start_time': start_time,
            'end_time': end_time,
            'task': task,
            'timesheet_id': timesheet_id,
            'project_list': project_list,
            'list_milestone_tasks': list_milestone_tasks,
            'list_project_milestones': list_project_milestones,
            'milestone_id': milestone_id,
            'milestone_name': milestone_name,
            'project_name': project_name,
            'project_id': project_id,
            'task_id': task_id,
            'notes': notes,
            'user_id' : id_user_dept,
            'user_name' : User.objects.get(id=id_user_dept)
        }

    else: 
        sla_name = request.GET.get('sla_name')
        sla_id = int(request.GET.get('sla_id'))

        customer = ServiceLevelAgreement.objects.get(id=sla_id)
        curr_customer_id = customer.customer_id
        curr_customer_name = customer.customer.name

        client_list = Company.objects.filter(category__category_value='CLIENT', parent=company_id)
        sla_list = ServiceLevelAgreement.objects.filter(customer_id=curr_customer_id)

        list_sla_requests = CustomerRequest.objects.filter(sla_id=int(sla_id), assigned_member__assigned_member=id_user_dept)
        
        template = loader.get_template('project_management/paginator_resubmit_request_timesheet.html')
        context = {
            'log_day': log_day,
            'start_time': start_time,
            'end_time': end_time,
            'req': task,
            'timesheet_id': timesheet_id,
            'req_id': task_id,
            'notes': notes,
            'user_id' : id_user_dept,
            'user_name' : User.objects.get(id=int(id_user_dept)),
            'client_list': client_list,
            'sla_id': sla_id,
            'sla_name': sla_name,
            'curr_customer_id': curr_customer_id,
            'curr_customer_name': curr_customer_name,
            'sla_list': sla_list,
            'request_list': list_sla_requests
        }

    return HttpResponse(template.render(context, request))


def save_update_timesheet(request):
    structural_vale = request.GET.get('structural_vale')
    company_id = request.session['company_id']
    log_day = request.GET.get('id_log_day')
    dept_uid = int(request.GET.get('uid'))
    uid = request.user.id
    log_day = datetime.datetime.strptime(log_day, '%d-%m-%Y')

    if structural_vale == 'project':
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')
        task = int(request.GET.get('id_task'))
        timesheet_id = int(request.GET.get('timesheet_id'))
        notes = request.GET.get('notes')
        
        start_time1 = datetime.datetime.strptime(start_time, '%I:%M %p')
        end_time1 =   datetime.datetime.strptime(end_time, '%I:%M %p')
        
        Timesheet.objects.filter(pk=int(timesheet_id)).update(log_day=log_day, start_time=start_time1, end_time=end_time1, last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=notes)
        TaskTimesheetExtend.objects.filter(pk=timesheet_id).update(task_id=task)
    else:
        id_assigned_requests = request.GET.get('id_assigned_requests')

        start_time02 = request.GET.get('start_time2')
        end_time02 = request.GET.get('end_time2')
        id_timesheet_notes02 = request.GET.get('notes2')
        timesheet_id02 = int(request.GET.get('timesheet_id2'))
        notes02 = request.GET.get('notes2')
        
        start_time003 = datetime.datetime.strptime(start_time02, '%I:%M %p')
        end_time003 =   datetime.datetime.strptime(end_time02, '%I:%M %p')
        
        Timesheet.objects.filter(pk=int(timesheet_id02)).update(log_day=log_day, start_time=start_time003, end_time=end_time003, last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=notes02)
        RequestTimesheetExtend.objects.filter(pk=timesheet_id02).update(customer_request_id=id_assigned_requests) 
    
    timesheets_exist = Timesheet.objects.filter(status='INITIAL', project_team_member_id=dept_uid, company_id=company_id).exists()
    if timesheets_exist == True:
        timesheet_list1 = Timesheet.objects.filter(status='INITIAL', project_team_member_id=dept_uid, company_id=company_id)
        new_list = []

        for i in timesheet_list1:
	        new_list.append(i.log_day)            

        new_list2 = []
        new_list = set(new_list)
        new_list = sorted(new_list, reverse = True)
        for tm in new_list: 
            task_request_list_final = []           
            new_dict = {}
            new_dict['tim'] = tm
            daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__log_day=tm, timesheet__status='INITIAL', timesheet__project_team_member_id=dept_uid, timesheet__company_id=company_id)
            daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__log_day=tm, timesheet__status='INITIAL', timesheet__project_team_member_id=dept_uid, timesheet__company_id=company_id)
            
            for tsk in daily_tm_tasks:
                dict_tasks = {}
                dict_tasks['tm_id'] = tsk.timesheet.id
                dict_tasks['name'] = tsk.task
                dict_tasks['task_id'] = tsk.task_id
                dict_tasks['duration'] = tsk.timesheet.duration
                dict_tasks['log_day'] = tsk.timesheet.log_day
                dict_tasks['start_time'] = tsk.timesheet.start_time
                dict_tasks['end_time'] = tsk.timesheet.end_time
                dict_tasks['notes'] = tsk.timesheet.notes
                dict_tasks['created_time'] = tsk.timesheet.created_time
                dict_tasks['timesheet_type'] = 'task_type'
                dict_tasks['sla_name'] = ''
                dict_tasks['sla_id'] = ''
                task_request_list_final.append(dict_tasks)

            for req in daily_tm_requests:
                dict_requests = {}
                dict_requests['tm_id'] = req.timesheet.id
                dict_requests['name'] = req.customer_request
                dict_requests['task_id'] = req.customer_request_id
                dict_requests['duration'] = req.timesheet.duration
                dict_requests['log_day'] = req.timesheet.log_day
                dict_requests['start_time'] = req.timesheet.start_time
                dict_requests['end_time'] = req.timesheet.end_time
                dict_requests['notes'] = req.timesheet.notes
                dict_requests['created_time'] = req.timesheet.created_time
                dict_requests['timesheet_type'] = 'request_type'
                dict_requests['sla_name'] = req.customer_request.sla.name
                dict_requests['sla_id'] = req.customer_request.sla.id
                task_request_list_final.append(dict_requests)

            new_dict['dictt'] = task_request_list_final
            
            sum_duration = 0 
            for ii in daily_tm_tasks:
	            sum_duration = sum_duration + ii.timesheet.durationsec()
            
            for req in daily_tm_requests:
                sum_duration = sum_duration + req.timesheet.durationsec()

            new_dict['duration'] = compute_duration(sum_duration)
            new_list2.append(new_dict)
    
    template = loader.get_template('project_management/list_timesheet.html')
    context = {
        'timesheet_list': new_list2,
    }

    return HttpResponse(template.render(context, request))


def delete_timesheet(request):
    company_id = request.session['company_id']
    dept_uid = int(request.GET.get('id_user_dept'))

    structural_vale = request.GET.get('state')
    if structural_vale == 'project':
        timesheet_id = request.GET.get('timesheet_id')
        task_id = request.GET.get('task_id')

        TaskTimesheetExtend.objects.filter(pk=timesheet_id).delete()
        Timesheet.objects.filter(id=int(timesheet_id)).delete()
    else:
        timesheet_id2 = request.GET.get('timesheet_id2')
        req_id = request.GET.get('request_id')
        RequestTimesheetExtend.objects.filter(pk=timesheet_id2).delete()
        Timesheet.objects.filter(id=int(timesheet_id2)).delete()

    timesheets_exist = Timesheet.objects.filter(status='INITIAL', project_team_member_id=dept_uid, company_id=company_id).exists()

    if timesheets_exist == True:
        timesheet_list1 = Timesheet.objects.filter(status='INITIAL', project_team_member_id=dept_uid, company_id=company_id)
        new_list = []

        for i in timesheet_list1:
	        new_list.append(i.log_day)            

        new_list2 = []
        new_list = set(new_list)
        new_list = sorted(new_list, reverse = True)
        for tm in new_list: 
            task_request_list_final = []           
            new_dict = {}
            new_dict['tim'] = tm
            daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__log_day=tm, timesheet__status='INITIAL', timesheet__project_team_member_id=dept_uid, timesheet__company_id=company_id)
            daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__log_day=tm, timesheet__status='INITIAL', timesheet__project_team_member_id=dept_uid, timesheet__company_id=company_id)
            
            for tsk in daily_tm_tasks:
                dict_tasks = {}
                dict_tasks['tm_id'] = tsk.timesheet.id
                dict_tasks['name'] = tsk.task
                dict_tasks['task_id'] = tsk.task_id
                dict_tasks['duration'] = tsk.timesheet.duration
                dict_tasks['log_day'] = tsk.timesheet.log_day
                dict_tasks['start_time'] = tsk.timesheet.start_time
                dict_tasks['end_time'] = tsk.timesheet.end_time
                dict_tasks['notes'] = tsk.timesheet.notes
                dict_tasks['created_time'] = tsk.timesheet.created_time
                dict_tasks['timesheet_type'] = 'task_type'
                dict_tasks['sla_name'] = ''
                dict_tasks['sla_id'] = ''
                task_request_list_final.append(dict_tasks)

            for req in daily_tm_requests:
                dict_requests = {}
                dict_requests['tm_id'] = req.timesheet.id
                dict_requests['name'] = req.customer_request
                dict_requests['task_id'] = req.customer_request_id
                dict_requests['duration'] = req.timesheet.duration
                dict_requests['log_day'] = req.timesheet.log_day
                dict_requests['start_time'] = req.timesheet.start_time
                dict_requests['end_time'] = req.timesheet.end_time
                dict_requests['notes'] = req.timesheet.notes
                dict_requests['created_time'] = req.timesheet.created_time
                dict_requests['timesheet_type'] = 'request_type'
                dict_requests['sla_name'] = req.customer_request.sla.name
                dict_requests['sla_id'] = req.customer_request.sla.id
                task_request_list_final.append(dict_requests)

            new_dict['dictt'] = task_request_list_final
            
            sum_duration = 0 
            for ii in daily_tm_tasks:
	            sum_duration = sum_duration + ii.timesheet.durationsec()

            for req in daily_tm_requests:
                sum_duration = sum_duration + req.timesheet.durationsec()

            new_dict['duration'] = compute_duration(sum_duration)
            new_list2.append(new_dict)
    else: 
        new_list2 = ''

    template = loader.get_template('project_management/list_timesheet.html')
    context = {
        'timesheet_list': new_list2,
    }

    return HttpResponse(template.render(context, request))


def send_timesheet_for_approval(request):
    company_id = request.session['company_id']

    timesheet_list = request.GET.get('listTimesheet')
    json_data = json.loads(timesheet_list)
    uid = request.user.id
    id_user_dept = int(request.GET.get('id_user_dept'))

    for timesheet_id in json_data:
        tm_id = timesheet_id['tm']
        Timesheet.objects.filter(pk=int(tm_id)).update(status='SUBMITTED', is_submitted=True, date_submitted=datetime.date.today(), submitted_by_id=uid)

    timesheets_exist = Timesheet.objects.filter(status='INITIAL', project_team_member_id=id_user_dept, company_id=company_id).exists()
    if timesheets_exist == True:
        timesheet_list1 = Timesheet.objects.filter(status='INITIAL', project_team_member_id=id_user_dept, company_id=company_id)
        new_list = []

        for i in timesheet_list1:
	        new_list.append(i.log_day)            

        new_list2 = []
        new_list = set(new_list)
        new_list = sorted(new_list, reverse = True)
        for tm in new_list: 
            task_request_list_final = []           
            new_dict = {}
            new_dict['tim'] = tm
            daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__log_day=tm, timesheet__status='INITIAL', timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
            daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__log_day=tm, timesheet__status='INITIAL', timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
            
            for tsk in daily_tm_tasks:
                dict_tasks = {}
                dict_tasks['tm_id'] = tsk.timesheet.id
                dict_tasks['name'] = tsk.task
                dict_tasks['task_id'] = tsk.task_id
                dict_tasks['duration'] = tsk.timesheet.duration
                dict_tasks['log_day'] = tsk.timesheet.log_day
                dict_tasks['start_time'] = tsk.timesheet.start_time
                dict_tasks['end_time'] = tsk.timesheet.end_time
                dict_tasks['created_time'] = tsk.timesheet.created_time
                dict_tasks['notes'] = tsk.timesheet.notes
                dict_tasks['timesheet_type'] = 'task_type'
                dict_tasks['sla_name'] = ''
                dict_tasks['sla_id'] = ''
                task_request_list_final.append(dict_tasks)

            for req in daily_tm_requests:
                dict_requests = {}
                dict_requests['tm_id'] = req.timesheet.id
                dict_requests['name'] = req.customer_request
                dict_requests['task_id'] = req.customer_request_id
                dict_requests['duration'] = req.timesheet.duration
                dict_requests['log_day'] = req.timesheet.log_day
                dict_requests['start_time'] = req.timesheet.start_time
                dict_requests['end_time'] = req.timesheet.end_time
                dict_requests['notes'] = req.timesheet.notes
                dict_requests['created_time'] = req.timesheet.created_time
                dict_requests['timesheet_type'] = 'request_type'
                dict_requests['sla_name'] = req.customer_request.sla.name
                dict_requests['sla_id'] = req.customer_request.sla.id
                task_request_list_final.append(dict_requests)

            new_dict['dictt'] = task_request_list_final
            
            sum_duration = 0 
            for ii in daily_tm_tasks:
	            sum_duration = sum_duration + ii.timesheet.durationsec()
            
            for req in daily_tm_requests:
                sum_duration = sum_duration + req.timesheet.durationsec()

            new_dict['duration'] = compute_duration(sum_duration)
            new_list2.append(new_dict)
    else: 
        new_list2 = False

    template = loader.get_template('project_management/list_timesheet.html')
    context = {
        'timesheet_list': new_list2,
    }
    return HttpResponse(template.render(context, request))


def timesheet_pending_approval(request):
    id_user_dept = request.GET.get('id_user_dept')
    company_id = request.session['company_id']

    task_request_list_final = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__status='SUBMITTED', timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__status='SUBMITTED', timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        task_request_list_final.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        task_request_list_final.append(dict_requests)


    template = loader.get_template('project_management/list_timesheets_pending_approval.html')
    context = {
        'timesheet_list': task_request_list_final,
    }

    return HttpResponse(template.render(context, request))


def approve_timesheet_pane(request):
    uid = request.user.id
    company_id = request.session['company_id']
    department_id = request.session['department_id']

    task_request_list_final = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__status='SUBMITTED', timesheet__project_team_member_id__department_id=department_id, timesheet__company_id=company_id)
    daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__status='SUBMITTED', timesheet__project_team_member__department_id=department_id, timesheet__company_id=company_id)
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['project_team_member'] = tsk.timesheet.project_team_member
        task_request_list_final.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['project_team_member'] = req.timesheet.project_team_member
        task_request_list_final.append(dict_requests)

    template = loader.get_template('project_management/approve_timesheet_pane.html')
    context = {
        'timesheet_list': task_request_list_final,
    }

    return HttpResponse(template.render(context, request))


def save_timesheet_approvals(request):
    company_id = request.session['company_id']
    department_id = request.session['department_id']
    timesheet_list = request.GET.get('listTimesheetApproval')

    json_data = json.loads(timesheet_list)
    uid = request.user.id

    for timesheet_id in json_data:
        tm_id = timesheet_id['tm']
        tm_approve_status = timesheet_id['status']
        approver_comment = timesheet_id['approver_comment']
        Timesheet.objects.filter(pk=int(tm_id)).update(status=tm_approve_status, approved=True, date_approved=datetime.date.today(), approved_by_id=uid, last_updated_date=datetime.date.today(), last_updated_by_id=uid, approver_notes=approver_comment)
    
    timesheet_list1 = Timesheet.objects.filter(status='SUBMITTED', company_id=company_id, project_team_member__department_id=department_id)
    template = loader.get_template('project_management/list_approve_timesheets.html')
    context = {
        'timesheet_list': timesheet_list1,
    }
    return HttpResponse(template.render(context, request))


def manage_approved_timesheets(request):
    uid = request.user.id
    company_id = request.session['company_id']
    department_id = request.session['department_id']

    task_request_list_final = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(Q(timesheet__status='ACCEPTED')|Q(timesheet__status='REJECTED'), timesheet__project_team_member_id__department_id=department_id, timesheet__company_id=company_id)
    daily_tm_requests = RequestTimesheetExtend.objects.filter(Q(timesheet__status='ACCEPTED')|Q(timesheet__status='REJECTED'), timesheet__project_team_member_id__department_id=department_id, timesheet__company_id=company_id)
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['project_team_member'] = tsk.timesheet.project_team_member
        dict_tasks['status'] = tsk.timesheet.status
        dict_tasks['approver_notes'] = tsk.timesheet.approver_notes
        dict_tasks['date_approved'] = tsk.timesheet.date_approved
        dict_tasks['approved_by'] = tsk.timesheet.approved_by
        dict_tasks['submitted_by'] = tsk.timesheet.submitted_by
        task_request_list_final.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['project_team_member'] = req.timesheet.project_team_member
        dict_requests['status'] = req.timesheet.status 
        dict_requests['approver_notes'] = req.timesheet.approver_notes
        dict_requests['date_approved'] = req.timesheet.date_approved
        dict_requests['approved_by'] = req.timesheet.approved_by
        dict_requests['submitted_by'] = req.timesheet.submitted_by
        task_request_list_final.append(dict_requests)

    template = loader.get_template('project_management/list_confirmed_timesheets.html')
    context = {
        'timesheet_list': task_request_list_final,
    }

    return HttpResponse(template.render(context, request))


def update_timesheet_approval(request):
    timesheet_id = request.GET.get('tm_id')
    new_status = request.GET.get('status_val')
    uid = request.user.id
    company_id = request.session['company_id']
    department_id = request.session['department_id']

    Timesheet.objects.filter(pk=int(timesheet_id)).update(status=new_status, last_updated_date=datetime.date.today(), last_updated_by_id=uid)

    task_request_list_final = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(Q(timesheet__status='ACCEPTED')|Q(timesheet__status='REJECTED'), timesheet__project_team_member_id__department_id=department_id, timesheet__company_id=company_id)
    daily_tm_requests = RequestTimesheetExtend.objects.filter(Q(timesheet__status='ACCEPTED')|Q(timesheet__status='REJECTED'), timesheet__project_team_member_id__department_id=department_id, timesheet__company_id=company_id)
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['project_team_member'] = tsk.timesheet.project_team_member
        dict_tasks['status'] = tsk.timesheet.status
        dict_tasks['approver_notes'] = tsk.timesheet.approver_notes
        dict_tasks['date_approved'] = tsk.timesheet.date_approved
        dict_tasks['approved_by'] = tsk.timesheet.approved_by
        dict_tasks['submitted_by'] = tsk.timesheet.submitted_by
        task_request_list_final.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['project_team_member'] = req.timesheet.project_team_member
        dict_requests['status'] = req.timesheet.status
        dict_requests['approver_notes'] = req.timesheet.approver_notes
        dict_requests['date_approved'] = req.timesheet.date_approved
        dict_requests['approved_by'] = req.timesheet.approved_by
        dict_requests['submitted_by'] = req.timesheet.submitted_by
        task_request_list_final.append(dict_requests)
    
    template = loader.get_template('project_management/list_confirmed_timesheets.html')
    context = {
        'timesheet_list': task_request_list_final,
    }

    return HttpResponse(template.render(context, request))


def view_user_approved_timesheets(request):
    id_user_dept = request.GET.get('id_user_dept')
    company_id = request.session['company_id']

    task_request_list_final = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__status='ACCEPTED', timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__status='ACCEPTED', timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['date_approved'] = tsk.timesheet.date_approved
        dict_tasks['approved_by'] = tsk.timesheet.approved_by
        task_request_list_final.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['date_approved'] = req.timesheet.date_approved
        dict_requests['approved_by'] = req.timesheet.approved_by
        task_request_list_final.append(dict_requests)

    template = loader.get_template('project_management/list_user_accepted_timesheets.html')
    context = {
        'timesheet_list': task_request_list_final,
    }

    return HttpResponse(template.render(context, request))


def manage_rejected_timesheets(request):
    id_user_dept = request.GET.get('id_user_dept')
    company_id = request.session['company_id']

    timesheet_list1 = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__status='REJECTED', timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__status='REJECTED', timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['date_approved'] = tsk.timesheet.date_approved
        dict_tasks['approved_by'] = tsk.timesheet.approved_by
        timesheet_list1.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['date_approved'] = req.timesheet.date_approved
        dict_requests['approved_by'] = req.timesheet.approved_by
        timesheet_list1.append(dict_requests)

    template = loader.get_template('project_management/list_user_rejected_timesheets.html')
    context = {
        'timesheet_list': timesheet_list1,
    }

    return HttpResponse(template.render(context, request))


def filter_pending_daily_timesheets_by_date(request):
    uid = int(request.GET.get('id_user_dept'))
    company_id = request.session['company_id']
    start_date1 = request.GET.get('start_date')
    end_date1 = request.GET.get('end_date')

    startdate = datetime.datetime.strptime(start_date1, '%d-%m-%Y')
    enddate = datetime.datetime.strptime(end_date1, '%d-%m-%Y')

    min_dt = datetime.datetime.combine(startdate, datetime.time.min)
    max_dt = datetime.datetime.combine(enddate, datetime.time.max)

    timesheet_list1 = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__status='SUBMITTED', timesheet__project_team_member_id=uid, timesheet__company_id=company_id, timesheet__log_day__range=(min_dt, max_dt))
    daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__status='SUBMITTED', timesheet__project_team_member_id=uid, timesheet__company_id=company_id, timesheet__log_day__range=(min_dt, max_dt))
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['status'] = tsk.timesheet.status
        timesheet_list1.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['status'] = req.timesheet.status
        timesheet_list1.append(dict_requests)

    template = loader.get_template('project_management/list_timesheets_pending_approval.html')
    context = {
        'timesheet_list': timesheet_list1,
    }

    return HttpResponse(template.render(context, request))


def filter_daily_proved_timesheets(request):
    uid = int(request.GET.get('id_user_dept'))
    company_id = request.session['company_id']
    start_date1 = request.GET.get('start_date')
    end_date1 = request.GET.get('end_date')

    startdate = datetime.datetime.strptime(start_date1, '%d-%m-%Y')
    enddate = datetime.datetime.strptime(end_date1, '%d-%m-%Y')

    min_dt = datetime.datetime.combine(startdate, datetime.time.min)
    max_dt = datetime.datetime.combine(enddate, datetime.time.max)
    
    timesheet_list1 = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(Q(timesheet__status='ACCEPTED')|Q(timesheet__status='REJECTED'), timesheet__project_team_member_id=uid, timesheet__company_id=company_id, timesheet__log_day__range=(min_dt, max_dt))
    daily_tm_requests = RequestTimesheetExtend.objects.filter(Q(timesheet__status='ACCEPTED')|Q(timesheet__status='REJECTED'), timesheet__project_team_member_id=uid, timesheet__company_id=company_id, timesheet__log_day__range=(min_dt, max_dt))
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['date_approved'] = tsk.timesheet.date_approved
        dict_tasks['approved_by'] = tsk.timesheet.approved_by
        timesheet_list1.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['date_approved'] = req.timesheet.date_approved
        dict_requests['approved_by'] = req.timesheet.approved_by
        timesheet_list1.append(dict_requests)

    template = loader.get_template('project_management/list_user_accepted_timesheets.html')
    context = {
        'timesheet_list': timesheet_list1,
    }

    return HttpResponse(template.render(context, request))

    
def filter_all_member_unapproved_timesheets(request):
    uid = request.user.id
    company_id = request.session['company_id']
    start_date1 = request.GET.get('start_date')
    end_date1 = request.GET.get('end_date')
    department_id = request.session['department_id']

    startdate = datetime.datetime.strptime(start_date1, '%d-%m-%Y')
    enddate = datetime.datetime.strptime(end_date1, '%d-%m-%Y')

    min_dt = datetime.datetime.combine(startdate, datetime.time.min)
    max_dt = datetime.datetime.combine(enddate, datetime.time.max)
    
    timesheet_list1 = Timesheet.objects.filter(status='SUBMITTED', company_id=company_id, log_day__range=(min_dt, max_dt), project_team_member__department_id=department_id)
    template = loader.get_template('project_management/list_approve_timesheets.html')
    context = {
        'timesheet_list': timesheet_list1,
    }
    return HttpResponse(template.render(context, request))


def filter_all_member_approved_timesheets(request):
    uid = request.user.id
    company_id = request.session['company_id']
    start_date1 = request.GET.get('start_date')
    end_date1 = request.GET.get('end_date')
    department_id = request.session['department_id']

    startdate = datetime.datetime.strptime(start_date1, '%d-%m-%Y')
    enddate = datetime.datetime.strptime(end_date1, '%d-%m-%Y')

    min_dt = datetime.datetime.combine(startdate, datetime.time.min)
    max_dt = datetime.datetime.combine(enddate, datetime.time.max)
            
    task_request_list_final = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(Q(timesheet__status='ACCEPTED')|Q(timesheet__status='REJECTED'), timesheet__project_team_member_id__department_id=department_id, timesheet__company_id=company_id, timesheet__log_day__range=(min_dt, max_dt))
    daily_tm_requests = RequestTimesheetExtend.objects.filter(Q(timesheet__status='ACCEPTED')|Q(timesheet__status='REJECTED'), timesheet__project_team_member_id__department_id=department_id, timesheet__company_id=company_id, timesheet__log_day__range=(min_dt, max_dt))
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['project_team_member'] = tsk.timesheet.project_team_member
        dict_tasks['status'] = tsk.timesheet.status
        dict_tasks['approver_notes'] = tsk.timesheet.approver_notes
        dict_tasks['date_approved'] = tsk.timesheet.date_approved
        dict_tasks['approved_by'] = tsk.timesheet.approved_by
        dict_tasks['submitted_by'] = tsk.timesheet.submitted_by
        task_request_list_final.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['project_team_member'] = req.timesheet.project_team_member
        dict_requests['status'] = req.timesheet.status
        dict_requests['approver_notes'] = req.timesheet.approver_notes
        dict_requests['date_approved'] = req.timesheet.date_approved
        dict_requests['approved_by'] = req.timesheet.approved_by
        dict_requests['submitted_by'] = req.timesheet.submitted_by
        task_request_list_final.append(dict_requests)

    template = loader.get_template('project_management/list_confirmed_timesheets.html')
    context = {
        'timesheet_list': task_request_list_final,
    }

    return HttpResponse(template.render(context, request))


def timesheets_report(request):
    company_id = request.session['company_id']

    template = loader.get_template('project_management/timesheetsReport.html')
    context = {}

    return HttpResponse(template.render(context, request))


def user_general_timesheet_report(request):
    uid = request.user.id
    company_id = request.session['company_id']
    new_list = []

    timesheet_list1 = Timesheet.objects.filter(company_id=company_id, project_team_member_id=uid).exists()
    if timesheet_list1 == True:
        
        timesheet_list2 = Timesheet.objects.filter(company_id=company_id, project_team_member_id=uid)
        for i in timesheet_list2:
            new_dict = {}
            new_dict['id'] = i.id
            new_dict['title'] = i.task.name
            if i.notes is None:
                new_dict['description'] = "No Added Notes"
            else:
                new_dict['description'] = i.notes
            
            log_day_date = i.log_day
            new_dict['start'] = log_day_date.strftime("%Y-%m-%d") + 'T' + i.start_time.strftime("%H:%M:%S")
            new_dict['end'] = log_day_date.strftime("%Y-%m-%d") + 'T' + i.end_time.strftime("%H:%M:%S")
            new_dict['icon'] = "clock-o"
            new_list.append(new_dict)

    data3 = {
        'tm': new_list
    }
    return JsonResponse(data3)


def save_resent_timesheet(request):
    company_id = request.session['company_id']
    structural_state = request.GET.get('structural_state')
    log_day = request.GET.get('id_log_day')
    uid = request.user.id
    log_day = datetime.datetime.strptime(log_day, '%d-%m-%Y')
    id_user_dept = int(request.GET.get('id_user_dept'))

    if structural_state == 'project':
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')
        task = int(request.GET.get('id_task'))
        timesheet_id = int(request.GET.get('timesheet_id'))
        notes = request.GET.get('notes')
        comment = request.GET.get('comment')

        start_time1 = datetime.datetime.strptime(start_time, '%I:%M %p')
        end_time1 =   datetime.datetime.strptime(end_time, '%I:%M %p')

        Timesheet.objects.filter(pk=int(timesheet_id)).update(status='SUBMITTED', log_day=log_day, start_time=start_time1, end_time=end_time1, last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=notes, is_resubmitted=True)
        TaskTimesheetExtend.objects.filter(pk=timesheet_id).update(task_id=task)

        obj1 = ResubmittedTimesheet(comment=comment, resubmitted_by_id=uid, timesheet_id=int(timesheet_id))
        obj1.save()

    else:
        id_assigned_requests = request.GET.get('id_assigned_requests')
        timesheet_id2 = int(request.GET.get('timesheet_id2'))
        start_time02 = request.GET.get('start_time2')
        end_time02 = request.GET.get('end_time2')
        id_timesheet_notes02 = request.GET.get('notes2')
        comment2 = request.GET.get('comment2')
        
        start_time003 = datetime.datetime.strptime(start_time02, '%I:%M %p')
        end_time003 =   datetime.datetime.strptime(end_time02, '%I:%M %p')

        Timesheet.objects.filter(pk=int(timesheet_id2)).update(status='SUBMITTED', log_day=log_day, start_time=start_time003, end_time=end_time003, last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=id_timesheet_notes02, is_resubmitted=True)
        RequestTimesheetExtend.objects.filter(pk=timesheet_id2).update(customer_request_id=id_assigned_requests) 

        obj2 = ResubmittedTimesheet(comment=comment2, resubmitted_by_id=uid, timesheet_id=int(timesheet_id2))
        obj2.save()

    timesheet_list1 = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__status='REJECTED', timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__status='REJECTED', timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['date_approved'] = tsk.timesheet.date_approved
        dict_tasks['approved_by'] = tsk.timesheet.approved_by
        timesheet_list1.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['date_approved'] = req.timesheet.date_approved
        dict_requests['approved_by'] = req.timesheet.approved_by
        timesheet_list1.append(dict_requests)

    template = loader.get_template('project_management/list_user_rejected_timesheets.html')
    
    rejected_count = Timesheet.objects.filter(Q(status='REJECTED'), company_id=company_id, project_team_member_id=id_user_dept).count()
    context = {
        'timesheet_list': timesheet_list1,
        'rejected_count': rejected_count
    }

    return HttpResponse(template.render(context, request))


def manage_timesheet_resubmissions(request):
    timesheetid = request.GET.get('timesheetid')

    timesheet_list1 = ResubmittedTimesheet.objects.filter(timesheet_id=int(timesheetid))

    template = loader.get_template('project_management/list_resubmitted_timesheets.html')
    context = {
        'timesheet_list': timesheet_list1,
    }

    return HttpResponse(template.render(context, request))


def update_approver_comment(request):
    company_id = request.session['company_id']
    uid = request.user.id
    appr_comment = request.GET.get('appr_comment')
    tm_id = request.GET.get('tm_id')
    department_id = request.session['department_id']
    
    Timesheet.objects.filter(pk=int(tm_id)).update(last_updated_date=datetime.date.today(), last_updated_by_id=uid, approver_notes=appr_comment)

    task_request_list_final = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(Q(timesheet__status='ACCEPTED')|Q(timesheet__status='REJECTED'), timesheet__project_team_member_id__department_id=department_id, timesheet__company_id=company_id)
    daily_tm_requests = RequestTimesheetExtend.objects.filter(Q(timesheet__status='ACCEPTED')|Q(timesheet__status='REJECTED'), timesheet__project_team_member_id__department_id=department_id, timesheet__company_id=company_id)
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['project_team_member'] = tsk.timesheet.project_team_member
        dict_tasks['status'] = tsk.timesheet.status
        dict_tasks['approver_notes'] = tsk.timesheet.approver_notes
        dict_tasks['date_approved'] = tsk.timesheet.date_approved
        dict_tasks['approved_by'] = tsk.timesheet.approved_by
        dict_tasks['submitted_by'] = tsk.timesheet.submitted_by
        task_request_list_final.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['project_team_member'] = req.timesheet.project_team_member
        dict_requests['status'] = req.timesheet.status
        dict_requests['approver_notes'] = req.timesheet.approver_notes
        dict_requests['date_approved'] = req.timesheet.date_approved
        dict_requests['approved_by'] = req.timesheet.approved_by
        dict_requests['submitted_by'] = req.timesheet.submitted_by
        task_request_list_final.append(dict_requests)
    
    template = loader.get_template('project_management/list_confirmed_timesheets.html')
    context = {
        'timesheet_list': task_request_list_final,
    }

    return HttpResponse(template.render(context, request))


def add_new_timesheet_from_calender(request):
    company_id = request.session['company_id']
    log_date = request.GET.get('log_date')

    project_list = Project.objects.filter(company=int(company_id))
    
    template = loader.get_template('project_management/add_new_calender_timesheet.html')
    context = {
        'project_list': project_list,
        'log_date': datetime.datetime.strptime(log_date, "%Y-%m-%d").strftime("%d-%m-%Y")
    }

    return HttpResponse(template.render(context, request))


def add_new_timesheet_from_datepaginator(request):
    company_id = request.session['company_id']
    log_date = request.GET.get('log_date')
    id_user_dept = int(request.GET.get('id_user_dept'))

    members = ProjectTeamMember.objects.filter(member=id_user_dept)
    team_list = []
    for value in members:  
        team_members = ProjectTeamMember.project_team.through.objects.filter(projectteammember=value.id)

        for obj in team_members:
            team_name = obj.projectteam
            team_list.append(team_name)
    
    project_list = []
    for team in team_list:
        project_id = team.project_id
        
        project = Project.objects.get(id=project_id)
        project_dict = {}
        project_dict['id'] = project.id
        project_dict['name'] = project.name

        project_list.append(project_dict)
    
    template = loader.get_template('project_management/add_new_calender_timesheet.html')
    context = {
        'project_list': project_list,
        'log_date': datetime.datetime.strptime(log_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
        'user_id' : id_user_dept,
        'user_name' : User.objects.get(id=int(id_user_dept)),

        'client_list' : Company.objects.filter(category__category_value='CLIENT', parent=company_id)
    }

    return HttpResponse(template.render(context, request))


def save_calender_timesheet(request):
    uid = request.user.id
    company_id = request.session['company_id']
    id_log_day = request.GET.get('id_log_day')
    id_task = request.GET.get('id_task')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    id_timesheet_notes = request.GET.get('notes')

    log_day = datetime.datetime.strptime(id_log_day, '%d-%m-%Y')
    start_time1 = datetime.datetime.strptime(start_time, '%I:%M %p')
    end_time1 =   datetime.datetime.strptime(end_time, '%I:%M %p')
    
    obj = Timesheet(log_day=log_day, start_time=start_time1, end_time=end_time1, added_by_id=uid, task_id=int(id_task), project_team_member_id=uid, company_id=int(company_id), last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=id_timesheet_notes)
    obj.save()

    template = loader.get_template('project_management/timesheet_calender.html')
    context = {}

    return HttpResponse(template.render(context, request))


def save_paginator_timesheet(request):
    structureRadioValue = request.GET.get('structureRadioValue')
    uid = request.user.id
    company_id = request.session['company_id']
    id_log_day = request.GET.get('id_log_day')
    id_dept_user = int(request.GET.get('uid'))
    log_day = datetime.datetime.strptime(id_log_day, '%d-%m-%Y')

    if structureRadioValue == 'project':
        id_task = request.GET.get('id_task')
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')
        id_timesheet_notes = request.GET.get('notes')

        start_time1 = datetime.datetime.strptime(start_time, '%I:%M %p')
        end_time1 =   datetime.datetime.strptime(end_time, '%I:%M %p')
        
        obj = Timesheet(log_day=log_day, start_time=start_time1, end_time=end_time1, added_by_id=uid, project_team_member_id=id_dept_user, company_id=int(company_id), last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=id_timesheet_notes)
        obj.save()
        
        new_timesheet_id = obj.id
        if new_timesheet_id != "":
            TaskTimesheetExtend.objects.create(timesheet_id=new_timesheet_id, task_id=int(id_task))

    else:
        id_assigned_requests = request.GET.get('id_assigned_requests')

        start_time02 = request.GET.get('start_time2')
        end_time02 = request.GET.get('end_time2')
        id_timesheet_notes02 = request.GET.get('notes2')
        
        start_time003 = datetime.datetime.strptime(start_time02, '%I:%M %p')
        end_time003 =   datetime.datetime.strptime(end_time02, '%I:%M %p')

        obj2 = Timesheet(log_day=log_day, start_time=start_time003, end_time=end_time003, added_by_id=uid, project_team_member_id=id_dept_user, company_id=int(company_id), last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=id_timesheet_notes02)
        obj2.save()

        new_timesheet_id2 = obj2.id
        if new_timesheet_id2 != "":
            RequestTimesheetExtend.objects.create(timesheet_id=new_timesheet_id2, customer_request_id=int(id_assigned_requests))

    timesheet_list1 = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__log_day=log_day, timesheet__project_team_member_id=id_dept_user, timesheet__company_id=company_id)
    daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__log_day=log_day, timesheet__project_team_member_id=id_dept_user, timesheet__company_id=company_id)
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['date_approved'] = tsk.timesheet.date_approved
        dict_tasks['approved_by'] = tsk.timesheet.approved_by
        dict_tasks['status'] = tsk.timesheet.status
        timesheet_list1.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['date_approved'] = req.timesheet.date_approved
        dict_requests['approved_by'] = req.timesheet.approved_by
        dict_requests['status'] = req.timesheet.status
        timesheet_list1.append(dict_requests)

    if Timesheet.objects.filter(log_day=log_day, status='INITIAL', company_id=company_id, project_team_member_id=id_dept_user).exists():
        intial_state = True
    else:
        intial_state = False
    
    sum_duration = 0 
    for ii in daily_tm_tasks:
        sum_duration = sum_duration + ii.timesheet.durationsec()
    
    for req in daily_tm_requests:
        sum_duration = sum_duration + req.timesheet.durationsec()

    tm_day_duration = compute_duration(sum_duration)

    template = loader.get_template('project_management/list_date_timesheet.html')
    context = {
        'timesheet_list': timesheet_list1,
        'initial_status': intial_state,
        'tm_day_duration': tm_day_duration
    }

    return HttpResponse(template.render(context, request))


def calenderTimesheetView(request):
    timesheet_id = request.GET.get('timesheet_id')
    state = request.GET.get('state')
    dict_data = {}

    if state == 'project':
        tsk = TaskTimesheetExtend.objects.get(timesheet__id=int(timesheet_id))
        
        dict_data['tm_id'] = tsk.timesheet.id
        dict_data['name'] = tsk.task
        dict_data['task_id'] = tsk.task_id
        dict_data['duration'] = tsk.timesheet.duration
        dict_data['log_day'] = tsk.timesheet.log_day
        dict_data['start_time'] = tsk.timesheet.start_time
        dict_data['end_time'] = tsk.timesheet.end_time
        dict_data['created_time'] = tsk.timesheet.created_time
        dict_data['notes'] = tsk.timesheet.notes
        dict_data['timesheet_type'] = 'task_type'
        dict_data['sla_name'] = ''
        dict_data['sla_id'] = ''
        dict_data['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_data['date_submitted'] = tsk.timesheet.date_submitted
        dict_data['project_team_member'] = tsk.timesheet.project_team_member
        dict_data['status'] = tsk.timesheet.status
        dict_data['approver_notes'] = tsk.timesheet.approver_notes
        dict_data['date_approved'] = tsk.timesheet.date_approved
        dict_data['approved_by'] = tsk.timesheet.approved_by
        dict_data['submitted_by'] = tsk.timesheet.submitted_by
        dict_data['status'] = tsk.timesheet.status
        dict_data['is_submitted'] = tsk.timesheet.is_submitted
        dict_data['approved'] = tsk.timesheet.approved
    
    else:
        req = RequestTimesheetExtend.objects.get(timesheet__id=int(timesheet_id))
        dict_data['tm_id'] = req.timesheet.id
        dict_data['name'] = req.customer_request
        dict_data['task_id'] = req.customer_request_id
        dict_data['duration'] = req.timesheet.duration
        dict_data['log_day'] = req.timesheet.log_day
        dict_data['start_time'] = req.timesheet.start_time
        dict_data['end_time'] = req.timesheet.end_time
        dict_data['notes'] = req.timesheet.notes
        dict_data['created_time'] = req.timesheet.created_time
        dict_data['timesheet_type'] = 'request_type'
        dict_data['sla_name'] = req.customer_request.sla.name
        dict_data['sla_id'] = req.customer_request.sla.id
        dict_data['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_data['date_submitted'] = req.timesheet.date_submitted
        dict_data['project_team_member'] = req.timesheet.project_team_member
        dict_data['status'] = req.timesheet.status
        dict_data['approver_notes'] = req.timesheet.approver_notes
        dict_data['date_approved'] = req.timesheet.date_approved
        dict_data['approved_by'] = req.timesheet.approved_by
        dict_data['submitted_by'] = req.timesheet.submitted_by       
        dict_data['status'] = req.timesheet.status  
        dict_data['is_submitted'] = req.timesheet.is_submitted
        dict_data['approved'] = req.timesheet.approved

    template = loader.get_template('project_management/calender_timesheet_details.html')
    context = {
        'timesheetdetails': dict_data
    }

    return HttpResponse(template.render(context, request))


def timesheets_schedule_pane(request):
    company_id = request.session['company_id']

    template = loader.get_template('project_management/schedule_plan_pane.html')
    context = {}

    return HttpResponse(template.render(context, request))


def filter_timesheets_by_date(request):
    id_user_dept = int(request.GET.get('id_user_dept'))
    company_id = request.session['company_id']
    dateSelected = request.GET.get('dateSelected')
    log_day = datetime.datetime.strptime(dateSelected, '%d-%m-%Y')

    timesheet_list1 = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__log_day=log_day, timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__log_day=log_day, timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['date_approved'] = tsk.timesheet.date_approved
        dict_tasks['approved_by'] = tsk.timesheet.approved_by
        dict_tasks['status'] = tsk.timesheet.status
        timesheet_list1.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['date_approved'] = req.timesheet.date_approved
        dict_requests['approved_by'] = req.timesheet.approved_by
        dict_requests['status'] = req.timesheet.status
        timesheet_list1.append(dict_requests)

    if Timesheet.objects.filter(log_day=log_day, status='INITIAL', company_id=company_id, project_team_member_id=id_user_dept).exists():
        intial_state = True
    else:
        intial_state = False

    sum_duration = 0 
    for ii in daily_tm_tasks:
        sum_duration = sum_duration + ii.timesheet.durationsec()

    for req in daily_tm_requests:
        sum_duration = sum_duration + req.timesheet.durationsec()

    tm_day_duration = compute_duration(sum_duration)

    template = loader.get_template('project_management/list_date_timesheet.html')
    context = {
        'timesheet_list': timesheet_list1,
        'initial_status': intial_state,
        'tm_day_duration': tm_day_duration
    }

    return HttpResponse(template.render(context, request))


def table_timesheet_view(request):
    uid = request.user.id
    company_id = request.session['company_id']
    department_id = request.session['department_id']
    dept_users = User.objects.filter(Q(department_id=int(department_id)), ~Q(id = int(uid)))

    template = loader.get_template('project_management/timesheet_tableview.html')
    context = {
        'dept_users': dept_users,
        'user_id' : uid,
        'user_name' : User.objects.get(id=int(uid))
    }

    return HttpResponse(template.render(context, request))


def list_timesheet_view(request):
    uid = request.user.id
    company_id = request.session['company_id']
    department_id = request.session['department_id']

    rejected_count = Timesheet.objects.filter(Q(status='REJECTED'), company_id=company_id, project_team_member_id=uid).count()

    timesheets_exist = Timesheet.objects.filter(status='INITIAL', project_team_member_id=uid, company_id=company_id).exists()

    if timesheets_exist == True:
        timesheet_list1 = Timesheet.objects.filter(status='INITIAL', project_team_member_id=uid, company_id=company_id)
        new_list = []

        for i in timesheet_list1:
	        new_list.append(i.log_day)            

        new_list2 = []
        new_list = set(new_list)
        new_list = sorted(new_list, reverse = True)
        for tm in new_list: 
            task_request_list_final = []           
            new_dict = {}
            new_dict['tim'] = tm
            daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__log_day=tm, timesheet__status='INITIAL', timesheet__project_team_member_id=uid, timesheet__company_id=company_id)
            daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__log_day=tm, timesheet__status='INITIAL', timesheet__project_team_member_id=uid, timesheet__company_id=company_id)
            
            for tsk in daily_tm_tasks:
                dict_tasks = {}
                dict_tasks['tm_id'] = tsk.timesheet.id
                dict_tasks['name'] = tsk.task
                dict_tasks['task_id'] = tsk.task_id
                dict_tasks['duration'] = tsk.timesheet.duration
                dict_tasks['log_day'] = tsk.timesheet.log_day
                dict_tasks['start_time'] = tsk.timesheet.start_time
                dict_tasks['end_time'] = tsk.timesheet.end_time
                dict_tasks['notes'] = tsk.timesheet.notes
                dict_tasks['created_time'] = tsk.timesheet.created_time
                dict_tasks['timesheet_type'] = 'task_type'
                dict_tasks['sla_name'] = ''
                dict_tasks['sla_id'] = ''
                task_request_list_final.append(dict_tasks)

            for req in daily_tm_requests:
                dict_requests = {}
                dict_requests['tm_id'] = req.timesheet.id
                dict_requests['name'] = req.customer_request
                dict_requests['task_id'] = req.customer_request_id
                dict_requests['duration'] = req.timesheet.duration
                dict_requests['log_day'] = req.timesheet.log_day
                dict_requests['start_time'] = req.timesheet.start_time
                dict_requests['end_time'] = req.timesheet.end_time
                dict_requests['notes'] = req.timesheet.notes
                dict_requests['created_time'] = req.timesheet.created_time
                dict_requests['timesheet_type'] = 'request_type'
                dict_requests['sla_name'] = req.customer_request.sla.name
                dict_requests['sla_id'] = req.customer_request.sla.id
                task_request_list_final.append(dict_requests)

            new_dict['dictt'] = task_request_list_final
            
            sum_duration = 0 
            for ii in daily_tm_tasks:
	            sum_duration = sum_duration + ii.timesheet.durationsec()
            
            for req in daily_tm_requests:
                sum_duration = sum_duration + req.timesheet.durationsec()

            new_dict['duration'] = compute_duration(sum_duration)
            new_list2.append(new_dict)
    else: 
        new_list2 = ''

    dept_users = User.objects.filter(Q(department_id=int(department_id)), ~Q(id = int(uid)))

    template = loader.get_template('project_management/list_timesheet_view.html')
    context = {
        'timesheet_list': new_list2,
        'rejected_count': rejected_count,
        'dept_users': dept_users,
        'user_id' : uid,
        'user_name' : User.objects.get(id=int(uid))
    }

    return HttpResponse(template.render(context, request))


def send_timesheet_for_approval_paginator(request):
    company_id = request.session['company_id']
    timesheet_list = request.GET.get('listTimesheet')
    dateSelected = request.GET.get('dateSelected')
    log_day = datetime.datetime.strptime(dateSelected, '%Y-%m-%d')
    json_data = json.loads(timesheet_list)
    uid = request.user.id
    id_user_dept = int(request.GET.get('id_user_dept'))

    for timesheet_id in json_data:
        tm_id = timesheet_id['tm']
        Timesheet.objects.filter(pk=int(tm_id)).update(status='SUBMITTED', is_submitted=True, date_submitted=datetime.date.today(), submitted_by_id=uid)

    timesheet_list1 = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__log_day=log_day, timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__log_day=log_day, timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['date_approved'] = tsk.timesheet.date_approved
        dict_tasks['approved_by'] = tsk.timesheet.approved_by
        dict_tasks['status'] = tsk.timesheet.status
        timesheet_list1.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['date_approved'] = req.timesheet.date_approved
        dict_requests['approved_by'] = req.timesheet.approved_by
        dict_requests['status'] = req.timesheet.status
        timesheet_list1.append(dict_requests)
    
    if Timesheet.objects.filter(log_day=log_day, status='INITIAL', company_id=company_id, project_team_member_id=id_user_dept).exists():
        intial_state = True
    else:
        intial_state = False
    
    sum_duration = 0 
    for ii in daily_tm_tasks:
        sum_duration = sum_duration + ii.timesheet.durationsec()
    
    for req in daily_tm_requests:
        sum_duration = sum_duration + req.timesheet.durationsec()

    tm_day_duration = compute_duration(sum_duration)

    template = loader.get_template('project_management/list_date_timesheet.html')
    context = {
        'timesheet_list': timesheet_list1,
        'initial_status': intial_state,
        'tm_day_duration': tm_day_duration
    }

    return HttpResponse(template.render(context, request))


def delete_timesheet_in_paginator(request):
    company_id = request.session['company_id']
    id_user_dept = int(request.GET.get('id_user_dept'))
    dateSelected = request.GET.get('dateSelected')
    log_day = datetime.datetime.strptime(dateSelected, '%Y-%m-%d')
    
    structural_vale = request.GET.get('state')
    if structural_vale == 'project':
        timesheet_id = request.GET.get('timesheet_id')
        task_id = request.GET.get('task_id')

        TaskTimesheetExtend.objects.filter(pk=timesheet_id).delete()
        Timesheet.objects.filter(id=int(timesheet_id)).delete()
    else:
        timesheet_id2 = request.GET.get('timesheet_id2')
        req_id = request.GET.get('request_id')
        RequestTimesheetExtend.objects.filter(pk=timesheet_id2).delete()
        Timesheet.objects.filter(id=int(timesheet_id2)).delete()

    timesheet_list1 = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__log_day=log_day, timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__log_day=log_day, timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['date_approved'] = tsk.timesheet.date_approved
        dict_tasks['approved_by'] = tsk.timesheet.approved_by
        dict_tasks['status'] = tsk.timesheet.status
        timesheet_list1.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['date_approved'] = req.timesheet.date_approved
        dict_requests['approved_by'] = req.timesheet.approved_by
        dict_requests['status'] = req.timesheet.status
        timesheet_list1.append(dict_requests)

    if Timesheet.objects.filter(log_day=log_day, status='INITIAL', company_id=company_id, project_team_member_id=id_user_dept).exists():
        intial_state = True
    else:
        intial_state = False

    sum_duration = 0 
    for ii in daily_tm_tasks:
        sum_duration = sum_duration + ii.timesheet.durationsec()
    
    for req in daily_tm_requests:
        sum_duration = sum_duration + req.timesheet.durationsec()

    tm_day_duration = compute_duration(sum_duration)

    template = loader.get_template('project_management/list_date_timesheet.html')
    context = {
        'timesheet_list': timesheet_list1,
        'initial_status': intial_state,
        'tm_day_duration': tm_day_duration
    }
    return HttpResponse(template.render(context, request))


def save_update_paginator_timesheet(request):
    state = request.GET.get('state')
    dateSelected = request.GET.get('dateSelected')
    log_day = datetime.datetime.strptime(dateSelected, '%Y-%m-%d')
    company_id = request.session['company_id']

    id_user_dept = int(request.GET.get('id_user_dept'))
    log_day = request.GET.get('id_log_day')
    uid = request.user.id
    log_day = datetime.datetime.strptime(log_day, '%d-%m-%Y')
    
    if state == 'project':
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')
        task = int(request.GET.get('id_task'))
        timesheet_id = int(request.GET.get('timesheet_id'))
        notes = request.GET.get('notes')
        
        start_time1 = datetime.datetime.strptime(start_time, '%I:%M %p')
        end_time1 =   datetime.datetime.strptime(end_time, '%I:%M %p')
        
        Timesheet.objects.filter(pk=int(timesheet_id)).update(log_day=log_day, start_time=start_time1, end_time=end_time1, last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=notes)
        TaskTimesheetExtend.objects.filter(pk=timesheet_id).update(task_id=task)
    else:
        id_assigned_requests = request.GET.get('id_assigned_requests')

        start_time02 = request.GET.get('start_time2')
        end_time02 = request.GET.get('end_time2')
        id_timesheet_notes02 = request.GET.get('notes2')
        timesheet_id02 = int(request.GET.get('timesheet_id2'))
        notes02 = request.GET.get('notes2')
        
        start_time003 = datetime.datetime.strptime(start_time02, '%I:%M %p')
        end_time003 =   datetime.datetime.strptime(end_time02, '%I:%M %p')
        
        Timesheet.objects.filter(pk=int(timesheet_id02)).update(log_day=log_day, start_time=start_time003, end_time=end_time003, last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=notes02)
        RequestTimesheetExtend.objects.filter(pk=timesheet_id02).update(customer_request_id=id_assigned_requests) 

    task_request_list_final = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__log_day=log_day, timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__log_day=log_day, timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['project_team_member'] = tsk.timesheet.project_team_member
        dict_tasks['status'] = tsk.timesheet.status
        dict_tasks['approver_notes'] = tsk.timesheet.approver_notes
        dict_tasks['date_approved'] = tsk.timesheet.date_approved
        dict_tasks['approved_by'] = tsk.timesheet.approved_by
        dict_tasks['submitted_by'] = tsk.timesheet.submitted_by
        task_request_list_final.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['project_team_member'] = req.timesheet.project_team_member
        dict_requests['status'] = req.timesheet.status 
        dict_requests['approver_notes'] = req.timesheet.approver_notes
        dict_requests['date_approved'] = req.timesheet.date_approved
        dict_requests['approved_by'] = req.timesheet.approved_by
        dict_requests['submitted_by'] = req.timesheet.submitted_by
        task_request_list_final.append(dict_requests)

    sum_duration = 0 
    for ii in daily_tm_tasks:
        sum_duration = sum_duration + ii.timesheet.durationsec()
    
    for req in daily_tm_requests:
        sum_duration = sum_duration + req.timesheet.durationsec()
    tm_day_duration = compute_duration(sum_duration)

    if Timesheet.objects.filter(log_day=log_day, status='INITIAL', company_id=company_id, project_team_member_id=id_user_dept).exists():
        intial_state = True
    else:
        intial_state = False

    template = loader.get_template('project_management/list_date_timesheet.html')
    context = {
        'timesheet_list': task_request_list_final,
        'initial_status': intial_state,
        'tm_day_duration': tm_day_duration
    }

    return HttpResponse(template.render(context, request))


def save_resent_paginator_timesheet(request):
    dateSelected = request.GET.get('dateSelected')
    selected_day = datetime.datetime.strptime(dateSelected, '%Y-%m-%d')
    structural_state = request.GET.get('structural_state')

    company_id = request.session['company_id']

    log_day = request.GET.get('id_log_day')
    uid = request.user.id
    id_user_dept = int(request.GET.get('uid'))
    log_day = datetime.datetime.strptime(log_day, '%d-%m-%Y')


    if structural_state == 'project':
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')
        task = int(request.GET.get('id_task'))
        timesheet_id = int(request.GET.get('timesheet_id'))
        notes = request.GET.get('notes')
        comment = request.GET.get('comment')
        
        start_time1 = datetime.datetime.strptime(start_time, '%I:%M %p')
        end_time1 =   datetime.datetime.strptime(end_time, '%I:%M %p')
        
        Timesheet.objects.filter(pk=int(timesheet_id)).update(status='SUBMITTED', log_day=log_day, start_time=start_time1, end_time=end_time1, last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=notes, is_resubmitted=True)
        TaskTimesheetExtend.objects.filter(pk=timesheet_id).update(task_id=task)

        obj1 = ResubmittedTimesheet(comment=comment, resubmitted_by_id=uid, timesheet_id=int(timesheet_id))
        obj1.save()

    else:
        id_assigned_requests = request.GET.get('id_assigned_requests')
        timesheet_id2 = int(request.GET.get('timesheet_id2'))
        start_time02 = request.GET.get('start_time2')
        end_time02 = request.GET.get('end_time2')
        id_timesheet_notes02 = request.GET.get('notes2')
        comment2 = request.GET.get('comment2')
        
        start_time003 = datetime.datetime.strptime(start_time02, '%I:%M %p')
        end_time003 =   datetime.datetime.strptime(end_time02, '%I:%M %p')

        Timesheet.objects.filter(pk=int(timesheet_id2)).update(status='SUBMITTED', log_day=log_day, start_time=start_time003, end_time=end_time003, last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=id_timesheet_notes02, is_resubmitted=True)
        RequestTimesheetExtend.objects.filter(pk=timesheet_id2).update(customer_request_id=id_assigned_requests) 

        obj2 = ResubmittedTimesheet(comment=comment2, resubmitted_by_id=uid, timesheet_id=int(timesheet_id2))
        obj2.save()
        
    
    timesheet_list1 = []           
    daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__log_day=selected_day, timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__log_day=selected_day, timesheet__project_team_member_id=id_user_dept, timesheet__company_id=company_id)
    
    for tsk in daily_tm_tasks:
        dict_tasks = {}
        dict_tasks['tm_id'] = tsk.timesheet.id
        dict_tasks['name'] = tsk.task
        dict_tasks['task_id'] = tsk.task_id
        dict_tasks['duration'] = tsk.timesheet.duration
        dict_tasks['log_day'] = tsk.timesheet.log_day
        dict_tasks['start_time'] = tsk.timesheet.start_time
        dict_tasks['end_time'] = tsk.timesheet.end_time
        dict_tasks['created_time'] = tsk.timesheet.created_time
        dict_tasks['notes'] = tsk.timesheet.notes
        dict_tasks['timesheet_type'] = 'task_type'
        dict_tasks['sla_name'] = ''
        dict_tasks['sla_id'] = ''
        dict_tasks['get_resubmission_count'] = tsk.timesheet.get_resubmission_count
        dict_tasks['date_submitted'] = tsk.timesheet.date_submitted
        dict_tasks['project_team_member'] = tsk.timesheet.project_team_member
        dict_tasks['status'] = tsk.timesheet.status
        dict_tasks['approver_notes'] = tsk.timesheet.approver_notes
        dict_tasks['date_approved'] = tsk.timesheet.date_approved
        dict_tasks['approved_by'] = tsk.timesheet.approved_by
        dict_tasks['submitted_by'] = tsk.timesheet.submitted_by
        timesheet_list1.append(dict_tasks)

    for req in daily_tm_requests:
        dict_requests = {}
        dict_requests['tm_id'] = req.timesheet.id
        dict_requests['name'] = req.customer_request
        dict_requests['task_id'] = req.customer_request_id
        dict_requests['duration'] = req.timesheet.duration
        dict_requests['log_day'] = req.timesheet.log_day
        dict_requests['start_time'] = req.timesheet.start_time
        dict_requests['end_time'] = req.timesheet.end_time
        dict_requests['notes'] = req.timesheet.notes
        dict_requests['created_time'] = req.timesheet.created_time
        dict_requests['timesheet_type'] = 'request_type'
        dict_requests['sla_name'] = req.customer_request.sla.name
        dict_requests['sla_id'] = req.customer_request.sla.id
        dict_requests['get_resubmission_count'] = req.timesheet.get_resubmission_count
        dict_requests['date_submitted'] = req.timesheet.date_submitted
        dict_requests['project_team_member'] = req.timesheet.project_team_member
        dict_requests['status'] = req.timesheet.status 
        dict_requests['approver_notes'] = req.timesheet.approver_notes
        dict_requests['date_approved'] = req.timesheet.date_approved
        dict_requests['approved_by'] = req.timesheet.approved_by
        dict_requests['submitted_by'] = req.timesheet.submitted_by
        timesheet_list1.append(dict_requests)


    if Timesheet.objects.filter(log_day=log_day, status='INITIAL', company_id=company_id, project_team_member_id=id_user_dept).exists():
        intial_state = True
    else:
        intial_state = False
    
    sum_duration = 0 
    for ii in daily_tm_tasks:
        sum_duration = sum_duration + ii.timesheet.durationsec()
    
    for req in daily_tm_requests:
        sum_duration = sum_duration + req.timesheet.durationsec()

    tm_day_duration = compute_duration(sum_duration)

    template = loader.get_template('project_management/list_date_timesheet.html')
    context = {
        'timesheet_list': timesheet_list1,
        'initial_status': intial_state,
        'tm_day_duration': tm_day_duration
    }

    return HttpResponse(template.render(context, request))


def timesheets_weekly_report(request):
    template = loader.get_template('project_management/timesheet_weekly_report_pane.html')
    context = {}

    return HttpResponse(template.render(context, request))


def filter_users_timesheets_by_week(request):
    uid = request.user.id
    company_id = request.session['company_id']
    department_id = request.session['department_id']
    start_date1 = request.GET.get('start_date')
    end_date1 = request.GET.get('end_date')
    
    startdate = datetime.datetime.strptime(start_date1, '%d-%m-%Y') 
    enddate = datetime.datetime.strptime(end_date1, '%d-%m-%Y') + datetime.timedelta(days=1)
    # delta = timedelta(days=1)

    min_dt = datetime.datetime.combine(startdate, datetime.time.min)
    max_dt = datetime.datetime.combine(enddate, datetime.time.max)
    day_delta = timedelta(days=1) 
    
    dept_members_exist = User.objects.filter(company_id=company_id, department_id=department_id).exists()
    if dept_members_exist == True:
        dept_members = User.objects.filter(company_id=company_id, department_id=department_id)
        all_member_tms = []
        days_list = {}
        for mem in dept_members:
            new_dict = {}
            new_dict['memberid'] = mem.id
            new_dict['member'] = mem.first_name + " " + mem.last_name
            for i in range((enddate - startdate).days):
                days_list['name'] = "User"
                days_list['day'+str(i)] = startdate + i*day_delta
                days_list['no'] = "#"

                duration = Timesheet.objects.filter(log_day=(startdate + i*day_delta), project_team_member_id=mem.id, company_id=company_id)
                sum_duration = 0
                for ii in duration:
                    sum_duration = sum_duration + ii.durationsec()
                new_dict['day'+str(i)] = compute_duration(sum_duration)
            all_member_tms.append(new_dict)
    else:
        all_member_tms = ''
        days_list = ''

    template = loader.get_template('project_management/list_users_timesheet_by_week.html')
    context = {
        'timesheet_list': all_member_tms,
        'days_list': days_list
    }

    return HttpResponse(template.render(context, request))


def timesheets_project_report(request):
    template = loader.get_template('project_management/timesheet_project_report_pane.html')
    context = {}
    
    return HttpResponse(template.render(context, request))


def filter_project_timesheets_by_week(request):
    uid = request.user.id
    company_id = request.session['company_id']
    department_id = request.session['department_id']
    start_date1 = request.GET.get('start_date')
    end_date1 = request.GET.get('end_date')
    
    startdate = datetime.datetime.strptime(start_date1, '%d-%m-%Y') 
    enddate = datetime.datetime.strptime(end_date1, '%d-%m-%Y') + datetime.timedelta(days=1)
    # delta = timedelta(days=1)

    min_dt = datetime.datetime.combine(startdate, datetime.time.min)
    max_dt = datetime.datetime.combine(enddate, datetime.time.max)
    day_delta = timedelta(days=1) 
    
    dept_projects_exist = Project.objects.filter(company=company_id, company__department=department_id).exists()
    if dept_projects_exist == True:
        dept_proj = Project.objects.filter(company=company_id, company__department=department_id)
        all_member_tms = []
        days_list = {}
        for pro in dept_proj:
            new_dict = {}
            new_dict['projectid'] = pro.id
            new_dict['project_name'] = pro.name
            proj_team_exist = ProjectTeam.objects.filter(project_id=pro.id).exists()
            if proj_team_exist == True:
                proj_team_id = ProjectTeam.objects.get(project_id=pro.id)
                proj_team_member_exist = ProjectTeamMember.objects.filter(project_team=proj_team_id).exists()
                proj_team_members = ProjectTeamMember.objects.filter(project_team=proj_team_id)
                list_mem_tms = []
                for each_memb in proj_team_members:
                    counter = 0
                    new_dict2 = {}
                    for i in range((enddate - startdate).days):
                        # TABLE HEADER
                        days_list['name'] = "Project"
                        days_list['user'] = "Name"
                        days_list['day'+str(i)] = startdate + i*day_delta
                        days_list['no'] = "#"
                        # TABLE HEADER

                        duration = Timesheet.objects.filter(log_day=(startdate + i*day_delta), project_team_member_id=each_memb.member.id, company_id=company_id)
                        
                        sum_duration = 0 
                        for ii in duration:
                            sum_duration = sum_duration + ii.durationsec()
                        new_dict2['day'+str(i)] = sum_duration
                    new_dict2['mem'+str(counter)] = each_memb.member.first_name + ' ' + each_memb.member.last_name
                    counter = counter + 1
                    list_mem_tms.append(new_dict2)
            new_dict['mem_timesheets'] = list_mem_tms
            all_member_tms.append(new_dict)

        final_list = []
        proj_set = set()
        for rr in all_member_tms:
            for yy in rr['mem_timesheets']:
                dict_mems = {}
                if(rr['projectid'] not in proj_set):
                    proj_set.add(rr['projectid'])
                    dict_mems['pro'] = rr['project_name']
                else:
                    dict_mems['pro'] = ''
                dict_mems['mem'] = yy['mem0']
                dict_mems['day0'] = compute_duration(yy['day0']) 
                dict_mems['day1'] = compute_duration(yy['day1'])
                dict_mems['day2'] = compute_duration(yy['day2'])
                dict_mems['day3'] = compute_duration(yy['day3'])
                dict_mems['day4'] = compute_duration(yy['day4'])
                dict_mems['day5'] = compute_duration(yy['day5'])
                dict_mems['day6'] = compute_duration(yy['day6'])
                
                dict_mems['mem_total'] = compute_duration(yy['day0'] + yy['day1'] + yy['day2'] + yy['day3'] + yy['day4'] + yy['day5'] + yy['day6'])
                final_list.append(dict_mems)
        
        all_member_tms = final_list
    else:
        all_member_tms = ''
        days_list = ''

    template = loader.get_template('project_management/list_project_timesheet_by_week.html')
    context = {
        'timesheet_list': all_member_tms,
        'days_list': days_list
    }

    return HttpResponse(template.render(context, request))


def select_daily_timesheets_by_user(request):
    id_user_dept = request.GET.get('id_user_dept')

    uid = int(id_user_dept)
    company_id = request.session['company_id']
    department_id = request.session['department_id']

    rejected_count = Timesheet.objects.filter(Q(status='REJECTED'), company_id=company_id, project_team_member_id=uid).count()

    timesheets_exist = Timesheet.objects.filter(status='INITIAL', project_team_member_id=uid, company_id=company_id).exists()

    if timesheets_exist == True:
        timesheet_list1 = Timesheet.objects.filter(status='INITIAL', project_team_member_id=uid, company_id=company_id)
        new_list = []

        for i in timesheet_list1:
	        new_list.append(i.log_day)            

        new_list2 = []
        new_list = set(new_list)
        new_list = sorted(new_list, reverse = True)
        for tm in new_list: 
            task_request_list_final = []           
            new_dict = {}
            new_dict['tim'] = tm
            daily_tm_tasks = TaskTimesheetExtend.objects.filter(timesheet__log_day=tm, timesheet__status='INITIAL', timesheet__project_team_member_id=uid, timesheet__company_id=company_id)
            daily_tm_requests = RequestTimesheetExtend.objects.filter(timesheet__log_day=tm, timesheet__status='INITIAL', timesheet__project_team_member_id=uid, timesheet__company_id=company_id)
            
            for tsk in daily_tm_tasks:
                dict_tasks = {}
                dict_tasks['tm_id'] = tsk.timesheet.id
                dict_tasks['name'] = tsk.task
                dict_tasks['task_id'] = tsk.task_id
                dict_tasks['duration'] = tsk.timesheet.duration
                dict_tasks['log_day'] = tsk.timesheet.log_day
                dict_tasks['start_time'] = tsk.timesheet.start_time
                dict_tasks['end_time'] = tsk.timesheet.end_time
                dict_tasks['notes'] = tsk.timesheet.notes
                dict_tasks['created_time'] = tsk.timesheet.created_time
                dict_tasks['timesheet_type'] = 'task_type'
                dict_tasks['sla_name'] = ''
                dict_tasks['sla_id'] = ''
                task_request_list_final.append(dict_tasks)

            for req in daily_tm_requests:
                dict_requests = {}
                dict_requests['tm_id'] = req.timesheet.id
                dict_requests['name'] = req.customer_request
                dict_requests['task_id'] = req.customer_request_id
                dict_requests['duration'] = req.timesheet.duration
                dict_requests['log_day'] = req.timesheet.log_day
                dict_requests['start_time'] = req.timesheet.start_time
                dict_requests['end_time'] = req.timesheet.end_time
                dict_requests['notes'] = req.timesheet.notes
                dict_requests['created_time'] = req.timesheet.created_time
                dict_requests['timesheet_type'] = 'request_type'
                dict_requests['sla_name'] = req.customer_request.sla.name
                dict_requests['sla_id'] = req.customer_request.sla.id
                task_request_list_final.append(dict_requests)

            new_dict['dictt'] = task_request_list_final
            
            sum_duration = 0 
            for ii in daily_tm_tasks:
	            sum_duration = sum_duration + ii.timesheet.durationsec()
            
            for req in daily_tm_requests:
                sum_duration = sum_duration + req.timesheet.durationsec()

            new_dict['duration'] = compute_duration(sum_duration)
            new_list2.append(new_dict)
    else: 
        new_list2 = ''

    dept_users = User.objects.filter(department_id=int(department_id))
    template = loader.get_template('project_management/filtered_daily_timesheets_users.html')
    context = {
        'timesheet_list': new_list2,
        'rejected_count': rejected_count,
        'dept_users': dept_users
    }

    return HttpResponse(template.render(context, request))


def select_table_timesheets_by_user(request):
    uid = request.GET.get('id_user_dept')
    company_id = request.session['company_id']

    template = loader.get_template('project_management/filter_table_timesheets_by_user.html')
    context = {
        'user_id' : uid,
        'user_name' : User.objects.get(id=int(uid))
    }
    
    return HttpResponse(template.render(context, request))


def compute_duration(sec):
    return '{}'.format(str(timedelta(seconds=sec)))


# project code format
class ListCodeFormat(ListView):
    template_name = 'project_management/list_code_format.html'
    context_object_name = 'list_code_formats'

    def get_queryset(self):
        return ProjectCode.objects.all()


class AddCodeFormat(CreateView):
    model = ProjectCode
    fields = ['project_code']
    template_name = 'project_management/add_code_format.html'
    success_url = reverse_lazy('listCodeFormat')


class UpdateCodeFormat(UpdateView):
    model = ProjectCode
    fields = ['project_code']
    template_name = 'project_management/update_code_format.html'
    success_url = reverse_lazy('listCodeFormat')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        code_id = int(self.request.GET['code_id'])
        context['code_id'] = code_id
        return context


class DeleteCodeFormat(DeleteView):
    model = ProjectCode
    success_url = reverse_lazy('listCodeFormat')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


def validate_project_code(request):
    """checking if project_code has already been created"""

    project_code_count = ProjectCode.objects.all().count()
    data = {}
    if project_code_count == 0:

        data = {
            "count": True
        }
    else:
        data = {
            "count" : False
        }

    return JsonResponse(data)


def populate_upload_document(request):
    project_id = request.GET.get('project_id')

    project = Project.objects.get(id= project_id)
    project_name = project.name
      
    template = loader.get_template('project_management/upload_document.html')
    context = {
        'project_id': project_id,
        'project_name': project_name
    }

    return HttpResponse(template.render(context, request))


def upload_document(request):
    if request.method == 'POST' and request.is_ajax():
        project_id = request.POST.get('project')
        title = request.POST.get("title")
        description = request.POST.get('document_description')
        document = request.FILES['document']
        created_by = request.user.id

        if title == "":
            title = None
        if description == "":
            description = None
        project = Project.objects.get(id=project_id)

        user_id = User.objects.get(id=created_by)

        document_upload = ProjectDocument(title=title, document=document, document_description=description,
        created_by=user_id, project=project)

        document_upload.save()

        response_data = {
            'success': 'Document uploaded successfully',
            'state': True,
        }
        
        return JsonResponse(response_data)

def staff_utilization(request):
    """generate staff utilization report"""

    return render(request, 'project_management/staff_report.html', {})
    

# staff utilization report
def staff_utilization_report(request):
    """ returns timesheet values for single individual """

    start_time = request.GET.get('start', None)
    end_time = request.GET.get('end', None)

    convert_start = datetime.datetime.strptime(start_time, "%d-%m-%Y").strftime("%Y-%m-%d")
    convert_end = datetime.datetime.strptime(end_time, "%d-%m-%Y").strftime("%Y-%m-%d")

    new_start = datetime.datetime.strptime(convert_start, "%Y-%m-%d")
    new_end = datetime.datetime.strptime(convert_end, "%Y-%m-%d")

    start = date(new_start.year, new_start.month, new_start.day)
    end = date(new_end.year, new_end.month, new_end.day)
    
    # getting the days in between start date and end date
    delta = end - start

    all_members = [] 
    
    users = User.objects.all()
    day_list = []

    for j in range(delta.days + 1):
        day = start + timedelta(days=j)
        new_day = day.strftime("%Y-%m-%d")

        strip_date = datetime.datetime.strptime(new_day, "%Y-%m-%d")
        split_date = date(strip_date.year, strip_date.month, strip_date.day);
        date_index = split_date.weekday()
        cal = calendar.day_name[date_index]
        
        if cal == 'Saturday' or cal == 'Sunday':
            pass
        else:
            day_list.append(new_day)

    expected_hours = len(day_list)
    counter = 0  

    for user in users:
        sum_timesheet = 0
        counter += 1 
        timesheet_dict = {}
        timesheet_dict['id'] = counter
        timesheet_dict["name"] = user.first_name + " " + user.last_name

        
        for i in range(delta.days+1):
            day = start + timedelta(days=i)
            new_day = day.strftime("%Y-%m-%d") 
            strip_date = datetime.datetime.strptime(new_day, "%Y-%m-%d")
            split_date = date(strip_date.year, strip_date.month, strip_date.day);
            date_index = split_date.weekday()
            cal = calendar.day_name[date_index]
            
            if cal == 'Saturday' or cal == 'Sunday':
                pass
            else:
                timesheet = Timesheet.objects.filter(log_day=new_day, added_by=user.id)
                for time in timesheet:
                    sum_timesheet = sum_timesheet + time.durationsec()
                    
        timesheet_dict['duration'] = sum_timesheet /3600 
        timesheet_dict['expected_hours']  = expected_hours * 8.5
        availability = timesheet_dict['duration']/timesheet_dict['expected_hours']
        percent = '%'
        timesheet_dict['timesheet/available'] = str(round(availability, 2)) + percent
        all_members.append(timesheet_dict)
    
    # converting user_list to json acceptable data
    list_users = json.dumps(all_members)
    data = {
        'members': list_users,
    }
    return JsonResponse(data)


def fetch_members_by_project(request):
    """return project team_members in project"""
    project_id = int(request.GET.get('project_id'))

    project = Project.objects.get(id=project_id)
    
    list_project_milestones = Milestone.objects.filter(project_id=int(project_id))

    if ProjectTeam.objects.filter(project_id=int(project_id)).exists():
        team = ProjectTeam.objects.get(project_id=project.id)
        project_team = team.id
        team_members = ProjectTeamMember.objects.filter(project_team=project_team)
        member_list = list(team_members)
    
        old = []

        if len(member_list) != 0:
            for member in member_list:
                old_user = User.objects.get(id=member.member_id)
                old.append(old_user)
 
        members = old

    else:
        members = ""

    data = {
        'mil': serializers.serialize("json", list_project_milestones),
        'members': serializers.serialize("json", members)
    }
    return JsonResponse(data)


# exporting as staff utilization report as excel
def export_staff_utilization(request):
    """exporting staff utilization"""
    if request.method == 'POST':
        start_time = request.POST.get('start')
        end_time = request.POST.get("end")        

        convert_start = datetime.datetime.strptime(start_time, "%d-%m-%Y").strftime("%Y-%m-%d")
        convert_end = datetime.datetime.strptime(end_time, "%d-%m-%Y").strftime("%Y-%m-%d")

        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename=Staff_utilization_report.xls'
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet("Staff Utilization Report")

        new_start = datetime.datetime.strptime(convert_start, "%Y-%m-%d")
        new_end = datetime.datetime.strptime(convert_end, "%Y-%m-%d")

        start = date(new_start.year, new_start.month, new_start.day)
        end = date(new_end.year, new_end.month, new_end.day)
        
        # getting the days in between start date and end date
        delta = end - start

        all_members = [] 
        
        users = User.objects.all()
        day_list = []

        for j in range(delta.days + 1):
            day = start + timedelta(days=j)
            new_day = day.strftime("%Y-%m-%d")

            strip_date = datetime.datetime.strptime(new_day, "%Y-%m-%d")
            split_date = date(strip_date.year, strip_date.month, strip_date.day);
            date_index = split_date.weekday()
            cal = calendar.day_name[date_index]
            
            if cal == 'Saturday' or cal == 'Sunday':
                pass
            else:
                day_list.append(new_day)

        expected_hours = len(day_list)
        counter = 0
        for user in users:
            sum_timesheet = 0
            counter += 1
            timesheet_dict = {}
            timesheet_dict['id'] = counter
            timesheet_dict["name"] = user.first_name + " " + user.last_name

            
            for i in range(delta.days+1):
                day = start + timedelta(days=i)
                new_day = day.strftime("%Y-%m-%d") 
                strip_date = datetime.datetime.strptime(new_day, "%Y-%m-%d")
                split_date = date(strip_date.year, strip_date.month, strip_date.day);
                date_index = split_date.weekday()
                cal = calendar.day_name[date_index]
                
                if cal == 'Saturday' or cal == 'Sunday':
                    pass
                else:
                    timesheet = Timesheet.objects.filter(log_day=new_day, added_by=user.id)
                    for time in timesheet:
                        sum_timesheet = sum_timesheet + time.durationsec()
                        
            timesheet_dict['timesheet_hours'] = sum_timesheet /3600 
            timesheet_dict['available_hours']  = expected_hours * 8.5
            availability = timesheet_dict['timesheet_hours']/timesheet_dict['available_hours']
            percent = '%'
            timesheet_dict['timesheet/available'] = str(round(availability, 2)) + percent
            all_members.append(timesheet_dict)
        
        print(all_members)
        row_num = 1

        columns = [(u"No.", 5000), (u"Name", 5000), (u"Timesheet Hrs", 5000), (u"Available Hrs", 5000),
                   (u"Timesheet/Available % ", 5000)
                   ]

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num][0], font_style)
            # set column width
            ws.col(col_num).width = columns[col_num][1]

        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1
        
        for obj in all_members:
            row_num += 1

            row = [
                obj['id'],
                obj['name'],
                obj['timesheet_hours'],
                obj['available_hours'],
                obj['timesheet/available']
            ]

            for col_num in range(len(row)):
                ws.write(row_num, col_num, str(row[col_num]), font_style)
                
        wb.save(response)
        print(f"{response} is the response")
        return response


def timesheet_monthly_report(request):

    template = loader.get_template('project_management/timesheet_monthly_report_pane.html')
    context = {}

    return HttpResponse(template.render(context, request))


def filter_monthly_timesheets(request):
    company_id = request.session['company_id']
    department_id = request.session['department_id']

    cur_month = datetime.datetime.now().strftime("%m").lstrip('0')
    cur_year = datetime.datetime.now().strftime("%Y").lstrip('0')
    today_date = datetime.datetime.today().date()

    first_day_of_month1 = today_date.replace(day=1)
    last_day_of_month1 = last_day_of_month(int(cur_year), int(cur_month))

    startdate = datetime.datetime.strptime(str(first_day_of_month1), '%Y-%m-%d') 
    enddate = datetime.datetime.strptime(str(last_day_of_month1), '%Y-%m-%d') + datetime.timedelta(days=1)

    min_dt = datetime.datetime.combine(startdate, datetime.time.min)
    max_dt = datetime.datetime.combine(enddate, datetime.time.max)
    day_delta = timedelta(days=1) 


    dept_members_exist = User.objects.filter(company_id=company_id, department_id=department_id).exists()
    if dept_members_exist == True:
        dept_members = User.objects.filter(company_id=company_id, department_id=department_id)
        all_member_tms = []
        for mem in dept_members:
            sum_duration = 0
            new_dict = {}
            new_dict['label'] = mem.first_name + " " + (mem.last_name)[0]
            for i in range((enddate - startdate).days):
                duration = Timesheet.objects.filter(log_day=(startdate + i*day_delta), project_team_member_id=mem.id, company_id=company_id)
                for ii in duration:
                    sum_duration = sum_duration + ii.durationsec()
            # new_dict['duration'] = compute_duration(sum_duration)
            new_dict['value'] = sum_duration / 3600 
            all_member_tms.append(new_dict)
    else:
        all_member_tms = ''
    data = {
        'members': all_member_tms
    }
    return JsonResponse(data)


def filter_monthly_timesheets_by_date(request):
    company_id = request.session['company_id']
    department_id = request.session['department_id']

    new_current_month = request.GET.get('new_month')
    new_current_year = request.GET.get('new_year')
    first_day_of_month1 = request.GET.get('selected_date')

    cur_month = datetime.datetime.strptime(new_current_month, "%m").strftime("%m").lstrip('0')
    cur_year = datetime.datetime.strptime(new_current_year, "%Y").strftime("%Y").lstrip('0')

    last_day_of_month1 = last_day_of_month(int(cur_year), int(cur_month))

    startdate = datetime.datetime.strptime(str(first_day_of_month1), '%Y-%m-%d') 
    enddate = datetime.datetime.strptime(str(last_day_of_month1), '%Y-%m-%d') + datetime.timedelta(days=1)

    min_dt = datetime.datetime.combine(startdate, datetime.time.min)
    max_dt = datetime.datetime.combine(enddate, datetime.time.max)
    day_delta = timedelta(days=1) 


    dept_members_exist = User.objects.filter(company_id=company_id, department_id=department_id).exists()
    if dept_members_exist == True:
        dept_members = User.objects.filter(company_id=company_id, department_id=department_id)
        all_member_tms = []
        for mem in dept_members:
            sum_duration = 0
            new_dict = {}
            new_dict['label'] = mem.first_name + " " + (mem.last_name)[0]
            for i in range((enddate - startdate).days):
                duration = Timesheet.objects.filter(log_day=(startdate + i*day_delta), project_team_member_id=mem.id, company_id=company_id)
                for ii in duration:
                    sum_duration = sum_duration + ii.durationsec()
            new_dict['value'] = sum_duration / 3600 
            all_member_tms.append(new_dict)
    else:
        all_member_tms = ''
    data = {
        'members': all_member_tms
    }
    return JsonResponse(data)


def last_day_of_month(year, month):
    """ Work out the last day of the month """
    last_days = [31, 30, 29, 28, 27]
    for i in last_days:
        try:
            end = datetime.datetime(year, month, i)
        except ValueError:
            continue
        else:
            return end.date()
    return None


class PdfPrint():
    """returns pdf object"""
    def __init__(self, buffer, pageSize):
        self.buffer = buffer
        # default format is A4
        if pageSize == 'A4':
            self.pageSize = A4
        elif pageSize == 'Letter':
            self.pageSize = letter
        self.width, self.height = self.pageSize

    def report(self, data_table, title):
        # set some characteristics for pdf document
        doc = SimpleDocTemplate(
            self.buffer,
            rightMargin=72,
            leftMargin=72,
            topMargin=30,
            bottomMargin=72,
            pagesize=self.pageSize)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle( name="ParagraphTitle", fontSize=11, fontName="FreeSansBold"))

        table=Table(data_table)

        data = []
        data.append(Paragraph(title, styles['Title']))
        data.append(table)

        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('ALIGN',(0,0), (-1,-1),'CENTER'),

            ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BACKGROUND',(0,1), (-1,-1), colors.beige),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('BOX',(0,0), (-1,-1),0.5, colors.black),
            ('GRID', (0,0), ( -1,-1), 0.25, colors.black),
        ])
        table.setStyle(style)

        # create other flowables
        doc.build(data)
        pdf = self.buffer.getvalue()
        self.buffer.close()
        return pdf


# export pdf for staff utilization
def export_pdf_utilization(request):
    if request.method == 'POST':
        start_time = request.POST.get('start_pdf')
        end_time = request.POST.get("end_pdf")
        print(f"{start_time} {end_time} are the dates")
        
        convert_start = datetime.datetime.strptime(start_time, "%d-%m-%Y").strftime("%Y-%m-%d")
        convert_end = datetime.datetime.strptime(end_time, "%d-%m-%Y").strftime("%Y-%m-%d")

        new_start = datetime.datetime.strptime(convert_start, "%Y-%m-%d")
        new_end = datetime.datetime.strptime(convert_end, "%Y-%m-%d")

        start = date(new_start.year, new_start.month, new_start.day)
        end = date(new_end.year, new_end.month, new_end.day)
        
        # getting the days in between start date and end date
        delta = end - start

        all_members = [] 
        
        users = User.objects.all()
        day_list = []

        for j in range(delta.days + 1):
            day = start + timedelta(days=j)
            new_day = day.strftime("%Y-%m-%d")

            strip_date = datetime.datetime.strptime(new_day, "%Y-%m-%d")
            split_date = date(strip_date.year, strip_date.month, strip_date.day);
            date_index = split_date.weekday()
            cal = calendar.day_name[date_index]
            
            if cal == 'Saturday' or cal == 'Sunday':
                pass
            else:
                day_list.append(new_day)

        expected_hours = len(day_list)
        counter = 0
        for user in users:
            sum_timesheet = 0
            counter += 1
            timesheet_dict = {}
            timesheet_dict['id'] = counter
            timesheet_dict["name"] = user.first_name + " " + user.last_name

            
            for i in range(delta.days+1):
                day = start + timedelta(days=i)
                new_day = day.strftime("%Y-%m-%d") 
                strip_date = datetime.datetime.strptime(new_day, "%Y-%m-%d")
                split_date = date(strip_date.year, strip_date.month, strip_date.day);
                date_index = split_date.weekday()
                cal = calendar.day_name[date_index]
                
                if cal == 'Saturday' or cal == 'Sunday':
                    pass
                else:
                    timesheet = Timesheet.objects.filter(log_day=new_day, added_by=user.id)
                    for time in timesheet:
                        sum_timesheet = sum_timesheet + time.durationsec()
                        
            timesheet_dict['timesheet_hours'] = sum_timesheet /3600 
            timesheet_dict['available_hours']  = expected_hours * 8.5
            availability = timesheet_dict['timesheet_hours']/timesheet_dict['available_hours']
            percent = '%'
            timesheet_dict['timesheet/available'] = str(round(availability, 2)) + percent
            all_members.append(timesheet_dict)

        # print(f"{all_members} are all memebers")

        response = HttpResponse(content_type='application/pdf')
        today = date.today()
        filename = 'StaffUtilization' + today.strftime('%Y-%m-%d')
        response['Content-Disposition'] = 'attachement; filename={0}.pdf'.format(filename)

        buffer = BytesIO()
        report = PdfPrint(buffer, 'Letter')

        list_details = [['ID', 'NAME', 'Timesheet Hrs', 'Available Hrs', 'Timesheet/Available(%)']]
        
        for member in all_members:
            list_values = [m for m in member.values()]
            list_details.append(list_values)

        print(list_details)

        title = "Staff Utilization Report from {} to {}".format(start_time, end_time)

        pdf = report.report(list_details, title)
        
        response.write(pdf)
        return response


def task_report_page(request):
    """generate task utilization report"""

    user_id = request.user.id
    company_id = request.session['company_id']
    department_id = request.session['department_id']
    statuses = Status.objects.all()
    dept_users = User.objects.filter(Q(department_id=int(department_id)), ~Q(id = int(user_id)))
    

    return render(request, 'project_management/task_report.html',{
        "statuses": statuses,
        "dept_users": dept_users,
        'user_id' : user_id,
        'user_name' : User.objects.get(id=int(user_id))
    })


def export_task_report(request):
    """exporting task_report"""
    if request.method == 'POST':
        start_time = request.POST.get('start')
        end_time = request.POST.get("end")
        status_two = request.POST.get("statusTwo")
        selected_member = request.POST.get("allUsers")

        original_user = ""

        company_id = request.session['company_id']
        department_id = request.session['department_id']
        status = ""

        company = Company.objects.get(id=company_id)

        convert_start = datetime.datetime.strptime(start_time, "%d-%m-%Y").strftime("%Y-%m-%d")
        convert_end = datetime.datetime.strptime(end_time, "%d-%m-%Y").strftime("%Y-%m-%d")

        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename=Task_Report_Status.xls'
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet("Task Completion Report")

        new_start = datetime.datetime.strptime(convert_start, "%Y-%m-%d")
        new_end = datetime.datetime.strptime(convert_end, "%Y-%m-%d")

        start = date(new_start.year, new_start.month, new_start.day)
        end = date(new_end.year, new_end.month, new_end.day)
        
        # getting the days in between start date and end date
        delta = end - start

        all_tasks = [] 

        for j in range(delta.days + 1):
            day = start + timedelta(days=j)
            new_day = day.strftime("%Y-%m-%d")

            if status_two != "all":
                status = Status.objects.get(id=int(status_two))
                tasks_exists = Task.objects.filter(start_date=new_day, status=status).exists()
                if tasks_exists:
                    tasks = Task.objects.filter(start_date=new_day, status=status)
                    
                    for task in tasks:   
                        all_tasks.append(task)
                
            else:
                tasks_exists = Task.objects.filter(start_date=new_day).exists()
                if tasks_exists:
                    tasks = Task.objects.filter(start_date=new_day)
                    
                    for task in tasks:   
                        all_tasks.append(task)
        
        new_list = []
        count = 0
        date_obj = ""

        assigned = []

        department = Department.objects.get(id=department_id, company=company)

        for task in all_tasks:

            assigned_id = task.assigned_to.all()
            
            for sign in assigned_id:

                my_new_tasks = {}
                my_new_tasks['name'] = task.name
                my_new_tasks["project"] = task.project.name
                my_new_tasks['milestone'] = task.milestone.name
                my_new_tasks["status"] = task.status.name
                my_new_tasks["description"] = task.description
                my_new_tasks["start_date"] = task.start_date
                my_new_tasks["end_date"] = task.end_date
                my_new_tasks["created_time"] = task.created_time

                my_new_tasks["task_age"] = task.aging()

                team = ProjectTeam.objects.get(project_id= task.project.id)
                
                project_member = ProjectTeamMember.objects.get(id=sign.id, project_team=team)
                user_id = project_member.member_id

                user = User.objects.get(id=user_id)

                my_new_tasks["assigned_to"] = user.first_name +" "+ user.last_name

                my_new_tasks["department"] = user.department.name

                my_new_tasks["user_id"] = user.id
                
                new_list.append(my_new_tasks)
        
        print_list = []
        
        for val in new_list:
            # selecting for all members
            if selected_member == "all":
                if val["department"] == department.name:
                    print_list.append(val)
            
            #selecting for a specific member 
            else:
                original_user = int(selected_member)

                if val["department"] == department.name and original_user == val["user_id"]:
                    print_list.append(val)
                
        for obj in print_list:
            if obj["start_date"] == None:
                obj.update(start_date="Not set")
            else:
                start_year = obj['start_date'].year
                start_month = obj['start_date'].month
                start_day = obj['start_date'].day

                new_start_month = append_zero(start_month)
                new_start_day = append_zero(start_day)
                new_start = str(start_year)+"-"+str(new_start_month)+"-"+str(new_start_day)

                obj.update(start_date=new_start)

            if obj["end_date"] == None:
                obj.update(end_date="Not set")
            else:
                end_year = obj['end_date'].year
                end_month = obj['end_date'].month
                end_day = obj['end_date'].day

                new_end_month = append_zero(end_month)
                new_end_day = append_zero(end_day)
                new_end = str(end_year)+"-"+str(new_end_month)+"-"+str(new_end_day)
                
                # updating dictionary value
                obj.update(end_date=new_end)

        # exporting to excel

        row_num = 0

        columns = [(u"TaskName", 5000), (u"Project", 5000), (u"Milestone", 5000), 
            (u"Status", 5000), (u"Description", 5000),  (u"Start Date(yy/mm/dd)", 5000), (u"Enddate(yy/mm/dd)", 5000),
            (u"Created At", 5000), (u"Assigned_To", 5000), (u"Department", 5000), (u"Task Age", 5000), 
        ]

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num][0], font_style)
            # set column width
            ws.col(col_num).width = columns[col_num][1]

        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1
        
        for obj in print_list:
            
            row_num += 1

            row = [
                obj["name"],
                obj["project"],
                obj["milestone"],
                obj["status"],
                obj["description"],
                obj["start_date"],
                obj["end_date"],
                obj["created_time"],
                obj["assigned_to"],
                obj["department"],
                obj["task_age"],
            ]

            for col_num in range(len(row)):
                ws.write(row_num, col_num, str(row[col_num]), font_style)
                
        wb.save(response)
        return response


def preview_task_report(request):
    """exporting task_report"""
    if request.method == 'POST':
        start_time = request.POST.get('startdate')
        end_time = request.POST.get("enddate")
        status_two = request.POST.get("status")
        selected_member = request.POST.get("users")

        original_user = ""

        company_id = request.session['company_id']
        department_id = request.session['department_id']
        status = ""

        company = Company.objects.get(id=company_id)

        convert_start = datetime.datetime.strptime(start_time, "%d-%m-%Y").strftime("%Y-%m-%d")
        convert_end = datetime.datetime.strptime(end_time, "%d-%m-%Y").strftime("%Y-%m-%d")

        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename=Task_Report_Status.xls'
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet("Task Completion Report")

        new_start = datetime.datetime.strptime(convert_start, "%Y-%m-%d")
        new_end = datetime.datetime.strptime(convert_end, "%Y-%m-%d")

        start = date(new_start.year, new_start.month, new_start.day)
        end = date(new_end.year, new_end.month, new_end.day)
        
        # getting the days in between start date and end date
        delta = end - start

        all_tasks = [] 

        for j in range(delta.days + 1):
            day = start + timedelta(days=j)
            new_day = day.strftime("%Y-%m-%d")

            if status_two != "all":
                status = Status.objects.get(id=int(status_two))
                tasks_exists = Task.objects.filter(start_date=new_day, status=status).exists()
                if tasks_exists:
                    tasks = Task.objects.filter(start_date=new_day, status=status)
                    
                    for task in tasks:   
                        all_tasks.append(task)
                
            else:
                tasks_exists = Task.objects.filter(start_date=new_day).exists()
                if tasks_exists:
                    tasks = Task.objects.filter(start_date=new_day)
                    
                    for task in tasks:   
                        all_tasks.append(task)
        
        new_list = []
        count = 0
        date_obj = ""

        assigned = []

        department = Department.objects.get(id=department_id, company=company)

        for task in all_tasks:

            assigned_id = task.assigned_to.all()
            
            for sign in assigned_id:

                my_new_tasks = {}
                my_new_tasks['name'] = task.name
                my_new_tasks["project"] = task.project.name
                my_new_tasks['milestone'] = task.milestone.name
                my_new_tasks["status"] = task.status.name
                my_new_tasks["description"] = task.description
                my_new_tasks["start_date"] = task.start_date
                my_new_tasks["end_date"] = task.end_date
                my_new_tasks["created_time"] = task.created_time

                my_new_tasks["task_age"] = task.aging()

                team = ProjectTeam.objects.get(project_id= task.project.id)
                
                project_member = ProjectTeamMember.objects.get(id=sign.id, project_team=team)
                user_id = project_member.member_id

                user = User.objects.get(id=user_id)

                my_new_tasks["assigned_to"] = user.first_name +" "+ user.last_name

                my_new_tasks["department"] = user.department.name

                my_new_tasks["user_id"] = user.id
                
                new_list.append(my_new_tasks)
        
        print_list = []
        
        for val in new_list:
            # selecting for all members
            if selected_member == "all":
                if val["department"] == department.name:
                    print_list.append(val)
            
            #selecting for a specific member 
            else:
                original_user = int(selected_member)

                if val["department"] == department.name and original_user == val["user_id"]:
                    print_list.append(val)
                
        for obj in print_list:
            if obj["start_date"] == None:
                obj.update(start_date="Not set")
            else:
                start_year = obj['start_date'].year
                start_month = obj['start_date'].month
                start_day = obj['start_date'].day

                new_start_month = append_zero(start_month)
                new_start_day = append_zero(start_day)
                new_start = str(start_year)+"-"+str(new_start_month)+"-"+str(new_start_day)

                obj.update(start_date=new_start)

            if obj["end_date"] == None:
                obj.update(end_date="Not set")
            else:
                end_year = obj['end_date'].year
                end_month = obj['end_date'].month
                end_day = obj['end_date'].day

                new_end_month = append_zero(end_month)
                new_end_day = append_zero(end_day)
                new_end = str(end_year)+"-"+str(new_end_month)+"-"+str(new_end_day)
                
                # updating dictionary value
                obj.update(end_date=new_end)
        
        return render(request, 'project_management/task_report.html',{
            "tasks": print_list
        })


def append_zero(number):
    """function to append zero to number"""
    if number < 10:
        new_str = "0" +str(number)
        return new_str
    else:
        return number


def customer_request_home(request):
    department_id = request.session['department_id']
    template = loader.get_template('project_management/customer_request_pane.html')
    
    # newly created requests
    open_req_list = CustomerRequest.objects.filter(client_request_status="OPEN", department_id=department_id)
    
    # assigned requests to enginners but not yet resolved
    pending_reg_list = CustomerRequest.objects.filter(client_request_status='PENDING', department_id=department_id)

    # resolved CRs
    completed_reg_list = CustomerRequest.objects.filter(client_request_status='COMPLETED', department_id=department_id)

    cancelled_reg_list = CustomerRequest.objects.filter(client_request_status='CANCELED', department_id=department_id)
    onhold_reg_list = CustomerRequest.objects.filter(client_request_status='ONHOLD', department_id=department_id)

    context = {
        'open_req_list': open_req_list,
        'pending_reg_list': pending_reg_list,
        'completed_reg_list': completed_reg_list,
        'cancelled_reg_list': cancelled_reg_list,
        'onhold_reg_list': onhold_reg_list
    }
    
    return HttpResponse(template.render(context, request))

def search_customerrequests(request):
    dataToggle = request.GET.get('dataToggle')
    user_id = request.user.id
    department_id = request.session['department_id']
    search_value = request.GET.get('searchValue')

    if dataToggle == 'true':
        template = loader.get_template('project_management/list_customer_requests.html')
        
        open_req_list = CustomerRequest.objects.filter(Q(name__icontains=search_value), Q(client_request_status="OPEN"), Q(department_id=department_id))
        pending_reg_list = CustomerRequest.objects.filter(Q(name__icontains=search_value), Q(client_request_status='PENDING'), Q(department_id=department_id))
        completed_reg_list = CustomerRequest.objects.filter(Q(name__icontains=search_value), Q(client_request_status='COMPLETED'), Q(department_id=department_id))
        cancelled_reg_list = CustomerRequest.objects.filter(Q(name__icontains=search_value), Q(client_request_status='CANCELED'), Q(department_id=department_id))
        onhold_reg_list = CustomerRequest.objects.filter(Q(name__icontains=search_value), Q(client_request_status='ONHOLD'), Q(department_id=department_id))

        context = {
            'open_req_list': open_req_list,
            'pending_reg_list': pending_reg_list,
            'completed_reg_list': completed_reg_list,
            'cancelled_reg_list': cancelled_reg_list,
            'onhold_reg_list': onhold_reg_list
        }
    if dataToggle == 'false':
        template = loader.get_template('project_management/list_your_customer_requests.html')

        open_req_list = CustomerRequest.objects.filter(Q(name__icontains=search_value), Q(client_request_status="OPEN"), Q(creator_id=user_id, department_id=department_id))
        pending_reg_list = CustomerRequest.objects.filter(Q(name__icontains=search_value), Q(client_request_status='PENDING'), Q(assigned_member=user_id), Q(department_id=department_id))
        completed_reg_list = CustomerRequest.objects.filter(Q(name__icontains=search_value), Q(client_request_status='COMPLETED'), Q(trackstatus__request_status="COMPLETED"), Q(trackstatus__added_by_id=user_id), Q(department_id=department_id))
        cancelled_reg_list = CustomerRequest.objects.filter(Q(name__icontains=search_value), Q(client_request_status='CANCELED'), Q(trackstatus__request_status="CANCELED"), Q(trackstatus__added_by_id=user_id), Q(department_id=department_id))
        onhold_reg_list = CustomerRequest.objects.filter(Q(name__icontains=search_value), Q(client_request_status='ONHOLD'), Q(trackstatus__request_status="ONHOLD"), Q(trackstatus__added_by_id=user_id), Q(department_id=department_id))

        context = {
            'open_req_list': open_req_list,
            'pending_reg_list': pending_reg_list,
            'completed_reg_list': completed_reg_list,
            'cancelled_reg_list': cancelled_reg_list,
            'onhold_reg_list': onhold_reg_list,
        }

    return HttpResponse(template.render(context, request))

def customer_request_set_data(request):
    department_id = request.session['department_id']
    cr_data = []
    open_req_list = CustomerRequest.objects.filter(client_request_status="OPEN", department_id=department_id).count()
    pending_reg_list = CustomerRequest.objects.filter(client_request_status='PENDING', department_id=department_id).count()
    completed_reg_list = CustomerRequest.objects.filter(client_request_status='COMPLETED', department_id=department_id).count()
    cancelled_reg_list = CustomerRequest.objects.filter(client_request_status='CANCELED', department_id=department_id).count()
    onhold_reg_list = CustomerRequest.objects.filter(client_request_status='ONHOLD', department_id=department_id).count()
    cr_data.append(open_req_list)
    cr_data.append(pending_reg_list)
    cr_data.append(completed_reg_list)
    cr_data.append(cancelled_reg_list)
    cr_data.append(onhold_reg_list)

    data = {
        'cr_data': cr_data
    }
    return JsonResponse(data)


def customer_requests_reports_home(request):
    template = loader.get_template('project_management/customer_request_reports_pane.html')

    
    context = {
       
    }
    
    return HttpResponse(template.render(context, request))


def manage_customer_request_pane(request):
    cr_id = request.GET.get('cr_id')
    template = loader.get_template('project_management/manage_customer_request.html')
    get_customer_req_obj = CustomerRequest.objects.get(id=int(cr_id))
    context = {
       "request": get_customer_req_obj
    }
    
    return HttpResponse(template.render(context, request))


def change_customer_request_state(request):
    cr_id = request.GET.get('cr_id')
    cr_name = request.GET.get('cr_name')
    template = loader.get_template('project_management/change_customer_request_state.html')
    context = {
       "cr_id": cr_id,
       "cr_name": cr_name,
    }
    
    return HttpResponse(template.render(context, request))


def add_customer_request_activity(request):
    req_name = request.GET.get('cr_name')
    cr_id = request.GET.get('cr_id')
    cr_code = request.GET.get('cr_code')

    template = loader.get_template('project_management/add_customer_request_activity.html')
    context = {

    }
    context = {
       "cr_name": req_name,
       "cr_id": cr_id,
       "cr_code": cr_code
    }
    return HttpResponse(template.render(context, request))


def save_customer_request_activity(request):
    cr_name = request.GET.get('cr_name')
    cr_code = request.GET.get('cr_code')
    company_id = request.session['company_id']

    id_log_day = request.GET.get('id_log_day')
    activity_name = request.GET.get('activity_name')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    activity_desc = request.GET.get('activity_desc')
    cr_id = int(request.GET.get('cr_id'))
    user_id = request.user.id

    log_day = datetime.datetime.strptime(id_log_day, '%d-%m-%Y')
    start_time1 = datetime.datetime.strptime(start_time, '%I:%M %p')
    end_time1 =   datetime.datetime.strptime(end_time, '%I:%M %p')

    obj = CustomerRequestActivity(name=activity_name, customerrequest_id=cr_id, activity_date=log_day, start_time=start_time1, end_time=end_time1, description=activity_desc, added_by_id=user_id, datetime_added=datetime.date.today())
    obj.save()

    # save timesheet activity
    obj2 = Timesheet(log_day=log_day, start_time=start_time1, end_time=end_time1, added_by_id=user_id, project_team_member_id=user_id, company_id=int(company_id), last_updated_date=datetime.date.today(), last_updated_by_id=user_id, notes=activity_desc, timesheet_category="REQUEST")
    obj2.save()

    new_timesheet_id2 = obj2.id
    if new_timesheet_id2 != "":
        RequestTimesheetExtend.objects.create(timesheet_id=new_timesheet_id2, customer_request_id=int(cr_id))

    # to add a customer request activity, you must be an assigned member
    check_if_assigned_member = CustomerRequestTeamMembers.objects.filter(customerrequest_id=int(cr_id), assigned_member_id=user_id).exists()

    cr_activities = CustomerRequestActivity.objects.filter(customerrequest_id=int(cr_id))
    template = loader.get_template('project_management/customer_request_activities_pane.html')
    context = {
       "cr_name": cr_name,
       "cr_id": cr_id,
       "cr_code": cr_code,
       "cr_activities": cr_activities,
       "check_if_assigned_member": check_if_assigned_member
    }

    return HttpResponse(template.render(context, request))


def load_customer_request_activities(request):
    req_name = request.GET.get('req_name')
    cr_id = request.GET.get('cr_id')
    cr_code = request.GET.get('cr_code')
    user_id = request.user.id

    # to add a customer request activity, you must be an assigned member
    check_if_assigned_member = CustomerRequestTeamMembers.objects.filter(customerrequest_id=int(cr_id), assigned_member_id=user_id).exists()

    cr_activities = CustomerRequestActivity.objects.filter(customerrequest_id=int(cr_id))
    template = loader.get_template('project_management/customer_request_activities_pane.html')
    context = {
       "cr_name": req_name,
       "cr_id": cr_id,
       "cr_code": cr_code,
       "cr_activities": cr_activities,
       "check_if_assigned_member": check_if_assigned_member
    }
    
    return HttpResponse(template.render(context, request))


def load_customer_request_team_members(request):
    req_name = request.GET.get('req_name')
    cr_id = request.GET.get('cr_id')
    cr_code = request.GET.get('cr_code')
    user_id = request.user.id

    # to add a customer request team member, you must be an assigned member
    check_if_assigned_member = CustomerRequestTeamMembers.objects.filter(customerrequest_id=int(cr_id), assigned_member_id=user_id).exists()

    cr_team = CustomerRequestTeamMembers.objects.filter(customerrequest_id=int(cr_id))
    template = loader.get_template('project_management/customer_request_team_members.html')
    context = {
       "cr_name": req_name,
       "cr_id": cr_id,
       "cr_code": cr_code,
       "cr_members": cr_team,
       "check_if_assigned_member": check_if_assigned_member
    }
    
    return HttpResponse(template.render(context, request))


def save_update_customer_request_state(request):
    cr_status = request.GET.get('cr_status')
    cr_id = request.GET.get('cr_id')
    user_id = request.user.id
    department_id = request.session['department_id']

    Trackstatus.objects.create(customerrequest_id=int(cr_id), request_status=cr_status, added_by_id=user_id)

    CustomerRequest.objects.filter(pk=int(cr_id)).update(modified_time=datetime.date.today(), client_request_status=cr_status, status=cr_status)
    
    template = loader.get_template('project_management/list_customer_requests.html')
    
    open_req_list = CustomerRequest.objects.filter(client_request_status="OPEN", department_id=department_id)
    pending_reg_list = CustomerRequest.objects.filter(client_request_status='PENDING', department_id=department_id)
    completed_reg_list = CustomerRequest.objects.filter(client_request_status='COMPLETED', department_id=department_id)
    cancelled_reg_list = CustomerRequest.objects.filter(client_request_status='CANCELED', department_id=department_id)
    onhold_reg_list = CustomerRequest.objects.filter(client_request_status='ONHOLD', department_id=department_id)

    context = {
        'open_req_list': open_req_list,
        'pending_reg_list': pending_reg_list,
        'completed_reg_list': completed_reg_list,
        'cancelled_reg_list': cancelled_reg_list,
        'onhold_reg_list': onhold_reg_list
    }
    
    return HttpResponse(template.render(context, request))



# CUSTOMER PROJECT VIEWS
def list_customer_projects(request):
    """list users under customer company"""
    company_id = request.GET.get('company_id')
    
    template = loader.get_template('project_management/list_customer_projects.html')

    project_list = []
    company = Company.objects.get(id=int(company_id))
    projects =Project.company.through.objects.filter(company_id=int(company_id))
    
    for project in projects:
        project_list.append(project.project_id)

    new_list = []

    for project_id in project_list:
        new_project = Project.objects.filter(id=project_id)

        for val in new_project:
            new_list.append(val)

    return HttpResponse(template.render({}, request))


def add_customer_projects(request):
    company_id = request.GET.get('company_id')
    company_name = request.GET.get('company_name')
    
    template = loader.get_template('project_management/add_customer_projects.html')
    context = {
        'company_id': company_id,
        'company_name': company_name,
    }

    return HttpResponse(template.render(context, request))


class AddCustomerRequest(CreateView):
    model = CustomerRequest
    fields = ['name', 'ticket_code','description', 'priority', 'sla', 'status', 'issue_type']

    template_name = 'project_management/add_customer_request.html'
    success_url = reverse_lazy('customerRequests')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.request.session['company_id']
        
        # Setting Ticket Code Sequency
        cr_count = CustomerRequest.objects.all().count()            
        cr_number = cr_count + 1

        test_string = str(cr_number)

        # only pick short year
        current_year_short = datetime.datetime.now().strftime('%y')
        str_date = str(current_year_short)
        
        result = ""
        final_result_code = ""

        # set code format
        code = "CR"

        if len(test_string) ==  1:
            N=2
            result = test_string.zfill(N + len(test_string)) 
            final_result_code = code + "-" + str_date + "-" + result
        elif len(test_string) == 2:
            N=1
            result = test_string.zfill(N + len(test_string)) 
            final_result_code = code + "-"  + str_date + "-" + result
        else:
            result = test_string
            final_result_code = code + "-"  + str_date + "-" + result

        # SHOULD FILTER BY SESSION CUTOMERS so that we see slas for only that customer
        context['customer_sla_list'] = ServiceLevelAgreement.objects.filter(company=company_id)
        context['ticket_code'] = final_result_code
        return context


def save_customer_request(request):
    dataToggle = request.GET.get('dataToggle')
    request_name = request.GET.get('request_name')
    id_description = request.GET.get('id_description')
    id_ticket_code = request.GET.get('id_ticket_code')
    id_customer_sla = int(request.GET.get('id_customer_sla'))
    id_priority = int(request.GET.get('id_priority'))
    id_issue_type = int(request.GET.get('id_issue_type'))
    user_id = request.user.id
    department_id = request.session['department_id']

    obj = CustomerRequest(name=request_name, ticket_code=id_ticket_code, description=id_description, priority_id=id_priority, sla_id=id_customer_sla, creator_id=user_id, created_time=datetime.date.today(), modified_time=datetime.date.today(), client_request_status='OPEN', issue_type_id=id_issue_type, department_id=department_id)
    obj.save()

    customer_req_id = obj.id
    if customer_req_id != "":
        Trackstatus.objects.create(customerrequest_id=customer_req_id, request_status="OPEN", added_by_id=user_id)
    if dataToggle == 'true':
        template = loader.get_template('project_management/list_customer_requests.html')
        
        open_req_list = CustomerRequest.objects.filter(client_request_status="OPEN", department_id=department_id)
        pending_reg_list = CustomerRequest.objects.filter(client_request_status='PENDING', department_id=department_id)
        completed_reg_list = CustomerRequest.objects.filter(client_request_status='COMPLETED', department_id=department_id)
        cancelled_reg_list = CustomerRequest.objects.filter(client_request_status='CANCELED', department_id=department_id)
        onhold_reg_list = CustomerRequest.objects.filter(client_request_status='ONHOLD', department_id=department_id)

        context = {
            'open_req_list': open_req_list,
            'pending_reg_list': pending_reg_list,
            'completed_reg_list': completed_reg_list,
            'cancelled_reg_list': cancelled_reg_list,
            'onhold_reg_list': onhold_reg_list
        }
    if dataToggle == 'false':
        template = loader.get_template('project_management/list_your_customer_requests.html')

        open_req_list = CustomerRequest.objects.filter(client_request_status="OPEN", creator_id=user_id, department_id=department_id)
        pending_reg_list = CustomerRequest.objects.filter(client_request_status='PENDING', assigned_member=user_id, department_id=department_id)
        completed_reg_list = CustomerRequest.objects.filter(client_request_status='COMPLETED', trackstatus__request_status="COMPLETED", trackstatus__added_by_id=user_id, department_id=department_id)
        cancelled_reg_list = CustomerRequest.objects.filter(client_request_status='CANCELED', trackstatus__request_status="CANCELED", trackstatus__added_by_id=user_id, department_id=department_id)
        onhold_reg_list = CustomerRequest.objects.filter(client_request_status='ONHOLD', trackstatus__request_status="ONHOLD", trackstatus__added_by_id=user_id, department_id=department_id)

        context = {
            'open_req_list': open_req_list,
            'pending_reg_list': pending_reg_list,
            'completed_reg_list': completed_reg_list,
            'cancelled_reg_list': cancelled_reg_list,
            'onhold_reg_list': onhold_reg_list
        }

    return HttpResponse(template.render(context, request))


class UpdateCustomerRequest(UpdateView):
    model = CustomerRequest
    fields = ['name', 'ticket_code','description', 'priority', 'sla', 'status', 'issue_type']
    template_name = 'project_management/update_customer_request.html'
    success_url = reverse_lazy('customerRequests')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_id = self.kwargs['pk']
        context['request_id'] = request_id

        sla_id = self.request.GET['sla_id']
        sla_name = self.request.GET['sla_name']
        context['sla_id'] = sla_id
        context['sla_name'] = sla_name
        
        prev_status = self.request.GET['status']
        context['customer_sla_list'] = ServiceLevelAgreement.objects.filter(~Q(id = int(sla_id)))
        context['prev_status'] = prev_status
        return context


def save_customer_request_update(request):
    request_id = request.GET.get('request_id')
    request_name = request.GET.get('request_name')
    id_description = request.GET.get('id_description')
    id_ticket_code = request.GET.get('id_ticket_code')
    id_customer_sla = int(request.GET.get('id_customer_sla'))
    id_priority = int(request.GET.get('id_priority'))
    id_issue_type = int(request.GET.get('id_issue_type'))
    prev_status = request.GET.get('prev_status')
    department_id = request.session['department_id']

    user_id = request.user.id
    cr_status = request.GET.get('id_status')

    if cr_status != prev_status:
        Trackstatus.objects.create(customerrequest_id=int(request_id), request_status=cr_status, added_by_id=user_id)

    CustomerRequest.objects.filter(pk=int(request_id)).update(name=request_name, ticket_code=id_ticket_code, description=id_description, priority_id=id_priority, sla_id=id_customer_sla, modified_time=datetime.date.today(), client_request_status=cr_status, issue_type_id=id_issue_type, status=cr_status)
    
    template = loader.get_template('project_management/list_customer_requests.html')
    
    open_req_list = CustomerRequest.objects.filter(client_request_status="OPEN", department_id=department_id)
    pending_reg_list = CustomerRequest.objects.filter(client_request_status='PENDING', department_id=department_id)
    completed_reg_list = CustomerRequest.objects.filter(client_request_status='COMPLETED', department_id=department_id)
    cancelled_reg_list = CustomerRequest.objects.filter(client_request_status='CANCELED', department_id=department_id)
    onhold_reg_list = CustomerRequest.objects.filter(client_request_status='ONHOLD', department_id=department_id)

    context = {
        'open_req_list': open_req_list,
        'pending_reg_list': pending_reg_list,
        'completed_reg_list': completed_reg_list,
        'cancelled_reg_list': cancelled_reg_list,
        'onhold_reg_list': onhold_reg_list
    }

    return HttpResponse(template.render(context, request))


def save_your_customer_request_update(request):
    request_id = request.GET.get('request_id')
    request_name = request.GET.get('request_name')
    id_description = request.GET.get('id_description')
    id_ticket_code = request.GET.get('id_ticket_code')
    id_customer_sla = int(request.GET.get('id_customer_sla'))
    id_priority = int(request.GET.get('id_priority'))
    id_issue_type = int(request.GET.get('id_issue_type'))
    prev_status = request.GET.get('prev_status')
    department_id = request.session['department_id']

    user_id = request.user.id
    cr_status = request.GET.get('id_status')

    if cr_status != prev_status:
        Trackstatus.objects.create(customerrequest_id=int(request_id), request_status=cr_status, added_by_id=user_id)

    CustomerRequest.objects.filter(pk=int(request_id)).update(name=request_name, ticket_code=id_ticket_code, description=id_description, priority_id=id_priority, sla_id=id_customer_sla, modified_time=datetime.date.today(), client_request_status=cr_status, issue_type_id=id_issue_type, status=cr_status)
    
    template = loader.get_template('project_management/list_your_customer_requests.html')
    
    open_req_list = CustomerRequest.objects.filter(client_request_status="OPEN", creator_id=user_id, department_id=department_id)
    pending_reg_list = CustomerRequest.objects.filter(client_request_status='PENDING', assigned_member=user_id, department_id=department_id)
    completed_reg_list = CustomerRequest.objects.filter(client_request_status='COMPLETED', trackstatus__request_status="COMPLETED", trackstatus__added_by_id=user_id, department_id=department_id)
    cancelled_reg_list = CustomerRequest.objects.filter(client_request_status='CANCELED', trackstatus__request_status="CANCELED", trackstatus__added_by_id=user_id, department_id=department_id)
    onhold_reg_list = CustomerRequest.objects.filter(client_request_status='ONHOLD', trackstatus__request_status="ONHOLD", trackstatus__added_by_id=user_id, department_id=department_id)

    context = {
        'open_req_list': open_req_list,
        'pending_reg_list': pending_reg_list,
        'completed_reg_list': completed_reg_list,
        'cancelled_reg_list': cancelled_reg_list,
        'onhold_reg_list': onhold_reg_list
    }

    return HttpResponse(template.render(context, request))
    

class ViewCustomerRequest(DetailView):
    model = CustomerRequest
    context_object_name = 'request'
    template_name = 'project_management/view_customer_request.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        req_desc = self.get_object().description
        if  req_desc.strip() is not "":
            context['desc'] = 1
        else: 
            context['desc'] = 0
        return context


def delete_customer_request(request):
    req_id = request.GET.get('req_id')
    dataToggle = request.GET.get('dataToggle')
    department_id = request.session['department_id']
    user_id = request.user.id
    
    Trackstatus.objects.filter(customerrequest_id=int(req_id)).delete()
    CustomerRequest.objects.filter(id=int(req_id)).delete()

    if dataToggle == 'true':
        template = loader.get_template('project_management/list_customer_requests.html')
    
        open_req_list = CustomerRequest.objects.filter(client_request_status="OPEN", department_id=department_id)
        pending_reg_list = CustomerRequest.objects.filter(client_request_status='PENDING', department_id=department_id)
        completed_reg_list = CustomerRequest.objects.filter(client_request_status='COMPLETED', department_id=department_id)
        cancelled_reg_list = CustomerRequest.objects.filter(client_request_status='CANCELED', department_id=department_id)
        onhold_reg_list = CustomerRequest.objects.filter(client_request_status='ONHOLD', department_id=department_id)

        context = {
            'open_req_list': open_req_list,
            'pending_reg_list': pending_reg_list,
            'completed_reg_list': completed_reg_list,
            'cancelled_reg_list': cancelled_reg_list,
            'onhold_reg_list': onhold_reg_list
        }
    if dataToggle == 'false':
        template = loader.get_template('project_management/list_your_customer_requests.html')

        open_req_list = CustomerRequest.objects.filter(client_request_status="OPEN", creator_id=user_id, department_id=department_id)
        pending_reg_list = CustomerRequest.objects.filter(client_request_status='PENDING', assigned_member=user_id, department_id=department_id)
        completed_reg_list = CustomerRequest.objects.filter(client_request_status='COMPLETED', trackstatus__request_status="COMPLETED", trackstatus__added_by_id=user_id, department_id=department_id)
        cancelled_reg_list = CustomerRequest.objects.filter(client_request_status='CANCELED', trackstatus__request_status="CANCELED", trackstatus__added_by_id=user_id, department_id=department_id)
        onhold_reg_list = CustomerRequest.objects.filter(client_request_status='ONHOLD', trackstatus__request_status="ONHOLD", trackstatus__added_by_id=user_id, department_id=department_id)

        context = {
            'open_req_list': open_req_list,
            'pending_reg_list': pending_reg_list,
            'completed_reg_list': completed_reg_list,
            'cancelled_reg_list': cancelled_reg_list,
            'onhold_reg_list': onhold_reg_list
        }
    
    return HttpResponse(template.render(context, request))


def customer_request_reload(request):
    template = loader.get_template('project_management/list_customer_requests.html')
    department_id = request.session['department_id']

    open_req_list = CustomerRequest.objects.filter(client_request_status="OPEN", department_id=department_id)
    pending_reg_list = CustomerRequest.objects.filter(client_request_status='PENDING', department_id=department_id)
    completed_reg_list = CustomerRequest.objects.filter(client_request_status='COMPLETED', department_id=department_id)
    cancelled_reg_list = CustomerRequest.objects.filter(client_request_status='CANCELED', department_id=department_id)
    onhold_reg_list = CustomerRequest.objects.filter(client_request_status='ONHOLD', department_id=department_id)

    context = {
        'open_req_list': open_req_list,
        'pending_reg_list': pending_reg_list,
        'completed_reg_list': completed_reg_list,
        'cancelled_reg_list': cancelled_reg_list,
        'onhold_reg_list': onhold_reg_list
    }

    return HttpResponse(template.render(context, request))


def customer_request_load_your_requests(request):
    template = loader.get_template('project_management/list_your_customer_requests.html')
    user_id = request.user.id
    department_id = request.session['department_id']
    
    open_req_list = CustomerRequest.objects.filter(client_request_status="OPEN", creator_id=user_id, department_id=department_id)
    pending_reg_list = CustomerRequest.objects.filter(client_request_status='PENDING', assigned_member=user_id, department_id=department_id)
    completed_reg_list = CustomerRequest.objects.filter(client_request_status='COMPLETED', trackstatus__request_status="COMPLETED", trackstatus__added_by_id=user_id, department_id=department_id)
    cancelled_reg_list = CustomerRequest.objects.filter(client_request_status='CANCELED', trackstatus__request_status="CANCELED", trackstatus__added_by_id=user_id, department_id=department_id)
    onhold_reg_list = CustomerRequest.objects.filter(client_request_status='ONHOLD', trackstatus__request_status="ONHOLD", trackstatus__added_by_id=user_id, department_id=department_id)

    context = {
        'open_req_list': open_req_list,
        'pending_reg_list': pending_reg_list,
        'completed_reg_list': completed_reg_list,
        'cancelled_reg_list': cancelled_reg_list,
        'onhold_reg_list': onhold_reg_list
    }

    return HttpResponse(template.render(context, request))


def delete_customer_request_engineer(request):
    assigned_id = request.GET.get('assigned_id')
    cr_id = request.GET.get('cr_id')
    cr_code = request.GET.get('cr_code')
    cr_name = request.GET.get('cr_name')
    user_id = request.user.id

    # to add a customer request team member, you must be an assigned member
    check_if_assigned_member = CustomerRequestTeamMembers.objects.filter(customerrequest_id=int(cr_id), assigned_member_id=user_id).exists()
    
    CustomerRequestTeamMembers.objects.filter(id=int(assigned_id)).delete()
    cr_team = CustomerRequestTeamMembers.objects.filter(customerrequest_id=int(cr_id))
    template = loader.get_template('project_management/customer_request_team_members.html')
    context = {
       "cr_name": cr_name,
       "cr_id": cr_id,
       "cr_code": cr_code,
       "cr_members": cr_team,
       "check_if_assigned_member": check_if_assigned_member
    }

    return HttpResponse(template.render(context, request))


def add_customer_request_member(request):
    cr_id = request.GET.get('cr_id')
    cr_code = request.GET.get('cr_code')
    cr_name = request.GET.get('cr_name')
    
    pendingTeam = []

    department_id = request.session['department_id']
    
    setAssigned = set()
    assiged_dept_users = CustomerRequestTeamMembers.objects.filter(customerrequest_id=int(cr_id)).values('assigned_member_id')
    for setA in assiged_dept_users:
        setAssigned.add(setA['assigned_member_id'])

    setAll = set()
    all_dept_users = User.objects.filter(department_id=department_id).values('id')
    for setb in all_dept_users:
        setAll.add(setb['id'])

    pending_team = setAll.difference(setAssigned)
    
    if len(pending_team) != 0:
        for tm in pending_team: 
            new_dict_pend = {}
            user_obj = User.objects.get(id=tm)
            new_dict_pend['id'] = user_obj.pk
            new_dict_pend['name'] = user_obj.first_name + ' ' + user_obj.last_name
            pendingTeam.append(new_dict_pend)

    template = loader.get_template('project_management/assign_member_to_customer_request.html')
    context = {
       "cr_name": cr_name,
       "cr_id": cr_id,
       "cr_code": cr_code,
       "members": pendingTeam,
    }

    return HttpResponse(template.render(context, request))

def issue_type_home(request):
    template = loader.get_template('project_management/issue_types_pane.html')

    issue_type_list = IssueType.objects.all()
    context = {
        'issue_type_list': issue_type_list,
    }
    
    return HttpResponse(template.render(context, request))


class UpdateIssueType(UpdateView):
    model = IssueType
    fields = ['name', 'description']
    template_name = 'project_management/update_issue_type.html'
    success_url = reverse_lazy('listIssueTypes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        iss_type_id = int(self.request.GET['iss_id'])
        context['iss_type_id'] = iss_type_id
        return context


class DeleteIssueType(DeleteView):
    model = IssueType
    success_url = reverse_lazy('listIssueTypes')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class AddIssueType(CreateView):
    model = IssueType
    fields = ['name', 'description']
    template_name = 'project_management/add_issue_type.html'
    success_url = reverse_lazy('listIssueTypes')


def validate_issuetype(request):
    issue_type_name = request.GET.get('name', None)
    data = {
        'is_taken': IssueType.objects.filter(name=issue_type_name).exists()
    }
    return JsonResponse(data)



def return_status(request):
    """
    populate status field with status
    """

    status = Status.objects.all()

    data = {
        'status': serializers.serialize("json", status)
    }

    return JsonResponse(data)


def save_project(request):
    # save project customer
    name = request.GET.get('name')
    description = request.GET.get('description')
    project_code = request.GET.get('project_code')
    client_company = int(request.GET.get('company_id'))
    start_date = request.GET.get('estimated_start_date')
    end_date = request.GET.get('estimated_end_date')
    project_status = request.GET.get('status')
    created_by = request.user.id
    parent = request.session['company_id']

    new_list = []
    new_list.append(client_company)
    new_list.append(parent)

    project_count = Project.objects.all().count()            
    project_number = project_count + 1

    test_string = str(project_number)

    # only pick short year
    current_year_short = datetime.datetime.now().strftime('%y')
    str_date = str(current_year_short)
    
    result = ""
    final_result_code = ""

    # retrieve project code format from database
    codes = ProjectCode.objects.all().first()
    code = codes.project_code

    if project_code is not None:
        final_result_code = project_code
    else:
        if len(test_string) ==  1:
            N=2
            result = test_string.zfill(N + len(test_string)) 
            final_result_code = code + "/" + str_date + "/" + result
        elif len(test_string) == 2:
            N=1
            result = test_string.zfill(N + len(test_string)) 
            final_result_code = code + "/"  + str_date + "/" + result
        else:
            result = test_string
            final_result_code = code + "/"  + str_date + "/" + result


    estimated_cost = 0;
    
    if start_date == "":
        start_date = None
        estimated_start_date = None
    else:
        estimated_start_date = datetime.datetime.strptime(start_date, "%m/%d/%Y").strftime("%Y-%m-%d")
        
    if end_date == "":
        end_date = None
        estimated_end_date = None
    else:
        estimated_end_date = datetime.datetime.strptime(end_date, "%m/%d/%Y").strftime("%Y-%m-%d")
    
    if project_status == "":
        status = None
    else:            
        status = Status.objects.get(id=project_status)

    estimate = float(estimated_cost)
    user_id = User.objects.get(id=created_by)

    project = Project(name=name, description=description, project_code=final_result_code, estimated_cost=estimate,
    estimated_start_date=estimated_start_date, estimated_end_date=estimated_end_date,
    project_status=status, created_by=user_id)

    project.save()
    for value in new_list:
        project.company.add(value)
        
    template = loader.get_template('project_management/list_customer_projects.html')

    projects =Project.company.through.objects.filter(company_id=int(client_company))
    company = Company.objects.get(id=int(client_company))
    project_list = []

    for project in projects:
        project_list.append(project.project_id)

    new_list = []

    for project_id in project_list:
        new_project = Project.objects.filter(id=project_id)

        for val in new_project:
            new_list.append(val)
    
    context = {
        "projects": new_list,
        "company_id": company.id,
        "company_name": company.name
    }

    return HttpResponse(template.render(context, request))


def assigned_users(request):
    """view members assigned to projects"""

    project_id = int(request.GET.get('project_id'))
    company_id = int(request.GET.get('company_id'))

    projects =Project.company.through.objects.filter(company_id=int(company_id))
    company = Company.objects.get(id=int(company_id))
    project_list = []

    for project in projects:
        project_list.append(project.project_id)

    new_list = []

    for project_id in project_list:
        new_project = Project.objects.filter(id=project_id)

        for val in new_project:
            new_list.append(val)

    context = {
        'company_id': company_id,
        'project_id': project.id,
    }

    return render(request, 'project_management/assigned_users.html', context) 


class UpdateCustomerProject(UpdateView):
    model = Project
    fields = ['name', 'project_status', 'company', 'project_code', 'final_cost', 'estimated_start_date', 'estimated_end_date', 'actual_start_date', 'actual_end_date', 'description', 'logo']
    template_name = 'project_management/update_customer_project.html'
    success_url = reverse_lazy('listProjects')


def list_customer_service_requests(request):
    """view service requests by customer"""

    company_id = request.GET.get('company_id')
    
    template = loader.get_template('project_management/list_customer_service_requests.html')
    
    company = Company.objects.get(id=int(company_id))

    context = {
        "company_id": company_id,
        "company_name": company.name
    }

    return HttpResponse(template.render(context, request))


def fetch_SLAs_by_customer(request):
    id_customer = request.GET.get('id_customer')
    
    list_customer_slas = ServiceLevelAgreement.objects.filter(customer_id=int(id_customer))
    data = {
        'sla': serializers.serialize("json", list_customer_slas)
    }
    return JsonResponse(data)


def fetch_requests_by_sla(request):
    id_sla_contract = request.GET.get('id_sla_contract')
    id_user = int(request.GET.get('id_user_dept01'))
  
    list_sla_requests = CustomerRequest.objects.filter(sla_id=int(id_sla_contract), assigned_member__assigned_member=id_user)
    data = {
        'req': serializers.serialize("json", list_sla_requests)
    }
    return JsonResponse(data)


def list_customer_sla(request):
    """view SLAs by customer"""

    company_id = request.GET.get('company_id')
    
    template = loader.get_template('project_management/list_customer_sla.html')

    company = Company.objects.get(id=int(company_id))

    context = {
        "company_id": company_id,
        "company_name": company.name
    }

    return HttpResponse(template.render(context, request))


def check_task(request):
    task_name = request.GET.get('task_name')
    task_id = int(request.GET.get('task_id'))

    if Timesheet.objects.filter(task_id=task_id).exists():
        response_data = {
            "success": False,
            "message": "Cannot delete"
        }

        return JsonResponse(response_data)
    else:
        response_data = {
            "success": True,
            "message": "Can delete"
        }

        return JsonResponse(response_data)


def assign_customer_request(request):
    req_id = request.GET.get('req_id')
    req_name = request.GET.get('req_name')
    req_name = request.GET.get('req_name')

    department_id = request.session['department_id']

    users = User.objects.filter(department_id=department_id)

    template = loader.get_template('project_management/assign_customer_requests.html')

    context = {
        "req_id": req_id,
        "req_name": req_name,
        "users": users
    }
    
    return HttpResponse(template.render(context, request))


def save_assigned_customerrequests(request):
    customer_request_id = request.GET.get('customer_request_id')
    project_members = request.GET.get('project_members')
    uid = request.user.id
    department_id = request.session['department_id']
    customer_request_id = request.GET.get('customer_request_id')
    dataToggle = request.GET.get('dataToggle')

    json_data = json.loads(project_members)
    
    CustomerRequest.objects.filter(pk=int(customer_request_id)).update(client_request_status='PENDING', status='PENDING')
    
    Trackstatus.objects.create(customerrequest_id=int(customer_request_id), request_status="PENDING", added_by_id=uid)
    
    for mem in json_data:
        CustomerRequestTeamMembers.objects.create(customerrequest_id=int(customer_request_id), assigned_member_id=int(mem), date_assigned=datetime.date.today(), assigned_by_id=uid)

    if dataToggle == 'true':
        template = loader.get_template('project_management/list_customer_requests.html')
    
        open_req_list = CustomerRequest.objects.filter(client_request_status="OPEN", department_id=department_id)
        pending_reg_list = CustomerRequest.objects.filter(client_request_status='PENDING', department_id=department_id)
        completed_reg_list = CustomerRequest.objects.filter(client_request_status='COMPLETED', department_id=department_id)
        cancelled_reg_list = CustomerRequest.objects.filter(client_request_status='CANCELED', department_id=department_id)
        onhold_reg_list = CustomerRequest.objects.filter(client_request_status='ONHOLD', department_id=department_id)

        context = {
            'open_req_list': open_req_list,
            'pending_reg_list': pending_reg_list,
            'completed_reg_list': completed_reg_list,
            'cancelled_reg_list': cancelled_reg_list,
            'onhold_reg_list': onhold_reg_list
        }
    if dataToggle == 'false':
        template = loader.get_template('project_management/list_your_customer_requests.html')

        open_req_list = CustomerRequest.objects.filter(client_request_status="OPEN", creator_id=uid, department_id=department_id)
        pending_reg_list = CustomerRequest.objects.filter(client_request_status='PENDING', assigned_member=uid, department_id=department_id)
        completed_reg_list = CustomerRequest.objects.filter(client_request_status='COMPLETED', trackstatus__request_status="COMPLETED", trackstatus__added_by_id=uid, department_id=department_id)
        cancelled_reg_list = CustomerRequest.objects.filter(client_request_status='CANCELED', trackstatus__request_status="CANCELED", trackstatus__added_by_id=uid, department_id=department_id)
        onhold_reg_list = CustomerRequest.objects.filter(client_request_status='ONHOLD', trackstatus__request_status="ONHOLD", trackstatus__added_by_id=uid, department_id=department_id)

        context = {
            'open_req_list': open_req_list,
            'pending_reg_list': pending_reg_list,
            'completed_reg_list': completed_reg_list,
            'cancelled_reg_list': cancelled_reg_list,
            'onhold_reg_list': onhold_reg_list
        }
    
    return HttpResponse(template.render(context, request))


def save_assigned_engineer(request):
    cr_name = request.GET.get('cr_name')
    customer_request_id = request.GET.get('cr_id')
    cr_code = request.GET.get('cr_code')
    project_members = request.GET.get('project_members')
    uid = request.user.id

    json_data = json.loads(project_members)

    for mem in json_data:
        CustomerRequestTeamMembers.objects.create(customerrequest_id=int(customer_request_id), assigned_member_id=int(mem), date_assigned=datetime.date.today(), assigned_by_id=uid)

    # to add a customer request team member, you must be an assigned member
    check_if_assigned_member = CustomerRequestTeamMembers.objects.filter(customerrequest_id=int(cr_id), assigned_member_id=user_id).exists()

    cr_team = CustomerRequestTeamMembers.objects.filter(customerrequest_id=int(customer_request_id))
    template = loader.get_template('project_management/customer_request_team_members.html')
    context = {
       "cr_name": cr_name,
       "cr_id": customer_request_id,
       "cr_code": cr_code,
       "cr_members": cr_team,
       "check_if_assigned_member": check_if_assigned_member
    }
    
    return HttpResponse(template.render(context, request))


def check_project_code_exists(request):
    """ check if project_code added"""
    if ProjectCode.objects.all().exists():
        data = {
            "status": True
        }
    else:
        data = {
            "status": False
        }

    return JsonResponse(data)


def timesheet_daily_report(request):
    today_date = datetime.datetime.today().date()
    today_date = datetime.datetime.strptime(str(today_date), "%Y-%m-%d").strftime("%d-%m-%Y")
    default_date_date = datetime.datetime.strptime(today_date, '%d-%m-%Y').strftime("%A, %d. %B %Y")
    template = loader.get_template('project_management/timesheet_daily_report_pane.html')
    context = {
        'today_date': today_date,
        'selected_date': default_date_date
        }

    return HttpResponse(template.render(context, request))


def filter_timesheet_daily_report(request):
    company_id = request.session['company_id']
    selected_date = request.GET.get('selected_date')
    selected_date2 = request.GET.get('selected_date')
    department_id = request.session['department_id']

    selected_date = datetime.datetime.strptime(selected_date, '%d-%m-%Y')
    selected_date2 = datetime.datetime.strptime(selected_date2, '%d-%m-%Y').strftime("%A, %d. %B %Y")

    dept_members_exist = User.objects.filter(company_id=company_id, department_id=department_id).exists()
    if dept_members_exist == True:
        dept_members = User.objects.filter(company_id=company_id, department_id=department_id, is_active=True)
        all_member_tms = []
        for mem in dept_members:
            sum_duration = 0
            new_dict = {}
            new_dict['label'] = mem.first_name + " " + (mem.last_name)
            duration = Timesheet.objects.filter(log_day=selected_date, project_team_member_id=mem.id, company_id=company_id)
            for ii in duration:
                sum_duration = sum_duration + ii.durationsec()
            new_dict['value'] = compute_duration(sum_duration)
            all_member_tms.append(new_dict)
    else:
        all_member_tms = ''

    template = loader.get_template('project_management/filter_members_daily_timesheets.html')
    context = {
        'timesheet_report': all_member_tms,
        'selected_date': selected_date2
    }

    return HttpResponse(template.render(context, request))


def export_daily_tm_report(request):
    company_id = request.session['company_id']
    selected_date = request.POST.get('id_selected_day')
    department_id = request.session['department_id']

    selected_date = datetime.datetime.strptime(selected_date, '%d-%m-%Y')

    dept_members_exist = User.objects.filter(company_id=company_id, department_id=department_id).exists()
    if dept_members_exist == True:
        dept_members = User.objects.filter(company_id=company_id, department_id=department_id, is_active=True)
        all_member_tms = []
        for mem in dept_members:
            sum_duration = 0
            new_dict = {}
            new_dict['label'] = mem.first_name + " " + (mem.last_name)
            duration = Timesheet.objects.filter(log_day=selected_date, project_team_member_id=mem.id, company_id=company_id)
            for ii in duration:
                sum_duration = sum_duration + ii.durationsec()
            new_dict['value'] = compute_duration(sum_duration)
            all_member_tms.append(new_dict)
    else:
        all_member_tms = ''

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Timesheetreport.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("DailyTimesheet")

    row_num = 1

    columns = [(u"Name", 5000), (u"Duration", 5000)]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        # set column width
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1

    for obj in all_member_tms:
        row_num += 1

        row = [
            obj['label'],
            obj['value'],
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)

    wb.save(response)
    return response


def export_and_send_email_daily_tm_report(request):
    company_id = request.session['company_id']
    selected_date = request.GET.get('id_selected_day')
    department_id = request.session['department_id']
    selected_date2 = request.GET.get('id_selected_day')
    selected_date = datetime.datetime.strptime(selected_date, '%d-%m-%Y')

    excelfile = BytesIO()

    dept_members_exist = User.objects.filter(company_id=company_id, department_id=department_id).exists()
    if dept_members_exist == True:
        dept_members = User.objects.filter(company_id=company_id, department_id=department_id, is_active=True)
        all_member_tms = []
        for mem in dept_members:
            sum_duration = 0
            new_dict = {}
            new_dict['label'] = mem.first_name + " " + (mem.last_name)
            duration = Timesheet.objects.filter(log_day=selected_date, project_team_member_id=mem.id, company_id=company_id)
            for ii in duration:
                sum_duration = sum_duration + ii.durationsec()
            new_dict['value'] = compute_duration(sum_duration)
            all_member_tms.append(new_dict)
    else:
        all_member_tms = ''

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("DailyTimesheet")

    row_num = 1

    columns = [(u"Name", 5000), (u"Duration", 5000)]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        # set column width
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1

    for obj in all_member_tms:
        row_num += 1

        row = [
            obj['label'],
            obj['value'],
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)

    wb.save(excelfile)

    selected_date2 = datetime.datetime.strptime(selected_date2, '%d-%m-%Y').strftime("%A, %d. %B %Y")
    context22 = {
        'selected_date': selected_date2,
        'department': request.session['department'],
    }

    msg = render_to_string('project_management/email_template_timesheet_report.html', context22)

    email_address = 'gracebabiryek@gmail.com'
    subject, from_email, to = 'SYBYL', 'from@example.com', email_address
    text_content = 'SERVICE DESK.'
    html_content = msg
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach('TimesheetReport.xls', excelfile.getvalue(), 'application/ms-excel')
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    context1 = {
        'timesheet_report': all_member_tms,
        'selected_date': selected_date2,
    }

    template = loader.get_template('project_management/filter_members_daily_timesheets.html')
    return HttpResponse(template.render(context1, request))


def detailed_task_report_pane(request):
    today_date = datetime.datetime.today().date()
    today_date = datetime.datetime.strptime(str(today_date), "%Y-%m-%d").strftime("%d-%m-%Y")
    default_date_date = datetime.datetime.strptime(today_date, '%d-%m-%Y').strftime("%A, %d. %B %Y")

    company_id = request.session['company_id']
    department_id = request.session['department_id']
    department_name = request.session['department']

    department_list = Department.objects.filter(Q(company=company_id) & ~Q(id=department_id))

    template = loader.get_template('project_management/detailed_task_timesheet_report_pane.html')
    context = {
        'today_date': today_date,
        'selected_date': default_date_date,
        'department_list': department_list,
        'department_id': department_id,
        'department_name': department_name
        }

    return HttpResponse(template.render(context, request))


def filter_detailed_task_timesheet_report(request):
    company_id = request.session['company_id']
    selected_date = request.GET.get('selected_date')
    selected_date2 = request.GET.get('selected_date')
    department_id = int(request.GET.get('id_department'))

    selected_date = datetime.datetime.strptime(selected_date, '%d-%m-%Y')
    selected_date2 = datetime.datetime.strptime(selected_date2, '%d-%m-%Y').strftime("%A, %d. %B %Y")

    dept_members_exist = User.objects.filter(company_id=company_id, department_id=department_id).exists()
    if dept_members_exist == True:
        dept_members = User.objects.filter(company_id=company_id, department_id=department_id, is_active=True)
        all_mem_gen_list = []
        
        for mem in dept_members:
            sum_duration = 0
            new_dict = {}
            all_member_tasks = []
            individual_tms = {}
            new_dict['mid'] = mem.id
            new_dict['label'] = mem.first_name + " " + (mem.last_name)
            member_tms = Timesheet.objects.filter(log_day=selected_date, project_team_member_id=mem.id, company_id=company_id)
            for duration in member_tms:
                sum_duration = sum_duration + duration.durationsec()
            new_dict['total_dur'] = compute_duration(sum_duration)

            for tm_list in member_tms:
                tm_dict_mem = {}
                tm_dict_mem['duration'] = compute_duration(tm_list.durationsec())
                tm_dict_mem['notes'] = tm_list.notes
                tm_dict_mem['timesheet_category'] = tm_list.timesheet_category
                tm_dict_mem['tmid'] = tm_list.id
                tm_dict_mem['stime'] = tm_list.start_time
                tm_dict_mem['etime'] = tm_list.end_time
                            
                if TaskTimesheetExtend.objects.filter(timesheet_id=tm_list.id).exists():
                    if tm_list.timesheet_category == "TIMESHEET" :

                        task_detail = TaskTimesheetExtend.objects.get(timesheet_id=tm_list.id)
                        task_id_1 = task_detail.task_id
                        
                        task_name = Task.objects.get(id=task_id_1).name
                        tm_dict_mem['task'] = task_name
                        project_det = Task.objects.get(id=task_id_1).project
                        milestone_det = Task.objects.get(id=task_id_1).milestone
                        tm_dict_mem['project'] = project_det
                        tm_dict_mem['milestone'] = milestone_det
                    else: 
                        request_detail = RequestTimesheetExtend.objects.get(timesheet_id=tm_list.id)
                        req_id = request_detail.customer_request_id
                        req_name = CustomerRequest.objects.get(id=req_id).name
                        tm_dict_mem['task'] = req_name

                        cust_req = CustomerRequest.objects.get(id=req_id)
                        milestone_det = "Customer Request"
                        tm_dict_mem['project'] = cust_req
                        tm_dict_mem['milestone'] = milestone_det

                    all_member_tasks.append(tm_dict_mem)
            new_dict['timesheets'] = all_member_tasks
            all_mem_gen_list.append(new_dict)
                        
            final_list = []
            proj_set = set()
            for rr in all_mem_gen_list:
                for yy in rr['timesheets']:
                    dict_mems = {}

                    if(rr['mid'] not in proj_set):
                        proj_set.add(rr['mid'])
                        dict_mems['name'] = rr['label']
                        dict_mems['total_dur'] = rr['total_dur']
                    else:
                        dict_mems['name'] = ''
                        dict_mems['total_dur'] = rr['total_dur']

                    dict_mems['task'] = yy['task']
                    dict_mems['duration'] = yy['duration']
                    dict_mems['notes'] = yy['notes']
                    dict_mems['project'] = yy['project']
                    dict_mems['milestone'] = yy['milestone']
                    dict_mems['stime'] = yy['stime']
                    dict_mems['etime'] = yy['etime']
                    final_list.append(dict_mems)

        all_mem_gen_list = final_list

    else:
        all_mem_gen_list = ''

    template = loader.get_template('project_management/filter_detailed_completed_task_report.html')
    context = {
        'timesheet_report': all_mem_gen_list,
        'selected_date': selected_date2
    }

    return HttpResponse(template.render(context, request))


def export_timesheet_task_report(request):
    company_id = request.session['company_id']
    selected_date = request.POST.get('id_selected_day_002')
    department_id = request.session['department_id']

    selected_date = datetime.datetime.strptime(selected_date, '%d-%m-%Y')

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=DetailedTaskReport.xls'
    wb = xlwt.Workbook(encoding='utf-8')

    dept_members_exist = User.objects.filter(company_id=company_id, department_id=department_id).exists()
    if dept_members_exist == True:
        # return timesheet summary
        dept_members = User.objects.filter(company_id=company_id, department_id=department_id, is_active=True)
        all_member_tms = []
        for member in dept_members:
            sum_duration = 0
            new_dict = {}
            new_dict['label'] = member.first_name + " " + (member.last_name)
            duration = Timesheet.objects.filter(log_day=selected_date, project_team_member_id=member.id, company_id=company_id)
            for ii in duration:
                sum_duration = sum_duration + ii.durationsec()
            new_dict['value'] = compute_duration(sum_duration)
            all_member_tms.append(new_dict)
        
        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        title_style = xlwt.XFStyle()
        title_style.font.bold = True
        title_style.font.height = 270
        title_style.font.width = 270

        ws = wb.add_sheet("Summary")
        ws.write(0, 1, "TimeSheet Summary ", title_style)

        row_num = 2

        columns = [(u"Name", 5000), (u"Duration", 5000)]

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num][0], font_style)
            # set column width
            ws.col(col_num).width = columns[col_num][1]

        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1

        for obj in all_member_tms:
            row_num += 1

            row = [
                obj['label'],
                obj['value'],
            ]

            for col_num in range(len(row)):
                ws.write(row_num, col_num, str(row[col_num]), font_style)
    	
        # return timesheet individual time
        all_mem_gen_list = []
        
        for mem in dept_members:
            sum_duration = 0
            new_dict = {}
            all_member_tasks = []
            individual_tms = {}
            new_dict['mid'] = mem.id
            new_dict['label'] = mem.first_name + " " + (mem.last_name)
            member_tms = Timesheet.objects.filter(log_day=selected_date, project_team_member_id=mem.id, company_id=company_id)
            for duration in member_tms:
                sum_duration = sum_duration + duration.durationsec()
            new_dict['total_dur'] = compute_duration(sum_duration)

            for tm_list in member_tms:
                tm_dict_mem = {}
                tm_dict_mem['duration'] = compute_duration(tm_list.durationsec())
                tm_dict_mem['notes'] = tm_list.notes
                tm_dict_mem['timesheet_category'] = tm_list.timesheet_category
                tm_dict_mem['tmid'] = tm_list.id
                stime = str(tm_list.start_time)
                stime = datetime.datetime.strptime(stime, '%H:%M:%S').strftime('%I:%M %p')
                etime = str(tm_list.end_time)
                etime = datetime.datetime.strptime(etime, '%H:%M:%S').strftime('%I:%M %p')
                tm_time = stime + " - " + etime
                tm_dict_mem['tm_time'] = tm_time           
                if tm_list.timesheet_category == "TIMESHEET":
                    task_detail = TaskTimesheetExtend.objects.get(timesheet_id=tm_list.id)
                    task_id_1 = task_detail.task_id
                    task_name = Task.objects.get(id=task_id_1).name
                    tm_dict_mem['task'] = task_name
                    project_det = Task.objects.get(id=task_id_1).project
                    milestone_det = Task.objects.get(id=task_id_1).milestone
                    tm_dict_mem['project'] = project_det
                    tm_dict_mem['milestone'] = milestone_det
                else: 
                    request_detail = RequestTimesheetExtend.objects.get(timesheet_id=tm_list.id)
                    req_id = request_detail.customer_request_id
                    req_name = CustomerRequest.objects.get(id=req_id).name
                    tm_dict_mem['task'] = req_name

                    cust_req = CustomerRequest.objects.get(id=req_id)
                    milestone_det = "Customer Request"
                    tm_dict_mem['project'] = cust_req
                    tm_dict_mem['milestone'] = milestone_det

                all_member_tasks.append(tm_dict_mem)
            new_dict['timesheets'] = all_member_tasks
            all_mem_gen_list.append(new_dict)

        for obj11 in all_mem_gen_list:
            font_style1 = xlwt.XFStyle()
            font_style1.font.bold = True
            font_style1.font.height = 270
            font_style1.font.width = 270

            ws = wb.add_sheet(obj11['label'])
            m_header = 'User: '+ obj11['label'] + " - " + "Total Duration: "+ obj11['total_dur']
            ws.write(0, 1, m_header, font_style1)
            
            row_num = 1
            columns = [(u"Task", 5000), (u"Duration", 5000), (u"Time Range", 5000), (u"Project", 5000)
            , (u"Milestone", 5000), (u"Details", 5000)]

            font_style = xlwt.XFStyle()
            font_style.font.bold = True
            font_style.alignment.wrap = 1

            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num][0], font_style)
                # set column width
                ws.col(col_num).width = columns[col_num][1]

            for obj in obj11['timesheets']:
                row_num += 1
                row = [
                    obj['task'],
                    obj['duration'],
                    obj['tm_time'],
                    obj['project'],
                    obj['milestone'],
                    obj['notes'],
                ]
                
                for col_num in range(len(row)):
                    ws.write(row_num, col_num, str(row[col_num]), font_style)

        wb.save(response)
        return response
    else:
        all_mem_gen_list = ''
        all_member_tms = ''
        return response


def export_email_timesheet_task_report(request):
    company_id = request.session['company_id']
    selected_date = request.GET.get('id_selected_day_002')
    department_id = int(request.GET.get('id_department'))
    selected_date2 = request.GET.get('id_selected_day_002')
    selected_date = datetime.datetime.strptime(selected_date, '%d-%m-%Y')
    department_name = Department.objects.get(id=department_id)

    excelfile = BytesIO()

    wb = xlwt.Workbook(encoding='utf-8')
    
    dept_members_exist = User.objects.filter(company_id=company_id, department_id=department_id).exists()
    if dept_members_exist == True:
        # return timesheet summary
        dept_head_email = []
        head_dept = User.objects.filter(company_id=company_id, department_id=department_id, is_active=True, is_dept_head=True)
        for leader in head_dept:
            dept_head_email.append(leader.email)

        dept_members = User.objects.filter(company_id=company_id, department_id=department_id, is_active=True, is_dept_head=False)
        all_member_tms = []
        dept_emails = []
        for member in dept_members:
            dept_emails.append(member.email)  
            sum_duration = 0
            new_dict = {}
            new_dict['label'] = member.first_name + " " + (member.last_name)
            duration = Timesheet.objects.filter(log_day=selected_date, project_team_member_id=member.id, company_id=company_id)
            for ii in duration:
                sum_duration = sum_duration + ii.durationsec()
            new_dict['value'] = compute_duration(sum_duration)
            all_member_tms.append(new_dict)
        
        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        title_style = xlwt.XFStyle()
        title_style.font.bold = True
        title_style.font.height = 270
        title_style.font.width = 270

        ws = wb.add_sheet("Summary")
        ws.write(0, 1, "TimeSheet Summary ", title_style)

        row_num = 2

        columns = [(u"Name", 5000), (u"Duration", 5000)]

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num][0], font_style)
            # set column width
            ws.col(col_num).width = columns[col_num][1]

        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1

        for obj in all_member_tms:
            row_num += 1

            row = [
                obj['label'],
                obj['value'],
            ]

            for col_num in range(len(row)):
                ws.write(row_num, col_num, str(row[col_num]), font_style)
    	
        # return individual timesheets
        all_mem_gen_list = []
        
        for mem in dept_members:
            sum_duration = 0
            new_dict = {}
            all_member_tasks = []
            individual_tms = {}
            new_dict['mid'] = mem.id
            new_dict['label'] = mem.first_name + " " + (mem.last_name)
            member_tms = Timesheet.objects.filter(log_day=selected_date, project_team_member_id=mem.id, company_id=company_id)
            for duration in member_tms:
                sum_duration = sum_duration + duration.durationsec()
            new_dict['total_dur'] = compute_duration(sum_duration)

            for tm_list in member_tms:
                tm_dict_mem = {}
                tm_dict_mem['duration'] = compute_duration(tm_list.durationsec())
                tm_dict_mem['notes'] = tm_list.notes
                tm_dict_mem['timesheet_category'] = tm_list.timesheet_category
                tm_dict_mem['tmid'] = tm_list.id
                stime = str(tm_list.start_time)
                stime = datetime.datetime.strptime(stime, '%H:%M:%S').strftime('%I:%M %p')
                etime = str(tm_list.end_time)
                etime = datetime.datetime.strptime(etime, '%H:%M:%S').strftime('%I:%M %p')
                tm_time = stime + " - " + etime
                tm_dict_mem['tm_time'] = tm_time           
                if tm_list.timesheet_category == "TIMESHEET":
                    task_detail = TaskTimesheetExtend.objects.get(timesheet_id=tm_list.id)
                    task_id_1 = task_detail.task_id
                    task_name = Task.objects.get(id=task_id_1).name
                    tm_dict_mem['task'] = task_name
                    project_det = Task.objects.get(id=task_id_1).project
                    milestone_det = Task.objects.get(id=task_id_1).milestone
                    tm_dict_mem['project'] = project_det
                    tm_dict_mem['milestone'] = milestone_det
                else: 
                    request_detail = RequestTimesheetExtend.objects.get(timesheet_id=tm_list.id)
                    req_id = request_detail.customer_request_id
                    req_name = CustomerRequest.objects.get(id=req_id).name
                    tm_dict_mem['task'] = req_name

                    cust_req = CustomerRequest.objects.get(id=req_id)
                    milestone_det = "Customer Request"
                    tm_dict_mem['project'] = cust_req
                    tm_dict_mem['milestone'] = milestone_det

                all_member_tasks.append(tm_dict_mem)
            new_dict['timesheets'] = all_member_tasks
            all_mem_gen_list.append(new_dict)

        for obj11 in all_mem_gen_list:
            font_style1 = xlwt.XFStyle()
            font_style1.font.bold = True
            font_style1.font.height = 270
            font_style1.font.width = 270

            ws = wb.add_sheet(obj11['label'])
            m_header = 'User: '+ obj11['label'] + " - " + "Total Duration: "+ obj11['total_dur']
            ws.write(0, 1, m_header, font_style1)
            
            row_num = 1
            columns = [(u"Task", 5000), (u"Duration", 5000), (u"Time Range", 5000), (u"Project", 5000)
            , (u"Milestone", 5000), (u"Details", 5000)]

            font_style = xlwt.XFStyle()
            font_style.font.bold = True
            font_style.alignment.wrap = 1

            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num][0], font_style)
                # set column width
                ws.col(col_num).width = columns[col_num][1]

            for obj in obj11['timesheets']:
                row_num += 1
                row = [
                    obj['task'],
                    obj['duration'],
                    obj['tm_time'],
                    obj['project'],
                    obj['milestone'],
                    obj['notes'],
                ]
                
                for col_num in range(len(row)):
                    ws.write(row_num, col_num, str(row[col_num]), font_style)

        wb.save(excelfile)
    else:
        all_mem_gen_list = ''
        all_member_tms = ''

    selected_date2 = datetime.datetime.strptime(selected_date2, '%d-%m-%Y').strftime("%A, %d. %B %Y")
  
    context22 = {
        'selected_date': selected_date2,
        'department': department_name.name,
        'mem_duration': all_member_tms,
    }

    msg = render_to_string('project_management/email_template_timesheet_report.html', context22)

    subject, from_email, to = 'Daily Timesheets for Resources', 'from@example.com', dept_emails
    text_content = 'SERVICE DESK.'
    html_content = msg
    msg = EmailMultiAlternatives(subject, text_content, from_email, to=dept_head_email, cc=dept_emails)
    msg.attach('TimesheetReport.xls', excelfile.getvalue(), 'application/ms-excel')
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    context1 = {
        'timesheet_report': all_mem_gen_list,
        'selected_date': selected_date2,
    }

    template = loader.get_template('project_management/filter_detailed_completed_task_report.html')
    return HttpResponse(template.render(context1, request))


def timesheet_defaulter_list(request):
    company_id = request.session['company_id']
    department_id = int(request.GET.get('id_department'))
    selected_date = request.GET.get('selected_date')
    selected_date2 = request.GET.get('selected_date')
    defaulter_state = False

    selected_date = datetime.datetime.strptime(selected_date, '%d-%m-%Y')
    selected_date2 = datetime.datetime.strptime(selected_date2, '%d-%m-%Y').strftime("%A, %d. %B %Y")

    dept_members_exist = User.objects.filter(company_id=company_id, department_id=department_id, is_dept_head=False).exists()
    if dept_members_exist == True:
        dept_members = User.objects.filter(company_id=company_id, department_id=department_id, is_active=True, is_dept_head=False)
        all_mem_gen_list = []
        
        for mem in dept_members:
            sum_duration = 0
            new_dict = {}
            all_member_tasks = []
            individual_tms = {}
            new_dict['mid'] = mem.email
            new_dict['label'] = mem.first_name + " " + (mem.last_name)
            member_tms = Timesheet.objects.filter(log_day=selected_date, project_team_member_id=mem.id, company_id=company_id)
            for duration in member_tms:
                sum_duration = sum_duration + duration.durationsec()
            new_dict['total_dur'] = compute_duration(sum_duration)
            
            # IF Member timesheets total hours are below 3 hrs [10800]
            if sum_duration < 10800:
                all_mem_gen_list.append(new_dict)

    else:
        all_mem_gen_list = ''

    if len(all_mem_gen_list) == 0: 
        defaulter_state = False
    else: 
        defaulter_state = True

    response_data = {
        'timesheet_report': all_mem_gen_list,
        "defaulter_state": defaulter_state
    }

    return JsonResponse(response_data)


def send_timesheet_email_reminder(request):
    company_id = request.session['company_id']
    department_id = int(request.GET.get('id_department'))
    defaulter_data = request.GET.get('dataArray1')
    defaulter_data = json.loads(defaulter_data)

    selected_date = request.GET.get('id_selected_day_002')
    selected_date2 = request.GET.get('id_selected_day_002')
    selected_date = datetime.datetime.strptime(selected_date, '%d-%m-%Y')
    
    selected_date2 = datetime.datetime.strptime(selected_date2, '%d-%m-%Y').strftime("%A, %d. %B %Y")
    current_date = date.today().strftime("%A, %d. %B %Y")
    
    for defaulter in defaulter_data:
        context22 = {
            'selected_date': selected_date2,
            'department': request.session['department'],
            'current_date': current_date,
            'name': defaulter['label'],
            'total_time': defaulter['total_dur']
        }

        msg1 = render_to_string('project_management/email_template_timesheet_remainder.html', context22)

        subject, from_email = 'Timesheet Reminder', 'from@example.com'
        text_content = 'Timesheet Reminder'
        html_content = msg1
        msg1 = EmailMultiAlternatives(subject, text_content, from_email, to=[defaulter['mid']])
        msg1.attach_alternative(html_content, "text/html")
        msg1.send()
        

    response_data = {
        'status': True,
    }

    return JsonResponse(response_data)


# @background(schedule=10)
# def notify_user():
#     # lookup user by id and send them a message
#     # user = User.objects.get(pk=user_id)
#     # user.email_user('Here is a notification', 'You have been notified')
#     print('xxxxxxxxxxxxxxx-xxxx---------------------xxxxxxxxxxx')


# notify_user()
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

from .models import Project, Milestone, Task, ProjectDocument, Incident, Priority, Status, ProjectTeam, ProjectTeamMember, Role, ProjectForumMessages, ProjectForum, ProjectForumMessageReplies, ServiceLevelAgreement, IncidentComment, EscalationLevel, IncidentComment, Timesheet, ResubmittedTimesheet, ProjectCode
from user_management.models import User
from company_management.models import Company, CompanyCategory, CompanyDomain
from .forms import CreateProjectForm, MilestoneForm, TaskForm, DocumentForm, ProjectUpdateForm, MilestoneUpdateForm, ProjectForm, IncidentForm, ProjectTeamForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.db.models import Count
import json
import time
from django.db.models import Sum


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


def milestone_list_by_project(request, project_id):
    project_milestones = Milestone.objects.filter(project_id=project_id)
    return render(request, 'project_management/milestone_list.html', {'milestones': project_milestones})


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


def load_milestones(request):
    projects = Project.objects.all
    return render(request, 'project_management/milestone_list.extended.html', {'projects': projects})


def load_task_milestoneI_list(request):
    project_id = request.GET.get('project')
    milestones = Milestone.objects.filter(project_id=project_id).order_by('name')
    return render(request, 'project_management/new_task_milestone_dropdown_list_options.html',
                  {'milestones': milestones})


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

# def task_list_by_project(request, project_id):
#     project_tasks = Task.objects.filter(project_id=project_id)
#     return render(request, 'project_management/task_list.html', {'tasks': project_tasks})


@login_required
def task_list_by_users(request):
    user = request.user
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
        for value in tasks:
            task_list.append(value)

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


# INCIDENTS
class AddProjectIncident(LoginRequiredMixin, CreateView):
    model = Incident
    fields = ['project', 'title', 'description', 'status', 'priority', 'assignee', 'document', 'image', 'task', 'close_time']
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

        tasks = Task.objects.filter(project_id=project_id)
        context['tasks'] = tasks

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


def validate_incident_name(request):
    title = request.GET.get('title', None)
    project_id = int(request.GET.get('project_id'))

    project = Project.objects.get(id=project_id)

    data = {
        'is_taken': Incident.objects.filter(title=title, project_id=project.id).exists()
    }

    return JsonResponse(data)


class AddIncident(LoginRequiredMixin, CreateView):
    model = Incident
    fields = ['project', 'title', 'description', 'status', 'priority', 'assignee', 'document', 'image', 'task']
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

                open_incidents = Incident.objects.filter(Q(creator=request.user)|Q(assignee__in=team_member), project_id=project.id, status=open_status).annotate(assigned=Count('assignee', distinct=True))
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


class ListIncidents(ListView):
    template_name = 'project_management/list_incidents.html'
    context_object_name = 'all_incidents'

    def get_queryset(self):
        team_members = ProjectTeamMember.objects.filter(member=self.request.user)
        # return Incident.objects.filter(Q(assignee__in=team_members)|Q(creator=self.request.user)).annotate(assigned=Count('assignee'))
        return Incident.objects.annotate(assigned=Count('assignee', distinct=True)).filter(Q(assignee__in=team_members)|Q(creator=self.request.user))
        # return Incident.objects.annotate(assigned=Count('assignee')).filter(creator=self.request.user)


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
    fields = ['project', 'title', 'description', 'document', 'image', 'status', 'priority', 'assignee', 'resolution_time', 'reopen_time', 'close_time']
    template_name = 'project_management/update_incident.html'
    success_url = reverse_lazy('listIncidents')


class UpdateProjectIncident(UpdateView):
    model = Incident
    fields = ['title', 'description', 'document', 'image', 'status', 'priority', 'assignee', 'task', 'resolution_time', 'reopen_time', 'close_time']
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
                completed_incidents = Incident.objects.filter(Q(creator=request.user)|Q(assignee__in=team_member), project_id=project.id, status=completed_status).annotate(assigned=Count('assignee', distinct=True))
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
                
                onhold_incidents = Incident.objects.filter(Q(creator=request.user)|Q(assignee__in=team_member), project_id=project.id, status=onhold_status).annotate(assigned=Count('assignee', distinct=True))
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
                terminated_incidents = Incident.objects.filter(Q(creator=request.user)|Q(assignee__in=team_member), project_id=project.id, status=terminated_status).annotate(assigned=Count('assignee', distinct=True))
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

    team_members = Incident.assignee.through.objects.filter(id=incident_id)

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


# ROLES
class AddRole(CreateView):
    model = Role
    fields = ['name', 'description']
    template_name = 'project_management/add_role.html'
    success_url = reverse_lazy('listAllRoles')


class ListAllRoles(ListView):
    template_name = 'project_management/list_all_roles.html'
    context_object_name = 'list_roles'

    def get_queryset(self):
        return Role.objects.all()


class UpdateRole(UpdateView):
    model = Role
    fields = ['name', 'description']
    template_name = 'project_management/update_role.html'
    success_url = reverse_lazy('listAllRoles')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        roleid = int(self.request.GET['roleid'])
        context['roleid'] = roleid
        return context


class DeleteRole(DeleteView):
    model = Role
    success_url = reverse_lazy('listAllRoles')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


def ValidateRoleName(request):
    role_name = request.GET.get('rolename', None)
    data = {
        'is_taken': Role.objects.filter(name=role_name).exists()
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
            company = data['company']
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

            project = Project(name=name.title(), description=description, project_code=final_result_code, estimated_cost=estimate,
            logo=logo, estimated_start_date=estimated_start_date, estimated_end_date=estimated_end_date,
            project_status=status, created_by=user_id)

            project.save()
            for value in company:
                p = project.company.add(value)
                
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
    fields = ['name', 'project_status', 'company', 'project_code', 'final_cost', 'estimated_start_date', 'estimated_end_date', 'actual_start_date', 'actual_end_date', 'description', 'logo']
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
        open_incidents = Incident.objects.filter(project_id=project_id, status_id=open_status.id).count()
        onhold_incidents = Incident.objects.filter(project_id=project_id, status_id=onhold_status.id).count()
        completed_incidents = Incident.objects.filter(project_id=project_id, status_id=complete_status.id).count()
        terminated_incidents = Incident.objects.filter(project_id=project_id, status_id=terminated_status.id).count()

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
    role_id = request.GET.get('responsibility')
    project_id = request.GET.get('project_id')

    user = User.objects.get(id=member)
    role = Role.objects.get(id=role_id)
    team = ProjectTeam.objects.get(id=team_id)

    team_member = ProjectTeamMember(member=user, responsibility=role)
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


class UpdateProjectTeamMember(UpdateView):
    model = ProjectTeamMember
    fields = ['responsibility']
    template_name = 'project_management/update_project_team_member.html'
    success_url = reverse_lazy('tabListTeam')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_id = self.request.GET.get('memberid')
        context['member_id'] = member_id

        project_id = int(self.request.GET.get('project_id'))
        project = Project.objects.get(id=project_id)
        context['project_id'] = project.id
         
        return context


class AdminUpdateProjectTeamMember(UpdateView):
    """update project team member by admin"""

    model = ProjectTeamMember
    fields = ['responsibility']
    template_name = 'project_management/admin_update_project_member.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_id = self.request.GET.get('memberid')
        context['member_id'] = member_id

        project_id = int(self.request.GET.get('project_id'))
        project = Project.objects.get(id=project_id)
        context['project_id'] = project.id

        team_name = self.request.GET.get('team_name')
        team_id = int(self.request.GET.get('team_id'))
        team = ProjectTeam.objects.get(id=team_id)
        context['team_id'] = team.id
        context['team_name'] = team.name
        
        return context


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
    roles = Role.objects.all()

    if len(member_list) != 0:
        for member in member_list:
            old_user = User.objects.get(id=member.member_id)
            old.append(old_user)

        all_users = User.objects.filter()
        

        new_users = set(all_users).difference(set(old))
        data = {
            'users': serializers.serialize("json", new_users),
            'roles': serializers.serialize("json", roles)
        }

        return JsonResponse(data)

    else:
        new_users = User.objects.all().filter()
        data = {
            'users': serializers.serialize("json", new_users),
            'roles': serializers.serialize("json", roles)
        }

        return JsonResponse(data)


def save_update_team_member(request, pk):
    """update team member"""

    team_member = ProjectTeamMember.objects.get(id=int(pk))
    member_id = int(request.GET.get('member_id'))
    project_id = int(request.GET.get('project_id'))
    responsibility_id = int(request.GET.get('responsibility_id'))

    ProjectTeamMember.objects.filter(pk=int(pk)).update(responsibility_id=responsibility_id)

    response_data = {
        "success": True
    }

    return JsonResponse(response_data)


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


def project_sla_list(request):
    projectid = request.GET.get('projectid')
    projectname = request.GET.get('projectname')

    template = loader.get_template('project_management/project_sla_list.html')
    if ServiceLevelAgreement.objects.filter(project_id=projectid).exists():
        sla_obj = ServiceLevelAgreement.objects.filter(project_id=int(projectid)).first()
        status = True
    else:
        status = False

    if status:
        context = {
            'status': status,
            'sla_obj': sla_obj
        }
    else:
        context = {
            'status': status,
            'projectid':projectid,
            'projectname':projectname
        }

    return HttpResponse(template.render(context, request))


class AddSla(CreateView):
    model = ServiceLevelAgreement
    fields = ['name', 'project','description', 'response_time', 'resolution_time', 'resolution_duration', 'response_duration']

    template_name = 'project_management/add_sla.html'
    success_url = reverse_lazy('projectsla')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pro_id = self.request.GET.get('pro_id')
        pro_name = self.request.GET.get('pro_name')
        context['pro_id'] = pro_id
        context['pro_name'] = pro_name
        return context


def save_sla(request):
    sla_name = request.GET.get('sla_name')
    id_description = request.GET.get('id_description')
    id_response_time = request.GET.get('id_response_time')
    id_resolution_time = request.GET.get('id_resolution_time')
    settingtoggleresp = request.GET.get('settingtoggleresp')
    settingtoggleresoln = request.GET.get('settingtoggleresoln')
    id_project = request.GET.get('id_project')

    obj = ServiceLevelAgreement(name=sla_name, project_id=int(id_project), description=id_description, response_time=int(id_response_time),
               resolution_time=int(id_resolution_time), response_duration=settingtoggleresp, resolution_duration=settingtoggleresoln)
    obj.save()

    slas = ServiceLevelAgreement.objects.filter(project_id=int(id_project)).first()
    status = True
    template = loader.get_template('project_management/project_sla_list.html')
    context = {
        'status': status,
        'sla_obj': slas
    }

    return HttpResponse(template.render(context, request))


class UpdateSLA(UpdateView):
    model = ServiceLevelAgreement
    fields = ['name', 'project','description', 'response_time', 'resolution_time', 'resolution_duration', 'response_duration']
    template_name = 'project_management/update_sla.html'
    success_url = reverse_lazy('projectsla')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sla_id = self.kwargs['pk']
        response_time = self.get_object().response_time
        resolution_time = self.get_object().resolution_time
        resolution_duration = self.get_object().resolution_duration
        response_duration = self.get_object().response_duration
        int_proj_id = self.get_object().project_id
        context['sla_id'] = sla_id
        context['response_time'] = response_time
        context['resolution_time'] = resolution_time
        context['resolution_duration'] = resolution_duration
        context['response_duration'] = response_duration
        context['intial_project'] = int_proj_id
        return context


def save_sla_update(request):
    sla_name = request.GET.get('sla_name')
    id_description = request.GET.get('id_description')
    id_response_time = request.GET.get('id_response_time')
    id_resolution_time = request.GET.get('id_resolution_time')
    settingtoggleresp = request.GET.get('settingtoggleresp')
    settingtoggleresoln = request.GET.get('settingtoggleresoln')
    id_project = request.GET.get('id_project')
    sla_id = request.GET.get('sla_id')
    intial_project_id = request.GET.get('intial_project_id')

    ServiceLevelAgreement.objects.filter(pk=int(sla_id)).update(name=sla_name, description=id_description, response_time=id_response_time,
        resolution_time=id_resolution_time, resolution_duration=settingtoggleresoln, response_duration=settingtoggleresp,  project_id=int(id_project))
    
    slas = ServiceLevelAgreement.objects.filter(project_id=int(id_project)).first()
    
    if int(id_project) == int(intial_project_id):
        status = True
    else:
        status = False
        
    template = loader.get_template('project_management/project_sla_list.html')
    context = {
        'status': status,
        'sla_obj': slas
    } 

    return HttpResponse(template.render(context, request))

class ProjectEscalationList(ListView):
    template_name = 'project_management/project_escalation_list.html'
    context_object_name = 'esc_levels'

    def get_queryset(self):
        id_project = int(self.request.GET['projectid'])
        return EscalationLevel.objects.filter(project_id=int(id_project)).annotate(num_esc=Count('escalated_to'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pro_id = self.request.GET.get('projectid')
        pro_name = self.request.GET.get('projectname')
        context['projectid'] = pro_id
        context['projectname'] = pro_name
        return context


class AddEscalation(CreateView):
    model = EscalationLevel
    fields = ['name', 'project','description', 'escalated_by', 'escalated_to', 'escalation_on', 'escalation_on_duration']

    template_name = 'project_management/add_escalation_level.html'
    success_url = reverse_lazy('tabProjectEscalation')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pro_id = self.request.GET.get('pro_id')
        pro_name = self.request.GET.get('pro_name')
        context['projectid'] = pro_id
        context['projectname'] = pro_name
        return context


def save_escation_level(request):
    esc_name = request.GET.get('esc_name')
    id_description = request.GET.get('id_description')
    id_escalate_on = request.GET.get('id_escalate_on')
    escsettingtogglebtn = request.GET.get('escsettingtogglebtn')
    id_project = int(request.GET.get('id_project'))
    id_escalated_to = request.GET.get('id_escalated_to')
    project_name = request.GET.get('pro_name')
    uid = request.user.id

    obj = EscalationLevel(name=esc_name, project_id=id_project, description=id_description, escalated_by_id=uid, escalation_on=id_escalate_on, escalation_on_duration=escsettingtogglebtn)
    obj.save()

    for i in json.loads(id_escalated_to): 
        if obj.id is not None:
            escalation = EscalationLevel.objects.get(id=obj.id)
            user_escalated_to = User.objects.get(id=int(i))
            escalation.escalated_to.add(user_escalated_to)

    esc_levels = EscalationLevel.objects.filter(project_id=int(id_project)).annotate(num_esc=Count('escalated_to'))
    template = loader.get_template('project_management/project_escalation_list.html')
    context = {
        'esc_levels': esc_levels,
        'projectid': id_project,
        'projectname': project_name,
    }

    return HttpResponse(template.render(context, request))


class UpdateEscalationLevel(UpdateView):
    model = EscalationLevel
    fields = ['name', 'project','description', 'escalated_by', 'escalated_to', 'escalation_on', 'escalation_on_duration']
    template_name = 'project_management/update_escalation.html'
    success_url = reverse_lazy('tabProjectEscalation')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        esc_id = self.kwargs['pk']
        escalation_on = self.get_object().escalation_on
        escalation_on_duration = self.get_object().escalation_on_duration
        desc = self.get_object().description
        context['esc_id'] = esc_id
        context['escalation_on'] = escalation_on
        context['escalation_on_duration'] = escalation_on_duration
        context['desc'] = desc
        return context


def update_escation_level_update(request):
    esc_name = request.GET.get('esc_name')
    id_description = request.GET.get('id_description')
    id_escalate_on = request.GET.get('id_escalate_on')
    escsettingtogglebtn = request.GET.get('escsettingtogglebtn')
    id_project = int(request.GET.get('id_project'))
    esc_id = int(request.GET.get('esc_id'))
    pro_name = request.GET.get('pro_name')

    uid = request.user.id
    
    EscalationLevel.objects.filter(pk=int(esc_id)).update(name=esc_name, project_id=id_project, description=id_description, escalation_on=id_escalate_on, escalation_on_duration=escsettingtogglebtn)

    esc_levels = EscalationLevel.objects.filter(project_id=id_project).annotate(num_esc=Count('escalated_to'))
    template = loader.get_template('project_management/project_escalation_list.html')
    context = {
        'esc_levels': esc_levels,
        'projectid': id_project,
        'projectname': pro_name,
    }

    return HttpResponse(template.render(context, request))


def manage_escalated_users(request):
    esc_id = request.GET.get('esc_id')
    esc_name = request.GET.get('esc_name')
    pro_name = request.GET.get('pro_name')
    pro_id = request.GET.get('pro_id')

    esc_users = User.objects.filter(escalationlevel=int(esc_id))
    
    template = loader.get_template('project_management/list_escalated_users.html')
    context = {
        'esc_users': esc_users,
        'esc_id': esc_id,
        'esc_name': esc_name,
        'pro_name': pro_name,
        'pro_id': pro_id,
    }

    return HttpResponse(template.render(context, request))


def de_escalate_user(request):
    uid = request.GET.get('uid')
    esc_id = request.GET.get('esc_id')
    esc_name = request.GET.get('esc_name')
    pro_id = request.GET.get('pro_id')
    pro_name = request.GET.get('pro_name')

    esc_id2 = EscalationLevel.objects.get(id=int(esc_id))
    uid2 = User.objects.get(id=int(uid))
    esc_id2.escalated_to.remove(uid2)

    esc_users = User.objects.filter(escalationlevel=int(esc_id))
    
    template = loader.get_template('project_management/list_escalated_users.html')
    context = {
        'esc_users': esc_users,
        'esc_id': esc_id,
        'esc_name': esc_name,
        'pro_name': pro_name,
        'pro_id': pro_id,
    }

    return HttpResponse(template.render(context, request))

def escalate_user(request):
    uid = request.GET.get('uid')
    esc_id = request.GET.get('esc_id')
    esc_name = request.GET.get('esc_name')
    pro_id = request.GET.get('pro_id')
    pro_name = request.GET.get('pro_name')
    company_id = request.session['company_id']

    all_company_users = User.objects.filter(company_id=int(company_id))
    escalated_users = User.objects.filter(escalationlevel=int(esc_id))
    distinct_users = set(all_company_users).difference(set(escalated_users))

    template = loader.get_template('project_management/escalate_new_user.html')
    context = {
        'esc_users': distinct_users,
        'esc_id': esc_id,
        'esc_name': esc_name,
        'pro_name': pro_name,
        'pro_id': pro_id,
    }

    return HttpResponse(template.render(context, request))


def save_escalated_user(request):
    uid = request.GET.get('uid')
    esc_id = request.GET.get('esc_id')
    esc_name = request.GET.get('esc_name')
    pro_id = request.GET.get('pro_id')
    pro_name = request.GET.get('pro_name')

    esc_id2 = EscalationLevel.objects.get(id=int(esc_id))
    uid2 = User.objects.get(id=int(uid))
    esc_id2.escalated_to.add(uid2)

    esc_users = User.objects.filter(escalationlevel=int(esc_id))
    
    template = loader.get_template('project_management/list_escalated_users.html')
    context = {
        'esc_users': esc_users,
        'esc_id': esc_id,
        'esc_name': esc_name,
        'pro_name': pro_name,
        'pro_id': pro_id,
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
        incid_hist = {'name': j.title, 'history_type': j.history_type, 'created_by': j.history_user, 'history_date': j.history_date, 'state': 'Incident', 'project' : j.project}
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


def manage_sla_esclations(request):
    # project_id = request.GET.get('project_id')
    # print(project_id)

    # date_now = datetime.datetime.now(timezone.utc)
    # print('------------------------')
    # print(date_now)


    # if Incident.objects.all():
    #     for i in Incident.objects.all():
    #         print(i.close_time)
    #         state = i.status
    #         print(state)
    #         if state is not None:
    #             if i.status is not 'Completed':
    #                 print(i.resolution_time)
    #                 if i.close_time >= date_now:
    #                     print("------------Don't  Escalate. Ignore------------------")
    #                 else:
    #                     print('fetch escalation levels, calculate time when to escalte to who, send emails, ')
    #                     print("create a function for running escalations, with arg projectid, it counts  seconds and triggers an escalation")
    #                     print("------------- Escalate -------------------")

    # make_escalation(int(project_id))
    # template = loader.get_template('project_management/escalate_new_user.html')
    # context = {}

    # return HttpResponse(template.render(context, request))
    pass


def make_escalation(project_id):
    #Define the constants
    # SECONDS_PER_MINUTE  = 60
    # SECONDS_PER_HOUR    = 3600
    # SECONDS_PER_DAY     = 86400

    # for i in EscalationLevel.objects.filter(project=int(project_id)):
    #     print('-----------escalations-------------')
    #     print('--'+i.escalation_on_duration+'--')
        
    #     if i.escalation_on_duration == "Second(s)":
    #         print("Second(s)")

    #     if i.escalation_on_duration == "Minute(s)":
    #         print("Minute(s)")

    #     if i.escalation_on_duration == "Hour(s)":
    #         print("Hour(s)")

    #     if i.escalation_on_duration == "Day(s)":
    #         print("Day(s)")
    #         d_seconds = SECONDS_PER_DAY
    #         print(d_seconds)

    #     if i.escalation_on_duration == "Week(s)":
    #         print("Week(s)")

    #     if i.escalation_on_duration == "Month(s)":
    #         print("Month(s)")
        
    pass


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
            new_dict = {}
            new_dict['tim'] = tm
            daily_tm = Timesheet.objects.filter(log_day=tm, status='INITIAL', project_team_member_id=uid, company_id=company_id)
            new_dict['dictt'] = daily_tm
            sum_duration = 0 
            for ii in daily_tm:
	            sum_duration = sum_duration + ii.durationsec()
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
        'user_name' : User.objects.get(id=int(id_user_dept))
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
    uid = request.GET.get('uid')
    company_id = request.session['company_id']
    id_log_day = request.GET.get('id_log_day')
    id_task = request.GET.get('id_task')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    id_timesheet_notes = request.GET.get('notes')
    dept_uid = int(request.GET.get('uid'))

    log_day = datetime.datetime.strptime(id_log_day, '%d-%m-%Y')
    start_time1 = datetime.datetime.strptime(start_time, '%I:%M %p')
    end_time1 =   datetime.datetime.strptime(end_time, '%I:%M %p')
    
    obj = Timesheet(log_day=log_day, start_time=start_time1, end_time=end_time1, added_by_id=uid, task_id=int(id_task), project_team_member_id=dept_uid, company_id=int(company_id), last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=id_timesheet_notes)
    obj.save()

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
            new_dict = {}
            new_dict['tim'] = tm
            daily_tm = Timesheet.objects.filter(log_day=tm, status='INITIAL', project_team_member_id=dept_uid, company_id=company_id)
            new_dict['dictt'] = daily_tm

            sum_duration = 0 
            for ii in daily_tm:
                sum_duration = sum_duration + ii.durationsec()
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
    company_id = request.session['company_id']
    log_day = request.GET.get('log_day')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    task = request.GET.get('task')
    timesheet_id = int(request.GET.get('timesheet_id'))
    task_id = int(request.GET.get('task_id'))
    notes = request.GET.get('notes')
    id_user_dept = request.GET.get('id_user_dept')

    obj_task = Task.objects.get(id=int(task_id))
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

    return HttpResponse(template.render(context, request))

def update_timesheet_paginator(request):
    company_id = request.session['company_id']
    log_day = request.GET.get('log_day')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    task = request.GET.get('task')
    timesheet_id = int(request.GET.get('timesheet_id'))
    task_id = int(request.GET.get('task_id'))
    notes = request.GET.get('notes')
    id_user_dept = request.GET.get('id_user_dept')

    obj_task = Task.objects.get(id=int(task_id))
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

    return HttpResponse(template.render(context, request))


def resubmit_timesheet(request):
    company_id = request.session['company_id']
    log_day = request.GET.get('log_day')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    task = request.GET.get('task')
    timesheet_id = int(request.GET.get('timesheet_id'))
    task_id = int(request.GET.get('task_id'))
    notes = request.GET.get('notes')
    id_user_dept = int(request.GET.get('id_user_dept'))

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

    return HttpResponse(template.render(context, request))


def paginator_resubmit_timesheet(request):
    company_id = request.session['company_id']
    log_day = request.GET.get('log_day')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    task = request.GET.get('task')
    timesheet_id = int(request.GET.get('timesheet_id'))
    task_id = int(request.GET.get('task_id'))
    notes = request.GET.get('notes')
    id_user_dept = int(request.GET.get('id_user_dept'))

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

    return HttpResponse(template.render(context, request))


def save_update_timesheet(request):
    company_id = request.session['company_id']

    log_day = request.GET.get('id_log_day')
    dept_uid = int(request.GET.get('uid'))
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    task = int(request.GET.get('id_task'))
    timesheet_id = int(request.GET.get('timesheet_id'))
    notes = request.GET.get('notes')
    uid = request.user.id

    log_day = datetime.datetime.strptime(log_day, '%d-%m-%Y')
    start_time1 = datetime.datetime.strptime(start_time, '%I:%M %p')
    end_time1 =   datetime.datetime.strptime(end_time, '%I:%M %p')
    
    Timesheet.objects.filter(pk=int(timesheet_id)).update(log_day=log_day, start_time=start_time1, end_time=end_time1, task_id=task, last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=notes)

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
            new_dict = {}
            new_dict['tim'] = tm
            daily_tm = Timesheet.objects.filter(log_day=tm, status='INITIAL', project_team_member_id=dept_uid, company_id=company_id)
            new_dict['dictt'] = daily_tm

            sum_duration = 0 
            for ii in daily_tm:
                sum_duration = sum_duration + ii.durationsec()
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
    timesheet_id = request.GET.get('timesheet_id')
    Timesheet.objects.filter(id=int(timesheet_id)).delete()

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
            new_dict = {}
            new_dict['tim'] = tm
            daily_tm = Timesheet.objects.filter(log_day=tm, status='INITIAL', project_team_member_id=dept_uid, company_id=company_id)
            new_dict['dictt'] = daily_tm

            sum_duration = 0 
            for ii in daily_tm:
                sum_duration = sum_duration + ii.durationsec()
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
            new_dict = {}
            new_dict['tim'] = tm
            daily_tm = Timesheet.objects.filter(log_day=tm, status='INITIAL', project_team_member_id=id_user_dept, company_id=company_id)
            new_dict['dictt'] = daily_tm

            sum_duration = 0 
            for ii in daily_tm:
                sum_duration = sum_duration + ii.durationsec()
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

    timesheet_list1 = Timesheet.objects.filter(status='SUBMITTED', company_id=company_id, project_team_member_id=id_user_dept)

    template = loader.get_template('project_management/list_timesheets_pending_approval.html')
    context = {
        'timesheet_list': timesheet_list1,
    }

    return HttpResponse(template.render(context, request))


def approve_timesheet_pane(request):
    uid = request.user.id
    company_id = request.session['company_id']
    department_id = request.session['department_id']

    timesheet_list1 = Timesheet.objects.filter(status='SUBMITTED', company_id=company_id, project_team_member__department_id=department_id)

    template = loader.get_template('project_management/approve_timesheet_pane.html')
    context = {
        'timesheet_list': timesheet_list1,
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

    timesheet_list1 = Timesheet.objects.filter(Q(status='ACCEPTED')|Q(status='REJECTED'), company_id=company_id, project_team_member__department_id=department_id)

    template = loader.get_template('project_management/list_confirmed_timesheets.html')
    context = {
        'timesheet_list': timesheet_list1,
    }

    return HttpResponse(template.render(context, request))


def update_timesheet_approval(request):
    timesheet_id = request.GET.get('tm_id')
    new_status = request.GET.get('status_val')
    uid = request.user.id
    company_id = request.session['company_id']
    department_id = request.session['department_id']

    Timesheet.objects.filter(pk=int(timesheet_id)).update(status=new_status, last_updated_date=datetime.date.today(), last_updated_by_id=uid)

    timesheet_list1 = Timesheet.objects.filter(Q(status='ACCEPTED')|Q(status='REJECTED'), company_id=company_id, project_team_member__department_id=department_id)
    template = loader.get_template('project_management/list_confirmed_timesheets.html')
    context = {
        'timesheet_list': timesheet_list1,
    }

    return HttpResponse(template.render(context, request))


def view_user_approved_timesheets(request):
    id_user_dept = request.GET.get('id_user_dept')
    company_id = request.session['company_id']

    timesheet_list1 = Timesheet.objects.filter(Q(status='ACCEPTED'), company_id=company_id, project_team_member_id=id_user_dept)

    template = loader.get_template('project_management/list_user_accepted_timesheets.html')
    context = {
        'timesheet_list': timesheet_list1,
    }

    return HttpResponse(template.render(context, request))


def manage_rejected_timesheets(request):
    id_user_dept = request.GET.get('id_user_dept')
    company_id = request.session['company_id']

    timesheet_list1 = Timesheet.objects.filter(Q(status='REJECTED'), company_id=company_id, project_team_member_id=id_user_dept)

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

    timesheet_list1 = Timesheet.objects.filter(status='SUBMITTED', company_id=company_id, log_day__range=(min_dt, max_dt), project_team_member_id=uid)

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
    
    timesheet_list1 = Timesheet.objects.filter(Q(status='ACCEPTED')|Q(status='REJECTED'), company_id=company_id, project_team_member_id=uid, log_day__range=(min_dt, max_dt))

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

    startdate = datetime.datetime.strptime(start_date1, '%d-%m-%Y')
    enddate = datetime.datetime.strptime(end_date1, '%d-%m-%Y')

    min_dt = datetime.datetime.combine(startdate, datetime.time.min)
    max_dt = datetime.datetime.combine(enddate, datetime.time.max)
        
    timesheet_list1 = Timesheet.objects.filter(Q(status='ACCEPTED')|Q(status='REJECTED'), company_id=company_id, log_day__range=(min_dt, max_dt))

    template = loader.get_template('project_management/list_confirmed_timesheets.html')
    context = {
        'timesheet_list': timesheet_list1,
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

    log_day = request.GET.get('id_log_day')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    task = int(request.GET.get('id_task'))
    timesheet_id = int(request.GET.get('timesheet_id'))
    notes = request.GET.get('notes')
    comment = request.GET.get('comment')
    uid = request.user.id
    id_user_dept = int(request.GET.get('id_user_dept'))

    log_day = datetime.datetime.strptime(log_day, '%d-%m-%Y')
    start_time1 = datetime.datetime.strptime(start_time, '%I:%M %p')
    end_time1 =   datetime.datetime.strptime(end_time, '%I:%M %p')
    
    Timesheet.objects.filter(pk=int(timesheet_id)).update(status='SUBMITTED', log_day=log_day, start_time=start_time1, end_time=end_time1, task_id=task, last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=notes, is_resubmitted=True)
    
    obj1 = ResubmittedTimesheet(comment=comment, resubmitted_by_id=uid, timesheet_id=int(timesheet_id))
    obj1.save()

    timesheet_list1 = Timesheet.objects.filter(Q(status='REJECTED'), company_id=company_id, project_team_member_id=id_user_dept)
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
    
    Timesheet.objects.filter(pk=int(tm_id)).update(last_updated_date=datetime.date.today(), last_updated_by_id=uid, approver_notes=appr_comment)

    timesheet_list1 = Timesheet.objects.filter(Q(status='ACCEPTED')|Q(status='REJECTED'), company_id=company_id)
    template = loader.get_template('project_management/list_confirmed_timesheets.html')
    context = {
        'timesheet_list': timesheet_list1,
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

    project_list = Project.objects.filter(company=int(company_id))
    
    template = loader.get_template('project_management/add_new_calender_timesheet.html')
    context = {
        'project_list': project_list,
        'log_date': datetime.datetime.strptime(log_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
        'user_id' : id_user_dept,
        'user_name' : User.objects.get(id=int(id_user_dept))
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
    uid = request.user.id
    company_id = request.session['company_id']
    id_log_day = request.GET.get('id_log_day')
    id_task = request.GET.get('id_task')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    id_timesheet_notes = request.GET.get('notes')
    id_dept_user = int(request.GET.get('uid'))

    log_day = datetime.datetime.strptime(id_log_day, '%d-%m-%Y')
    start_time1 = datetime.datetime.strptime(start_time, '%I:%M %p')
    end_time1 =   datetime.datetime.strptime(end_time, '%I:%M %p')
    
    obj = Timesheet(log_day=log_day, start_time=start_time1, end_time=end_time1, added_by_id=uid, task_id=int(id_task), project_team_member_id=id_dept_user, company_id=int(company_id), last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=id_timesheet_notes)
    obj.save()

    timesheet_list1 = Timesheet.objects.filter(log_day=log_day, company_id=company_id, project_team_member_id=id_dept_user)
    
    if Timesheet.objects.filter(log_day=log_day, status='INITIAL', company_id=company_id, project_team_member_id=id_dept_user).exists():
        intial_state = True
    else:
        intial_state = False
    
    sum_duration = 0 
    for ii in timesheet_list1:
        sum_duration = sum_duration + ii.durationsec()
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
   
    timesheetdetails = Timesheet.objects.get(id=int(timesheet_id))
    template = loader.get_template('project_management/calender_timesheet_details.html')
    context = {
        'timesheetdetails': timesheetdetails
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

    timesheet_list1 = Timesheet.objects.filter(log_day=log_day, company_id=company_id, project_team_member_id=id_user_dept)

    if Timesheet.objects.filter(log_day=log_day, status='INITIAL', company_id=company_id, project_team_member_id=id_user_dept).exists():
        intial_state = True
    else:
        intial_state = False

    sum_duration = 0 
    for ii in timesheet_list1:
        sum_duration = sum_duration + ii.durationsec()
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
            new_dict = {}
            new_dict['tim'] = tm
            daily_tm = Timesheet.objects.filter(log_day=tm, status='INITIAL', project_team_member_id=uid, company_id=company_id)
            new_dict['dictt'] = daily_tm
            sum_duration = 0 
            for ii in daily_tm:
	            sum_duration = sum_duration + ii.durationsec()
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

    timesheet_list1 = Timesheet.objects.filter(log_day=log_day, company_id=company_id, project_team_member_id=id_user_dept)

    if Timesheet.objects.filter(log_day=log_day, status='INITIAL', company_id=company_id, project_team_member_id=id_user_dept).exists():
        intial_state = True
    else:
        intial_state = False
    
    sum_duration = 0 
    for ii in timesheet_list1:
        sum_duration = sum_duration + ii.durationsec()
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
    dateSelected = request.GET.get('dateSelected')
    id_user_dept = int(request.GET.get('id_user_dept'))
    log_day = datetime.datetime.strptime(dateSelected, '%Y-%m-%d')

    timesheet_id = request.GET.get('timesheet_id')
    Timesheet.objects.filter(id=int(timesheet_id)).delete()

    timesheet_list1 = Timesheet.objects.filter(log_day=log_day, company_id=company_id, project_team_member_id=id_user_dept)

    if Timesheet.objects.filter(log_day=log_day, status='INITIAL', company_id=company_id, project_team_member_id=id_user_dept).exists():
        intial_state = True
    else:
        intial_state = False

    sum_duration = 0 
    for ii in timesheet_list1:
        sum_duration = sum_duration + ii.durationsec()
    tm_day_duration = compute_duration(sum_duration)

    template = loader.get_template('project_management/list_date_timesheet.html')
    context = {
        'timesheet_list': timesheet_list1,
        'initial_status': intial_state,
        'tm_day_duration': tm_day_duration
    }
    return HttpResponse(template.render(context, request))


def save_update_paginator_timesheet(request):
    dateSelected = request.GET.get('dateSelected')
    log_day = datetime.datetime.strptime(dateSelected, '%Y-%m-%d')
    company_id = request.session['company_id']

    id_user_dept = int(request.GET.get('id_user_dept'))
    log_day = request.GET.get('id_log_day')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    task = int(request.GET.get('id_task'))
    timesheet_id = int(request.GET.get('timesheet_id'))
    notes = request.GET.get('notes')
    uid = request.user.id

    log_day = datetime.datetime.strptime(log_day, '%d-%m-%Y')
    start_time1 = datetime.datetime.strptime(start_time, '%I:%M %p')
    end_time1 =   datetime.datetime.strptime(end_time, '%I:%M %p')
    
    Timesheet.objects.filter(pk=int(timesheet_id)).update(log_day=log_day, start_time=start_time1, end_time=end_time1, task_id=task, last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=notes)

    timesheet_list1 = Timesheet.objects.filter(log_day=log_day, company_id=company_id, project_team_member_id=id_user_dept)

    if Timesheet.objects.filter(log_day=log_day, status='INITIAL', company_id=company_id, project_team_member_id=id_user_dept).exists():
        intial_state = True
    else:
        intial_state = False

    sum_duration = 0 
    for ii in timesheet_list1:
        sum_duration = sum_duration + ii.durationsec()
    tm_day_duration = compute_duration(sum_duration)

    template = loader.get_template('project_management/list_date_timesheet.html')
    context = {
        'timesheet_list': timesheet_list1,
        'initial_status': intial_state,
        'tm_day_duration': tm_day_duration
    }

    return HttpResponse(template.render(context, request))


def save_resent_paginator_timesheet(request):
    dateSelected = request.GET.get('dateSelected')
    selected_day = datetime.datetime.strptime(dateSelected, '%Y-%m-%d')

    company_id = request.session['company_id']

    log_day = request.GET.get('id_log_day')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    task = int(request.GET.get('id_task'))
    timesheet_id = int(request.GET.get('timesheet_id'))
    notes = request.GET.get('notes')
    comment = request.GET.get('comment')
    uid = request.user.id
    id_user_dept = int(request.GET.get('uid'))

    log_day = datetime.datetime.strptime(log_day, '%d-%m-%Y')
    start_time1 = datetime.datetime.strptime(start_time, '%I:%M %p')
    end_time1 =   datetime.datetime.strptime(end_time, '%I:%M %p')
    
    Timesheet.objects.filter(pk=int(timesheet_id)).update(status='SUBMITTED', log_day=log_day, start_time=start_time1, end_time=end_time1, task_id=task, last_updated_date=datetime.date.today(), last_updated_by_id=uid, notes=notes, is_resubmitted=True)
    
    obj1 = ResubmittedTimesheet(comment=comment, resubmitted_by_id=uid, timesheet_id=int(timesheet_id))
    obj1.save()

    timesheet_list1 = Timesheet.objects.filter(log_day=selected_day, company_id=company_id, project_team_member_id=id_user_dept)
    
    if Timesheet.objects.filter(log_day=log_day, status='INITIAL', company_id=company_id, project_team_member_id=id_user_dept).exists():
        intial_state = True
    else:
        intial_state = False
    
    sum_duration = 0 
    for ii in timesheet_list1:
        sum_duration = sum_duration + ii.durationsec()
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
    else:
        all_member_tms = ''
        days_list = ''

    template = loader.get_template('project_management/list_project_timesheet_by_week.html')
    context = {
        'timesheet_list': final_list,
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
            new_dict = {}
            new_dict['tim'] = tm
            daily_tm = Timesheet.objects.filter(log_day=tm, status='INITIAL', project_team_member_id=uid, company_id=company_id)
            new_dict['dictt'] = daily_tm
            sum_duration = 0 
            for ii in daily_tm:
	            sum_duration = sum_duration + ii.durationsec()
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
    # timesheets = Timesheet.objects.filter(submitted_by=request.user.id)
    
    # end_time = []
    # start_time = []
    # for object in timesheets:

    #     difference = object.durationsec()

    #     total_hours = difference / 3600
    #     end_time.append(total_hours)

    # print(f"{end_time} is the end")

    # sum_list = sum(end_time)

    # print(f"The difference is {sum_list}")

    # return render(request, 'project_management/staff_report.html', {
    #     'total': str(sum_list),
    #     'timesheets': timesheets,
    #     'user': request.user
    #     })
    


    return render(request, 'project_management/staff_report.html', context=None)
    

def render_calendar(request):
    """ returns timesheet values for single individual """
    company_id = request.session['company_id']

    start_time = request.GET.get('start', None)
    end_time = request.GET.get('end', None)

    print(f"{start_time} is the start")
    print(f"{end_time} is the end time")

    convert_start = datetime.datetime.strptime(start_time, "%d-%m-%Y").strftime("%Y-%m-%d")
    convert_end = datetime.datetime.strptime(end_time, "%d-%m-%Y").strftime("%Y-%m-%d")

    new_start = datetime.datetime.strptime(convert_start, "%Y-%m-%d")
    new_end = datetime.datetime.strptime(convert_end, "%Y-%m-%d")

    start = date(new_start.year, new_start.month, new_start.day)
    end = date(new_end.year, new_end.month, new_end.day)
    
    # getting the days in between start date and end date
    delta = end - start
    
    timesheet = Timesheet.objects.filter(company_id=company_id)
    list_timesheet_user = []
    all_users = User.objects.filter(company_id=company_id)
    days_list = []

    for time in timesheet:
        logged_day = time.log_day.strftime("%Y-%m-%d")
        timesheet_dict = {}
        users = User.objects.filter(id= time.added_by.id)

        for user in users:
            timesheet_dict["user"] = user.last_name
            timesheet_dict["user_id"] = user.id

            for i in range(delta.days + 1):
                day = start + timedelta(days=i)
                new_day = day.strftime("%Y-%m-%d")           

                if new_day == logged_day:
                    duration_in_seconds = time.durationsec()
                    duration_in_hours = duration_in_seconds/3600
                    timesheet_dict["user_hours"] = duration_in_hours
                    list_timesheet_user.append(timesheet_dict)
                

    #  getting the user total time 
    print(list_timesheet_user)
    # sum_list = sum(list_timesheet_user)
    # final_list = round(sum_list, 2)

    user_list = []
    for user in all_users:
        hours = 0
        user_dict = {}
        for obj in list_timesheet_user:
            print(f"{obj} is the one")
            if user.id == obj['user_id']:
                hours += obj['user_hours']
                
            user_dict['user_id'] = user.id
            user_dict['first_name'] = user.first_name
            user_dict['last_name'] = user.last_name
            user_dict['hours'] = hours
            
        user_list.append(user_dict)

    
    print(user_list) 
    list_users = json.dumps(user_list)
    print(f"{list_users} is the list of users")
    return JsonResponse(list_users)


def daily_logged_hours(request):
    """daily logged hours"""

    return render(request, 'project_management/daily_logged_hours.html', context=None)


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
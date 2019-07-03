import csv, io, xlwt
import xlsxwriter
import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, HttpResponse
from django.template.loader import get_template
from django.core.mail import EmailMessage
from static.fusioncharts import FusionCharts
from django.template import loader
from django.core import serializers


from django.contrib.auth.decorators import user_passes_test, permission_required

from .models import Project, Milestone, Task, ProjectDocument, Incident, Priority, Status, ProjectTeam, ProjectTeamMember, Role, ProjectForumMessages, ProjectForum, ProjectForumMessageReplies, ServiceLevelAgreement, IncidentComment, EscalationLevel, IncidentComment
from user_management.models import User
from company_management.models import Company, CompanyCategory
from .forms import CreateProjectForm, MilestoneForm, TaskForm, DocumentForm, ProjectUpdateForm, MilestoneUpdateForm, ProjectForm, IncidentForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.db.models import Count
import json


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
    project_id = request.GET.get('project')
    documents = ProjectDocument.objects.all
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
        start = form.cleaned_data['startdate']
        finish = form.cleaned_data['enddate']
        current_user = self.request.user
        name = current_user.username
        
        milestone = Milestone(name=milestone_name, project=project, startdate=start, enddate=finish, creator=current_user)
        milestone.save()

        context = {
            'name': name,
            'milestone_name': milestone_name,
            'project': project,
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
        # mail_to_send.send()

        return HttpResponseRedirect('/projectManagement/milestones')

    success_url = reverse_lazy('milestones')


class MilestoneListView(ListView):
    context_object_name = 'milestones'

    def get_queryset(self):
        return Milestone.objects.all()


# class AddMilestone(LoginRequiredMixin, CreateView):
#     model = Milestone
#     fields = ['name', 'status', 'startdate', 'enddate', 'description',]
#     template_name = 'project_management/add_project_milestone.html'
#     success_url = reverse_lazy('listProjectMilestones')

#     def form_valid(self, form):
#         """auto registering loggedin user"""
#         form.instance.creator = self.request.user
#         return super().form_valid(form)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         project_id = int(self.request.GET['project_id'])
#         context['project_id'] = project_id
#         print(context)
#         return context


def milestone_list_by_project(request, project_id):
    project_milestones = Milestone.objects.filter(project_id=project_id)
    return render(request, 'project_management/milestone_list.html', {'milestones': project_milestones})


def populate_milestone_view(request):
    """
    populate project_milestone view
    """
    project_id = request.GET.get('project_id')
    project_name = request.GET.get('project_name')
      
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
    data = {
        'is_taken': Milestone.objects.filter(name=milestone_name).exists()
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
    project_id = request.GET.get('project_id')
    project_name = request.GET.get('project_name')
    name = request.GET.get('name')
    description = request.GET.get('description')
    status_id = request.GET.get('status_id')
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')
    actual_start = request.GET.get('actual_start')
    actual_end = request.GET.get('actual_end')
    creator = request.user.id

    if status_id == "":
        status_id = None

    if end != "null":
        end = datetime.datetime.strptime(end, "%m/%d/%Y").strftime("%Y-%m-%d")
    else:
        end = None

    if start != "null":
        start = datetime.datetime.strptime(start, "%m/%d/%Y").strftime("%Y-%m-%d")
    else:
        start = None

    if actual_start != "null":
        actual_start = datetime.datetime.strptime(actual_start, "%m/%d/%Y").strftime("%Y-%m-%d")
    else:
        actual_start = None

    if actual_end != "null":
        actual_end = datetime.datetime.strptime(actual_end, "%m/%d/%Y").strftime("%Y-%m-%d")
    else:
        actual_end = None

    if Milestone.objects.filter(name=name).exists():
        milestone = Milestone.objects.get(name=name)
        response_data = {
            'error': "Name exists",
            'name': milestone.name,
            'state':False
        }
    
    else:
        milestone = Milestone(name=name, description=description, project_id=project_id, creator_id=creator, startdate=start, enddate=end, status_id=status_id, actual_startdate=actual_start, actual_enddate=actual_end )
        milestone.save()

        response_data ={
            'success': "Milestone saved successfully",
            'name': milestone.name,
            'state':True
        }

    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json"
    )
    

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
    fields = ['name', 'status', 'description', 'startdate', 'enddate', 'actual_startdate', 'actual_enddate', ]
    template_name = 'project_management/update_project_milestone.html'
    success_url = reverse_lazy('listProjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        milestone_id = int(self.request.GET['milestone_id'])
        context['milestone_id'] = milestone_id
        return context


def list_project_milestones(request):
    """
    list project specific milestones
    """
    project_id = request.GET.get('project_id')

    project = Project.objects.get(id=project_id)

    template = loader.get_template('project_management/list_project_milestones.html')

    milestones_exist = Milestone.objects.filter(project_id=project.id).exists()
    if milestones_exist:
        milestones = Milestone.objects.filter(project_id=project.id)

        context = {
            'project_id': project.id,
            'project_name': project.name,
            'milestones': milestones
        }

        return HttpResponse(template.render(context, request))

    else:
        context = {
            'project_id': project.id,
            'project_name': project.name,
            'milestones': ''
        }

        return HttpResponse(template.render(context, request))   


def view_tasks_under_milestone(request):
    milestone_id = request.GET.get('milestone_id')
    project_id = request.GET.get('project_id')

    template = loader.get_template('project_management/list_milestone_tasks.html')
    project = get_object_or_404(Project, pk=project_id)
    
    milestone_exists = Milestone.objects.filter(id=milestone_id, project_id=project.id).exists()
    if milestone_exists:
        milestone = Milestone.objects.get(id=milestone_id)
        milestone_tasks = Task.objects.filter(milestone_id=milestone.id)
        statuses = Status.objects.all()

        context = {
            'milestone_name': milestone.name,
            'milestone_id': milestone.id,
            'milestone_tasks': milestone_tasks,
            'project_id': project.id,
            'statuses': statuses
        }

        return HttpResponse(template.render(context, request))


def add_milestone_specific_task(request):
    project_id = request.GET.get('project_id')
    milestone_id = request.GET.get('milestone_id')

    project = Project.objects.get(id=project_id)

    milestone = Milestone.objects.get(id=milestone_id)

    template = loader.get_template('project_management/add_milestone_task.html')
    context = {
        'project_id': project_id,
        'project_name':project.name,
        'milestone_id': milestone_id,
        'milestone_name': milestone.name   
    }

    return HttpResponse(template.render(context, request))


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


def populate_task_view(request):
    """
    populate project_task view
    """
    project_id = request.GET.get('project_id')
    project_name = request.GET.get('project_name')
     
    template = loader.get_template('project_management/add_project_tasks.html')
    context = {
        'project_id': project_id,
        'project_name': project_name
    }

    return HttpResponse(template.render(context, request))


def populate_status_milestone(request):
    """
    populate status and milestone in task view
    """
    project_id = request.GET.get('project_id')
    project_name = request.GET.get('project_name')
    
    project = Project.objects.get(id=project_id)

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
        'status': serializers.serialize("json", status),
        'milestones': serializers.serialize("json", milestones),
        'members': serializers.serialize('json', old)
    }

    return JsonResponse(data)
    

# def add_project_tasks(request):
#     project_id = request.GET.get('project_id')
#     print(f"{project_id} is ssdjkalsdfa")
#     project = get_object_or_404(Project, pk=project_id)

#     milestones_exist = Milestone.objects.filter(project_id=project.id).exists()
#     all_statuses = Status.objects.all()
#     if milestones_exist:
#         milestones = Milestone.objects.filter(project_id=project.id)
        
#         data = {
#             'milestones': serializers.serialize("json", milestones),
#             'statuses': serializers.serialize("json", all_statuses)
#         }
        
#         return JsonResponse(data)

#     else:
#         data = {
#             'milestones': '',
#             'statuses': serializers.serialize("json", all_statuses)
#         }

#         return JsonResponse(data)


def add_milestone_tasks(request):
    project_id = request.GET.get('project_id')
    print(f"{project_id} is ssdjkalsdfa")
    project_name = request.GET.get('project_name')
    
    project = Project.objects.get(id=project_id)

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
        'milestones': serializers.serialize("json", milestones),
        'members': serializers.serialize('json', old)
    }

    return JsonResponse(data)


def validateTaskName(request):
    """
    check if name already exists
    """
    task_name = request.GET.get('task_name', None)
    data = {
        'is_taken': Task.objects.filter(name=task_name).exists()
    }
    return JsonResponse(data)


def save_project_tasks(request):
    """
    save project tasks
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
    assigned_to = request.GET.get('assigned_to')

    response_data = {}

    if assigned_to == "":
        assigned_to = None
    else:
        team = ProjectTeam.objects.get(project_id= project_id)
        team_member = ProjectTeamMember.objects.get(member_id=assigned_to, project_team=team)
        
        assigned_to = team_member.id

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
    
    milestone = Milestone.objects.get(id=milestone_id, project_id=project.id)
    
    if Task.objects.filter(name=name).exists():
        response_data['error'] = "Name exists"
        response_data['state'] = False
    else:   
        task = Task(name=name, description=description, status_id=status_id, milestone_id=milestone.id, project_id=project.id, start_date=start_date, end_date=end_date, creator_id=created_by, assigned_to_id=assigned_to, actual_start_date=actual_start , actual_end_date=actual_end)
        task.save()

        response_data['success'] = "Task created successfully"
        response_data['name'] = task.name
        response_data['state'] = True

    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json"
    )
    

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
    created_by = request.user.id

    print(f"chineke me {created_by}")
    print(f"descriptoin is {description}")
    print(f"name is {name}")    
    print(f"status is {status_id}")
    print(f"start_date is {start_date}")
    print(f"end_date is {end_date}")
    print(f"milestone_id is {milestone_id}")
    print(f"project_id is {project_id}")

    response_data = {}

    if status_id == "":
        status_id = None

    if description == "":
        description = None

    if start_date == "":
        start_date = None

    if end_date == "":
        end_date = None

    if start_date != "":
        start_date = datetime.datetime.strptime(start_date, "%m/%d/%Y").strftime("%Y-%m-%d")

    if end_date != "":
        end_date = datetime.datetime.strptime(end_date, "%m/%d/%Y").strftime("%Y-%m-%d")

    project = Project.objects.get(id=project_id)
    
    milestone = Milestone.objects.get(id=milestone_id, project_id=project.id)
    
    if Task.objects.filter(name=name).exists():
        response_data['error'] = "Name exists"
        response_data['state'] = False
    else:   
        task = Task(name=name, description=description, status_id=status_id, milestone_id=milestone.id, project_id=project.id, start_date=start_date, end_date=end_date, creator_id=created_by)
        task.save()

        response_data['success'] = "Task created successfully"
        response_data['name'] = task.name
        response_data['state'] = True


    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json"
    )


class UpdateProjectTask(UpdateView):
    model = Task
    fields = ['name', 'status', 'description', 'start_date', 'end_date', 'actual_start_date', 'actual_end_date', 'assigned_to']
    template_name = 'project_management/update_project_task.html'
    success_url = reverse_lazy('listProjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_id = int(self.request.GET['task_id'])
        project_id = int(self.request.GET['project_id'])
        context['task_id'] = task_id

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


class UpdateMilestoneTask(UpdateView):
    model = Task
    fields = ['name', 'status', 'description', 'start_date', 'end_date', 'actual_start_date', 'actual_end_date', ]
    template_name = 'project_management/update_milestone_task.html'
    success_url = reverse_lazy('listProjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_id = int(self.request.GET['task_id'])
        context['task_id'] = task_id
        return context


def tasklist_by_project(request):
    """
    Tasks allocated to project
    """
    project_id = request.GET.get('project_id')
    project = get_object_or_404(Project, pk=project_id)

    template = loader.get_template('project_management/list_project_tasks.html')

    tasks = Task.objects.filter(project_id= project_id).exists()
    
    if tasks:
        project_tasks = Task.objects.filter(project_id=project.id)

        context = {
            'project_name': project.name,
            'project_id': project.id,
            'tasks': project_tasks
        }

        return HttpResponse(template.render(context, request))

    else:
        context = {
            'project_name': project.name,
            'project_id': project.id,
            'tasks': ''
        }

        return HttpResponse(template.render(context, request))


class DetailsProjectTask(DetailView):
    model = Task
    context_name = 'task'
    template_name = 'project_management/details_project_tasks.html'


class TaskListView(ListView):
    template_name = 'project_management/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.all()


# def task_list_by_project(request, project_id):
#     project_tasks = Task.objects.filter(project_id=project_id)
#     return render(request, 'project_management/task_list.html', {'tasks': project_tasks})


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


def change_status_on_task(request, pk):
    """update incident status if incident is linked to task"""
    task_status = request.GET.get('status')
    
    print("task status is "+task_status)
    print("task id is "+str(pk))

    incident_exists = Incident.objects.filter(task_id=pk).exists()
    
    if incident_exists == True:
        incident = Incident.objects.get(task_id=pk)
        updateIncidentStatus = Incident.objects.filter(pk=incident.id).update(status=task_status)
    else:
        print("no about to reach there")


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
        team_members = ProjectTeamMember.objects.filter(project_team=int(team_id))
        if team_members:
            if Incident.objects.filter(project_id=project.id).exists():
                team_member = ProjectTeamMember.objects.filter(member=request.user, project_team=team_id)
                
                incidents = Incident.objects.filter(Q(creator=request.user)|Q(assignee__in=team_member), project_id=project.id).annotate(assigned=Count('assignee', distinct=True))
                state = True
                context = {
                    'project_id': project.id,
                    'project_name': project.name,
                    'incidents': incidents,
                    'state': state
                }

                return HttpResponse(template.render(context, request))
        
            else:
                state=True
                context={
                    'project_id': project.id,
                    'project_name': project.name,
                    'incidents': '',
                    'state': state
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
    fields = ['project', 'title', 'description', 'document', 'image', 'status', 'priority', 'assignee']
    template_name = 'project_management/update_incident.html'
    success_url = reverse_lazy('listIncidents')


class UpdateProjectIncident(UpdateView):
    model = Incident
    fields = ['title', 'description', 'document', 'image', 'status', 'priority', 'assignee', 'task', 'resolution_time']
    template_name = 'project_management/update_project_incident.html'
    success_url = reverse_lazy('listIncidents')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        incident_id = int(self.request.GET['incident_id'])
        context['incident_id'] = incident_id
        return context

    # def get_success_url(self):
    #     return reverse_lazy('listProjectIncidents', kwargs={'pk': self.object.project_id})


def get_team_members(request):
    """display team members on incident assigning"""

    project_id = request.GET.get('project')

    team = ProjectTeam.objects.filter(project_id=project_id).exists()

    if team == True:
        project_team = ProjectTeam.objects.get(project_id=project_id)
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
        priority = Priority.objects.get(id=priority_id)
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
        document_form = DocumentForm(request.FILES)

        if project_form.is_valid():
            data = request.POST.copy()
            name = data.get('name')
            description = data.get('description')
            project_code = data.get('project_code')
            estimated_cost = data.get('estimated_cost')
            logo = request.FILES['logo']
            start_date = data.get('estimated_start_date')
            end_date = data.get('estimated_end_date')
            project_status = data.get('project_status')
            created_by = request.user.id

            # converting date to yyyy-mm-dd format to save to db
            estimated_start_date = datetime.datetime.strptime(start_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            estimated_end_date = datetime.datetime.strptime(end_date, "%m/%d/%Y").strftime("%Y-%m-%d")

            status = Status.objects.get(id=project_status)
            user_id = User.objects.get(id=created_by)

            project = Project(name=name, description=description, project_code=project_code, estimated_cost=estimated_cost,
            logo=logo, estimated_start_date=estimated_start_date, estimated_end_date=estimated_end_date,
            project_status=status, created_by=user_id)

            project.save()

            # project_id = Project.objects.get(pk=project.id)

            # if project:
            #     # save project document information
            #     form = request.POST.copy()
            #     if form.is_valid():
            #         title = form.get('title')
            #         description = form.get('description')
            #         creator = request.user.id
            #         user = User.objects.get(id=creator)
            #         document = request.FILES['document']
            #         doc = ProjectDocument(title=title, description=description, project=project_id, document=document, created_by=user)
            #         doc.save()
                
            return redirect('listProjects')
    else:
        project_form = ProjectForm()
        # document_form = DocumentForm()

    return render(request, 'project_management/add_project.html', {
            'project_form': project_form,
            # 'document_form': document_form
    })


class ListProjects(ListView):
    template_name = 'project_management/list_projects.html'
    context_object_name = 'all_projects'

    def get_queryset(self):
        return Project.objects.all()


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

        if Milestone.objects.filter(project_id=project_id).exists():
            milestone_status = True
        else:
            milestone_status = False
        
        context['milestone_status'] = milestone_status

        if ProjectTeam.objects.filter(project_id=project_id).exists():
            obj1 = ProjectTeam.objects.filter(project_id=project_id).values('id').first()
            project_team_id = obj1['id']

            if ProjectTeamMember.objects.filter(project_team=project_team_id, member_id=self.request.user.id).exists():
                forum_status = True
                incident_status = True
            else:
                forum_status = False
                incident_status = False
        else:
            forum_status = False
            incident_status = False

        context['forum_status'] = forum_status
        context['incident_status'] = incident_status
        return context


def validateProjectName(request):
    project_name = request.GET.get('projectname', None)
    data = {
        'is_taken': Project.objects.filter(name=project_name).exists()
    }
    return JsonResponse(data)


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
        'success': 'Member added successfully',
        'state': True,
        "name": team_member.member_id
    }
    
    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json"
    )
    

class AddProjectTeamMember(CreateView):
    """
    admin view for adding project team member
    """
    model = ProjectTeamMember
    template_name = 'project_management/add_project_team_member.html'
    fields = ['member', 'project_team', 'responsibility']
    success_url = reverse_lazy('listProjectTeams')


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


def remove_project_team_member(request):
    team_id = request.GET.get('teamid')
    team_name = request.GET.get('teamname')
    member_id = request.GET.get('memberid')

    teamid = ProjectTeam.objects.get(id=int(team_id))
    memberid = ProjectTeamMember.objects.get(id=int(member_id))
    memberid.project_team.remove(teamid)


    team = ProjectTeamMember.objects.filter(project_team=int(team_id))
    template = loader.get_template('project_management/details_team_member.html')
    context = {
        'team': team,
        'team_name': team_name,
        'team_id': team_id,
    }

    return HttpResponse(template.render(context, request))


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
        context['sla_id'] = sla_id
        context['response_time'] = response_time
        context['resolution_time'] = resolution_time
        context['resolution_duration'] = resolution_duration
        context['response_duration'] = response_duration
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

    ServiceLevelAgreement.objects.filter(pk=int(sla_id)).update(name=sla_name, description=id_description, response_time=id_response_time,
        resolution_time=id_resolution_time, resolution_duration=settingtoggleresoln, response_duration=settingtoggleresp,  project_id=int(id_project))
    
    slas = ServiceLevelAgreement.objects.filter(project_id=int(id_project)).first()
    status = True
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
    fields = ['name', 'project','description', 'escalated_by', 'escalated_to', 
                    'escalation_on', 'escalation_on_duration']

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
    print('fffff')
    print(escalated_users)
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
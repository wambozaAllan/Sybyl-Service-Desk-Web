import csv, io, xlwt
import xlsxwriter

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

from django.contrib.auth.decorators import user_passes_test, permission_required

from .models import Project, Milestone, Task, ProjectDocument, Incident, Priority, Status, ProjectTeam, \
    ProjectTeamMember, Role
from user_management.models import User
from company_management.models import Company
from .forms import CreateProjectForm, MilestoneForm, TaskForm, DocumentForm, ProjectUpdateForm, MilestoneUpdateForm
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
            project           = form.cleaned_data['project'].id
            form.save()
            return redirect('%d/'%project)
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
        context                 = super(ProjectDetailView, self).get_context_data(**kwargs)
        context['milestones']   = Milestone.objects.filter(project_id=self.kwargs.get('pk'))
        context['tasks']        = Task.objects.filter(project_id=self.kwargs.get('pk'))
        context['incidents']    = Incident.objects.filter(project_id=self.kwargs.get('pk'))
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

    response    = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="projects.csv"'

    writer = csv.writer(response)
    writer.writerow(['Project Name', 'Description', 'Client', 'Start Date', 'End Date', 'Project Manager', 'Status', 'Vendor', 'Completion', 'Cost'])

    for obj in items:
        writer.writerow([obj.name, obj.description, obj.client, obj.startdate,obj.enddate, obj.project_manager, obj.project_status, obj.vendor, obj.completion, obj.estimated_cost])

    return response


def export_projects_xls(request):
    import xlwt
    queryset = Project.objects.all()
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Projects.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("Projects")

    row_num = 1

    columns = [(u"Project Name", 5000),(u"Description", 5000),(u"Client", 5000),
        (u"Start Date", 5000),(u"End Date", 5000),(u"Project Manager", 5000),
        (u"Status", 5000),(u"Vendor", 5000),(u"Cost", 5000)
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


class MilestoneCreateView(LoginRequiredMixin,CreateView):
    model = Milestone
    form_class = MilestoneForm

    def form_valid(self, form):
        milestone_name  = form.cleaned_data['name']
        project         = form.cleaned_data['project']
        start           = form.cleaned_data['startdate']
        finish          = form.cleaned_data['enddate']
        current_user    = self.request.user
        name            = current_user.username
        form.save()
        cxt = {
            'name'              :name,
            'milestone_name'    :milestone_name,
            'project'           :project,
            'startdate'         :start,
            'enddate'           :finish,
        }

        subject                         = 'New Milestone | Action Required'
        message                         = get_template('mails/new_milestone_email.html').render(cxt)
        email_from                      = settings.EMAIL_HOST_USER
        recipient_list                  = [current_user.email,'ampumuzadickson@gmail.com']
        mail_to_send                    = EmailMessage(subject, message, to=recipient_list, from_email=email_from)
        mail_to_send                    = EmailMessage(subject, message, to=recipient_list, from_email=email_from)
        mail_to_send.content_subtype    = 'html'
        #mail_to_send.send()

        return HttpResponseRedirect('/projectManagement/milestones')
    success_url = reverse_lazy('milestones')


class MilestoneListView(ListView):
    context_object_name = 'milestones'

    def get_queryset(self):
        return Milestone.objects.all()


def milestone_list_by_project(request, project_id):
    project_milestones = Milestone.objects.filter(project_id=project_id)
    return render(request, 'project_management/milestone_list.html', {'milestones': project_milestones})


def load_milestones(request):
    projects = Project.objects.all
    return render(request, 'project_management/milestone_list.extended.html', {'projects': projects})


def load_task_milestoneI_list(request):
    project_id = request.GET.get('project')
    milestones = Milestone.objects.filter(project_id=project_id).order_by('name')
    return render(request, 'project_management/new_task_milestone_dropdown_list_options.html', {'milestones': milestones})


class MilestoneDetailView(DetailView):
    def get_queryset(self):
        return Milestone.objects.all()


class MilestoneUpdateView(UpdateView):
    model = Milestone
    template_name = 'project_management/milestone_update_form.html'
    form_class = MilestoneUpdateForm
    success_url = reverse_lazy('milestone_list')


class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm

    success_url = reverse_lazy('task_list')


class TaskListView(ListView):
    model = Task
    context_object_name = 'tasks'


def task_list_by_project(request, project_id):
    project_tasks = Task.objects.filter(project_id=project_id)
    return render(request, 'project_management/task_list.html', {'tasks': project_tasks})


def task_list_by_milestone(request, milestone_id):
    milestone_tasks = Task.objects.filter(milestone_id=milestone_id)
    return render(request, 'project_management/task_list.html', {'tasks': milestone_tasks})


class TaskUpdateView(UpdateView):
    model = Task
    template_name = 'project_management/task_update_form.html'
    form_class = TaskForm

        #id = self.request.GET.get('id',None)
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


class AddIncident(CreateView):
    model = Incident
    fields = ['project', 'milestone', 'task', 'title', 'description'
              , 'status', 'priority', 'assignee']
    template_name = 'project_management/addIncident.html'
    success_url = reverse_lazy('listIncidents')


class ListIncidents(ListView):
    template_name = 'project_management/listIncidents.html'
    context_object_name = 'all_incidents'

    def get_queryset(self):
        return Incident.objects.all()


class DetailsIncident(DetailView):
    model = Incident
    context_object_name = 'incident'
    template_name = 'project_management/detailsIncident.html'


class UpdateIncident(UpdateView):
    model = Incident
    fields = ['project', 'milestone', 'task', 'title', 'description'
              , 'status', 'priority', 'assignee']
    template_name = 'project_management/updateIncident.html'
    success_url = reverse_lazy('listIncidents')


def Milestone_progress():
    total_milestones = Milestone.objects.all()
    print(total_milestones)


def ongoingProjects(request):
    return render(request, 'project_management/ongoingprojects.html')


def listOfIncidents(request):
    return render(request, 'project_management/incidents.html')


def listOfMilesoneIncidents(request):
    return render(request, 'project_management/milestoneincidents.html')


def listOfTaskIncidents(request):
    return render(request, 'project_management/taskincidents.html')


def incident(request):
    return render(request, 'project_management/incident.html')


def newIncident(request):
    return render(request, 'project_management/newincident.html')


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
    fields = ['name', 'description']
    template_name = 'project_management/add_priority.html'
    success_url = reverse_lazy('listAllPriorities')


class UpdatePriority(UpdateView):
    model = Priority
    fields = ['name', 'description']
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
class AddProject(CreateView):
    model = Project
    template_name = 'project_management/add_project.html'
    fields = ['name', 'project_status', 'description', 'project_code', 'estimated_cost', 'final_cost', 'start_date',
              'end_date', 'actual_start_date', 'actual_end_date', 'logo', 'thumbnail']
    success_url = reverse_lazy('listProjects')


class ListProjects(ListView):
    template_name = 'project_management/list_projects.html'
    context_object_name = 'all_projects'

    def get_queryset(self):
        return Project.objects.all()


class UpdateProject(UpdateView):
    model = Project
    fields = ['name', 'project_status', 'project_code', 'final_cost', 'actual_start_date', 'actual_end_date']
    template_name = 'project_management/update_project.html'
    success_url = reverse_lazy('listProjects')


class DetailProject(DetailView):
    model = Project
    context_object_name = 'project'
    template_name = 'project_management/details_project.html'
    success_url = reverse_lazy('listProjects')


def validateProjectName(request):
    project_name = request.GET.get('projectname', None)
    data = {
        'is_taken': Project.objects.filter(name=project_name).exists()
    }
    return JsonResponse(data)


# PROJECT TEAMS
class AddProjectTeam(CreateView):
    model = ProjectTeam
    template_name = 'project_management/add_project_team.html'
    fields = ['name', 'project']
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
    project = request.GET.get('project', None)
    print(project)
    data = {
        'is_assigned': ProjectTeam.objects.filter(project=project).exists()
    }

    return JsonResponse(data)


# PROJECT TEAM MEMBERS
class AddProjectTeamMember(CreateView):
    model = ProjectTeamMember
    template_name = 'project_management/add_team_member.html'
    fields = ['member', 'project_team', 'responsibility']
    success_url = reverse_lazy('listProjectTeamMembers')


class ListProjectTeamMembers(ListView):
    template_name = 'project_management/list_team_members.html'
    context_object_name = 'teams'

    def get_queryset(self):
        return ProjectTeam.objects.annotate(num_members=Count('projectteammember'))


class UpdateProjectTeamMember(UpdateView):
    model = ProjectTeamMember
    fields = ['responsibility']
    template_name = 'project_management/update_project_team_member.html'
    success_url = reverse_lazy('listProjectTeamMembers')

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
    member_name = request.GET.get('member')
    project_team = request.GET.get('projectTeam')
    print(member_name)
    print(project_team)


    projectteam = ProjectTeam.objects.get(id=project_team)
    membername = ProjectTeamMember.objects.filter(id=member_name).exists()
    print("member name exists as '{}'".format(membername))

    if membername == 'True':
        print("member name is '{}'".format(membername))


        data = {

            'is_assigned': ProjectTeamMember.objects.filter(project_team=project_team).exists()
        }
        print(data)

        return JsonResponse(data)


def remove_project_team_member(request):
    team_id = request.GET.get('teamid')
    team_name = request.GET.get('teamname')
    member_id = request.GET.get('memberid')

    teamid = ProjectTeam.objects.get(id=int(team_id))
    memberid = ProjectTeamMember.objects.get(member=int(member_id))
    memberid.project_team.remove(teamid)


    team = ProjectTeamMember.objects.filter(project_team=int(team_id))
    template = loader.get_template('user_management/details_team_member.html')
    context = {
        'team': team,
        'team_name': team_name,
        'team_id': team_id,
    }


    return HttpResponse(template.render(context, request))
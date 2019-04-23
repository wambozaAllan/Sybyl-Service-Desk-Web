from django.contrib.auth.hashers import make_password
from django.views import generic
from django.views.generic import View, CreateView, ListView, DetailView, UpdateView, DeleteView
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from .models import User, UserTeam, UserTeamMember, GroupExtend
from django.http import JsonResponse
from django.template import loader
from extra_views import CreateWithInlinesView, UpdateWithInlinesView, InlineFormSetFactory
from .forms import UserForm, GroupExtendForm

# Used to add new users
def user_createview(request):
    model = User
    form_class = UserForm

    all_users = User.objects.all()
    template = loader.get_template('user_management/list_users.html')
    context = {
        'all_users': all_users,
    }

    form = UserForm(request.POST)
    if form.is_valid:
        data = request.POST.copy()
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        gender = data.get('gender')
        company = data.get('company')
        branch = data.get('branch')
        department = data.get('department')
        usergroup = data.get('group')
        category = data.get('category')
        username = data.get('username')
        password = make_password(data.get('password'))
        email = data.get('email')
        created_by = request.user.id

        obj = User(first_name=first_name, last_name=last_name, gender=gender, company_id=company, branch_id=branch,
                   department_id=department, group_id=usergroup, category_id=category, username=username,
                   password=password, created_by=created_by, email=email)
        obj.save()

    return HttpResponse(template.render(context, request))


class AddUser(CreateView):
    model = User
    fields = ['first_name', 'last_name', 'gender', 'company', 'branch', 'department', 'group', 'category'
        , 'username', 'email', 'password']

    template_name = 'user_management/add_user.html'
    success_url = reverse_lazy('listUsers')


# All user groups list view
class ListUsers(ListView):
    template_name = 'user_management/list_users.html'
    context_object_name = 'all_users'

    def get_queryset(self):
        return User.objects.all()


def validate_user_name(request):
    user_name = request.GET.get('username', None)
    data = {
        'is_taken': User.objects.filter(username=user_name).exists()
    }
    return JsonResponse(data)


class ProfileView(ListView):
    template_name = 'user_management/user_profile.html'

    def get_queryset(self):
        pass


# Detailed view of a specific user
class DetailsUser(DetailView):
    # model = User
    # context_object_name = 'user'
    # template_name = 'user_management/detailsUser.html'
    queryset = User.objects.all()


class UpdateUser(UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'gender', 'company'
        , 'branch', 'department', 'group', 'category'
        , 'username', 'password', 'email', 'is_superuser', 'is_staff', 'is_active']

    template_name = 'user_management/update_user.html'
    success_url = reverse_lazy('listUsers')


# Used to add new user groups
class AddUserGroup(CreateView):
    model = GroupExtend
    fields = ['company', 'description']
    template_name = 'user_management/add_user_group.html'
    success_url = reverse_lazy('listUserGroups')


def save_user_group(request):
    model = GroupExtend
    form_class = GroupExtendForm

    all_user_groups = GroupExtend.objects.all()
    template = loader.get_template('user_management/list_groups.html')
    context = {
        'all_userGroups': all_user_groups,
    }

    name = request.GET.get('name')
    desc = request.GET.get('desc')
    comp_id = request.GET.get('company')

    group_obj = Group(name=name)
    group_obj.save()

    if group_obj.id != "":
        if desc != "":
            group_extend_obj = GroupExtend(group_id=group_obj.id, company_id=comp_id, description=desc)
        else:
            group_extend_obj = GroupExtend(group_id=group_obj.id, company_id=comp_id)
        group_extend_obj.save()

    return HttpResponse(template.render(context, request))

def update_user_group(request):
    name = request.GET.get('name')
    desc = request.GET.get('desc')
    comp_id = request.GET.get('company')
    grp_extid = request.GET.get('grpextid')
    group_id = request.GET.get('grpid')

    GroupExtend.objects.filter(id=grp_extid).update(description=desc, company_id=comp_id)
    Group.objects.filter(id=group_id).update(name=name)

    all_user_groups = GroupExtend.objects.all()
    template = loader.get_template('user_management/list_groups.html')
    context = {
        'all_userGroups': all_user_groups,
    }

    return HttpResponse(template.render(context, request))


# All user groups list view
class ListUserGroups(ListView):
    template_name = 'user_management/list_user_groups.html'
    context_object_name = 'all_userGroups'

    def get_queryset(self):
        return GroupExtend.objects.all()


class UpdateUserGroup(UpdateView):
    model = GroupExtend
    fields = ['group', 'description', 'company']
    template_name = 'user_management/update_user_group.html'
    success_url = reverse_lazy('listUserGroups')


# Used to add new teams
class AddTeam(CreateView):
    model = UserTeam
    fields = ['name', ]
    template_name = 'user_management/addTeam.html'
    success_url = reverse_lazy('listTeams')


# All user groups list view
class ListTeams(ListView):
    template_name = 'user_management/listTeams.html'
    context_object_name = 'all_teams'

    def get_queryset(self):
        return UserTeam.objects.all()


# Detailed view of a specific user group
class DetailsTeam(DetailView):
    model = UserTeam
    context_object_name = 'team'
    template_name = 'user_management/detailsTeam.html'


class UpdateTeam(UpdateView):
    model = UserTeam
    fields = ['name', ]
    template_name = 'user_management/updateTeam.html'
    success_url = reverse_lazy('listTeams')


# Used to add new user groups
class AddUserToTeam(CreateView):
    model = UserTeamMember
    fields = ['user', 'user_team']
    template_name = 'user_management/addUserToTeam.html'
    success_url = reverse_lazy('listTeams')


def load_teams(request):
    # project_id = request.GET.get('project')
    # milestones = Milestone.objects.filter(project_id=project_id).order_by('name')
    userGroups = UserTeam.objects.all
    return render(request, 'user_management/listUserGroupsExtended.html', {'userGroups': userGroups})


def load_team_members(request):
    project_id = request.GET.get('project')
    members = UserTeamMember.objects.filter(user_team=project_id)  # .order_by('name')
    # members = UserTeamMember.objects.all
    return render(request, 'user_management/team_member_dropdown_list_options.html', {'members': members})


# System Modules
class ListSystemModules(ListView):
    template_name = 'user_management/list_system_modules.html'
    context_object_name = 'list_modules'

    def get_queryset(self):
        return ContentType.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_apps'] = ContentType.objects.order_by().values('app_label').distinct()
        return context


def get_permission_count(request):
    model_id = request.GET.get('modelid', None)
    data = {
        'pcount': Permission.objects.filter(content_type_id=model_id).count()
    }
    return JsonResponse(data)


class ListModulePermissions(ListView):
    model = ContentType
    template_name = 'user_management/list_permissions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        moduleid = int(self.request.GET['moduleid'])
        modulename = self.request.GET['modulename']
        context['permissions_list'] = Permission.objects.all().filter(content_type_id=moduleid)
        context['modulename'] = modulename
        return context


# Filter System Modules by app name
def filter_system_modules(request):
    app_label = request.GET.get('appname')
    modules = ContentType.objects.filter(app_label=app_label)

    return render(request, 'user_management/list_filtered_modules.html', {'list_modules': modules})

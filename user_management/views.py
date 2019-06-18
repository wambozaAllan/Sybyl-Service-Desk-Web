from django.contrib.auth.hashers import make_password
from django.views import generic
from django.views.generic import View, CreateView, ListView, DetailView, UpdateView, DeleteView
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from .models import User, UserTeam, UserTeamMember, GroupExtend, Company, Branch, Department
from django.http import JsonResponse
from django.template import loader
from .forms import UserForm, GroupExtendForm
from django.db.models import Q
from django.core import serializers
import json
from django.db.models import Count

from django.shortcuts import render
from django.core.mail import send_mail
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.template import RequestContext
import socket


# Used to add new users
def user_createview(request):
    comp_id = request.session['company_id']

    all_users = User.objects.filter(company=comp_id)
    template = loader.get_template('user_management/list_user_update.html')
    context = {
        'all_users': all_users,
    }

    first_name = request.GET.get('first_name')
    last_name = request.GET.get('last_name')
    gender = request.GET.get('gender')
    branch = request.GET.get('branch')
    department = request.GET.get('department')
    username = request.GET.get('username')
    email = request.GET.get('email')
    random_password = User.objects.make_random_password()
    password = make_password(random_password)
    created_by = request.user.id
    company = request.session['company_id']

    obj = User(first_name=first_name.title(), last_name=last_name.title(), gender=gender, company_id=company,
               branch_id=branch, department_id=department, username=username,
               password=password, created_by=created_by, email=email)
    obj.save()

    if obj.pk is not None:
        context22 = {
            'username': username,
            'password': random_password,
            'fullname': first_name + ' ' + last_name
        }

        msg = render_to_string(
            'user_management/email_template.html', context22)

        subject, from_email, to = 'SYBYL', 'from@example.com', email
        text_content = 'SERVICE DESK.'
        html_content = msg
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    return HttpResponse(template.render(context, request))


def update_resend_user_email(request):
    uid = request.GET.get('uid')
    username = request.GET.get('username')
    email = request.GET.get('email')
    first_name = request.GET.get('fname')
    last_name = request.GET.get('lname')
    random_password = User.objects.make_random_password()
    password = make_password(random_password)

    User.objects.filter(pk=int(uid)).update(username=username, email=email, password=password)

    context22 = {
        'username': username,
        'password': random_password,
        'fullname': first_name + ' ' + last_name
    }

    msg = render_to_string(
        'user_management/email_template.html', context22)

    subject, from_email, to = 'SYBYL', 'from@example.com', email
    text_content = 'SERVICE DESK.'
    html_content = msg
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    comp_id = request.session['company_id']
    all_users = User.objects.filter(company=comp_id)
    template = loader.get_template('user_management/list_user_update.html')
    context = {
        'all_users': all_users,
    }

    return HttpResponse(template.render(context, request))


class AddUser(CreateView):
    model = User
    fields = ['first_name', 'last_name',
              'gender', 'username', 'email', 'password']

    template_name = 'user_management/add_user.html'
    success_url = reverse_lazy('listUsers')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comp_id = self.request.session['company_id']

        comp_branches = Branch.objects.filter(company=comp_id)
        comp_department = Department.objects.filter(company=comp_id)
        context['branches'] = comp_branches
        context['dept'] = comp_department
        return context


# All user groups list view
class ListUsers(ListView):
    template_name = 'user_management/list_users.html'
    context_object_name = 'all_users'

    def get_queryset(self):
        comp_id = self.request.session['company_id']
        return User.objects.filter(company=comp_id)


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
    model = User
    context_object_name = 'user_details'
    template_name = 'user_management/detailsUser.html'


class UpdateUser(UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'gender', 'company', 'department', 'group',
              'branch', 'username', 'password', 'email', 'is_superuser', 'is_staff', 'is_active']

    template_name = 'user_management/update_user.html'
    success_url = reverse_lazy('listUsers')
    context_object_name = 'user_update'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comp_id = self.request.session['company_id']

        comp_branches = Branch.objects.filter(company=comp_id)
        comp_department = Department.objects.filter(company=comp_id)
        context['branches'] = comp_branches
        context['dept'] = comp_department
        return context


def save_system_user_update(request):
    comp_id = request.session['company_id']

    all_users = User.objects.filter(company=comp_id)
    template = loader.get_template('user_management/list_user_update.html')
    context = {
        'all_users': all_users,
    }

    first_name = request.GET.get('first_name')
    last_name = request.GET.get('last_name')
    gender = request.GET.get('gender')
    branch = request.GET.get('branch')
    uid = request.GET.get('user_id')
    department = request.GET.get('department')
    username = request.GET.get('username')
    email = request.GET.get('email')
    group = request.GET.get('group')
    active = request.GET.get('status')
    company = request.GET.get('company')

    User.objects.filter(pk=int(uid)).update(first_name=first_name.title(), last_name=last_name.title(), gender=gender,
                                            branch_id=branch,
                                            department_id=department, username=username, email=email, group=group,
                                            is_active=int(active), company_id=company)

    return HttpResponse(template.render(context, request))


class AddUserGroup(CreateView):
    model = GroupExtend
    fields = ['description', 'active']
    template_name = 'user_management/add_user_group.html'
    success_url = reverse_lazy('listUserGroups')


class AddGlobalUserGroup(CreateView):
    model = GroupExtend
    fields = ['description', 'active']
    template_name = 'user_management/add_global_user_group.html'
    success_url = reverse_lazy('listUserGroups')


def save_user_group(request):
    company_id = request.session['company_id']
    all_user_groups = Group.objects.filter(
        initialgroup__company_id=company_id).annotate(num_user=Count('initialgroup'))
    template = loader.get_template('user_management/list_groups.html')
    context = {
        'all_userGroups': all_user_groups,
    }

    name = request.GET.get('name')
    desc = request.GET.get('desc')
    active = request.GET.get('active')

    group_obj = Group(name=name)
    group_obj.save()

    if group_obj.id != "":
        if desc != "":
            group_extend_obj = GroupExtend(
                group_id=group_obj.id, description=desc, active=active)
        else:
            group_extend_obj = GroupExtend(
                group_id=group_obj.id, active=active)
        group_extend_obj.save()

    return HttpResponse(template.render(context, request))


def save_global_user_group(request):
    all_user_groups = Group.objects.annotate(num_user=Count('initialgroup'))
    template = loader.get_template('user_management/global_user_groups.html')
    context = {
        'all_userGroups': all_user_groups,
    }

    name = request.GET.get('name')
    desc = request.GET.get('desc')
    active = request.GET.get('active')

    group_obj = Group(name=name)
    group_obj.save()

    if group_obj.id != "":
        if desc != "":
            group_extend_obj = GroupExtend(
                group_id=group_obj.id, description=desc, active=active)
        else:
            group_extend_obj = GroupExtend(
                group_id=group_obj.id, active=active)
        group_extend_obj.save()

    return HttpResponse(template.render(context, request))


def save_global_user_group(request):
    all_user_groups = Group.objects.annotate(num_user=Count('initialgroup'))
    template = loader.get_template('user_management/list_global_groups.html')
    context = {
        'all_userGroups': all_user_groups,
    }

    name = request.GET.get('name')
    desc = request.GET.get('desc')
    active = request.GET.get('active')

    group_obj = Group(name=name)
    group_obj.save()

    if group_obj.id != "":
        if desc != "":
            group_extend_obj = GroupExtend(
                group_id=group_obj.id, description=desc, active=active)
        else:
            group_extend_obj = GroupExtend(
                group_id=group_obj.id, active=active)
        group_extend_obj.save()

    return HttpResponse(template.render(context, request))


def update_user_group(request):
    name = request.GET.get('name')
    desc = request.GET.get('desc')
    active = request.GET.get('active')
    grp_extid = request.GET.get('grpextid')
    group_id = request.GET.get('grpid')

    GroupExtend.objects.filter(id=grp_extid).update(
        description=desc, active=active)
    Group.objects.filter(id=group_id).update(name=name)

    company_id = request.session['company_id']
    all_user_groups = Group.objects.filter(
        initialgroup__company_id=company_id).annotate(num_user=Count('initialgroup'))
    template = loader.get_template('user_management/list_groups.html')
    context = {
        'all_userGroups': all_user_groups,
    }

    return HttpResponse(template.render(context, request))


def update_global_user_group(request):
    name = request.GET.get('name')
    desc = request.GET.get('desc')
    active = request.GET.get('active')
    grp_extid = request.GET.get('grpextid')
    group_id = request.GET.get('grpid')

    GroupExtend.objects.filter(id=grp_extid).update(
        description=desc, active=active)
    Group.objects.filter(id=group_id).update(name=name)

    company_id = request.session['company_id']
    all_user_groups = Group.objects.annotate(num_user=Count('initialgroup'))
    template = loader.get_template('user_management/list_global_groups.html')
    context = {
        'all_userGroups': all_user_groups,
    }

    return HttpResponse(template.render(context, request))


def list_manage_group(request):
    grpid = request.GET.get('grpid')
    grpname = request.GET.get('grp')
    company_id = request.session['company_id']

    group_users = User.objects.filter(group_id=grpid, company=company_id)
    template = loader.get_template('user_management/list_group_users.html')
    context = {
        'group_users': group_users,
        'grp': grpname,
        'grpid': grpid,
    }

    return HttpResponse(template.render(context, request))


def list_manage_global_group(request):
    grpid = request.GET.get('grpid')
    grpname = request.GET.get('grp')

    group_users = User.objects.filter(group_id=grpid)
    template = loader.get_template(
        'user_management/list_global_group_users.html')
    context = {
        'group_users': group_users,
        'grp': grpname,
        'grpid': grpid,
    }

    return HttpResponse(template.render(context, request))


def manage_group_permissions(request):
    grpid = request.GET.get('grpid')
    grpname = request.GET.get('grp')

    group_permissions = Permission.objects.filter(group=grpid)
    template = loader.get_template(
        'user_management/list_group_permissions.html')
    context = {
        'group_permissions': group_permissions,
        'grp': grpname,
        'grpid': grpid,
    }

    return HttpResponse(template.render(context, request))


def manage_global_group_permissions(request):
    grpid = request.GET.get('grpid')
    grpname = request.GET.get('grp')

    group_permissions = Permission.objects.filter(group=grpid)
    template = loader.get_template(
        'user_management/list_global_group_permissions.html')
    context = {
        'group_permissions': group_permissions,
        'grp': grpname,
        'grpid': grpid,
    }

    return HttpResponse(template.render(context, request))


def search_unassigned_users(request):
    search_value = request.GET.get('searchValue')
    grp = request.GET.get('grp')
    grpid = request.GET.get('grpid')
    company_id = request.session['company_id']
    users = User.objects.filter(
        (Q(first_name__icontains=search_value) | Q(last_name__icontains=search_value)) & Q(group_id__isnull=True) & Q(
            company=company_id))
    template = loader.get_template(
        'user_management/unassigned_users_search_results.html')
    context = {
        'users': users,
        'search_value': search_value,
        'grp': grp,
        'grpid': grpid,
    }

    return HttpResponse(template.render(context, request))


def search_unassigned_global_users(request):
    search_value = request.GET.get('searchValue')
    grp = request.GET.get('grp')
    grpid = request.GET.get('grpid')
    users = User.objects.filter(
        (Q(first_name__icontains=search_value) | Q(last_name__icontains=search_value)) & Q(group_id__isnull=True))
    template = loader.get_template(
        'user_management/unassigned_global_users_search_results.html')
    context = {
        'users': users,
        'search_value': search_value,
        'grp': grp,
        'grpid': grpid,
    }

    return HttpResponse(template.render(context, request))


def save_user_to_group(request):
    user_id = request.GET.get('uid')
    group_id = request.GET.get('grpid')
    grpname = request.GET.get('grpname')
    company_id = request.session['company_id']

    User.objects.filter(id=int(user_id)).update(group_id=int(group_id))

    group_users = User.objects.filter(
        group_id=int(group_id), company=company_id)
    template = loader.get_template('user_management/list_group_users.html')
    context = {
        'group_users': group_users,
        'grp': grpname,
        'grpid': group_id,
    }

    return HttpResponse(template.render(context, request))


def save_user_to_global_group(request):
    user_id = request.GET.get('uid')
    group_id = request.GET.get('grpid')
    grpname = request.GET.get('grpname')

    User.objects.filter(id=int(user_id)).update(group_id=int(group_id))

    group_users = User.objects.filter(group_id=int(group_id))
    template = loader.get_template(
        'user_management/list_global_group_users.html')
    context = {
        'group_users': group_users,
        'grp': grpname,
        'grpid': group_id,
    }

    return HttpResponse(template.render(context, request))


# Company user groups list view
class ListUserGroups(ListView):
    template_name = 'user_management/list_user_groups.html'
    context_object_name = 'all_userGroups'

    def get_queryset(self, *args, **kwargs):
        company_id = self.request.session['company_id']
        return Group.objects.filter(initialgroup__company_id=company_id).annotate(num_user=Count('initialgroup'))


# All user groups list view
class GlobalUserGroups(ListView):
    template_name = 'user_management/global_user_groups.html'
    context_object_name = 'all_userGroups'

    def get_queryset(self, *args, **kwargs):
        return Group.objects.annotate(num_user=Count('initialgroup'))


class UpdateUserGroup(UpdateView):
    model = GroupExtend
    fields = ['group', 'description', 'active']
    template_name = 'user_management/update_user_group.html'
    success_url = reverse_lazy('listUserGroups')


class UpdateUserGlobalGroup(UpdateView):
    model = GroupExtend
    fields = ['group', 'description', 'active']
    template_name = 'user_management/update_global_user_group.html'
    success_url = reverse_lazy('globalUserGroups')


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
    members = UserTeamMember.objects.filter(
        user_team=project_id)  # .order_by('name')
    # members = UserTeamMember.objects.all
    return render(request, 'user_management/team_member_dropdown_list_options.html', {'members': members})


# System Modules
class ListSystemModules(ListView):
    template_name = 'user_management/list_system_modules.html'
    context_object_name = 'list_modules'

    def get_queryset(self):
        return ContentType.objects.annotate(count_permissions=Count('permission'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_apps'] = ContentType.objects.order_by().values(
            'app_label').distinct()
        return context


class ListModulePermissions(ListView):
    model = ContentType
    template_name = 'user_management/list_permissions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        moduleid = int(self.request.GET['moduleid'])
        modulename = self.request.GET['modulename']
        context['permissions_list'] = Permission.objects.all().filter(
            content_type_id=moduleid)
        context['modulename'] = modulename
        return context


# Filter System Modules by app name
def filter_system_modules(request):
    app_label = request.GET.get('appname')
    modules = ContentType.objects.filter(app_label=app_label).annotate(
        count_permissions=Count('permission'))

    return render(request, 'user_management/list_filtered_modules.html', {'list_modules': modules})


class ListContentTypes(ListView):
    template_name = 'user_management/assign_permissions.html'
    context_object_name = 'all_modules'

    def get_queryset(self):
        return ContentType.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grpid = int(self.request.GET['grpid'])
        grp = self.request.GET['grp']
        context['grpid'] = grpid
        context['grp'] = grp
        return context


def fetch_permissions_by_module(request):
    module_id = request.GET.get('moduleid')
    grpid1 = request.GET.get('grpid')

    all_permission = Permission.objects.filter(content_type_id=int(module_id))

    permission_obj = Permission.objects.filter(
        content_type_id=int(module_id), group=int(grpid1))

    distinct_permissions = set(all_permission).difference(set(permission_obj))

    data = {
        'perm': serializers.serialize("json", distinct_permissions)
    }
    return JsonResponse(data)


def save_group_permissions(request):
    group_id = request.GET.get('grpid')
    grpname = request.GET.get('grpname')
    permission_list = request.GET.get('permissionlist')
    json_data = json.loads(permission_list)

    for permission in json_data:
        groupid = Group.objects.get(id=int(group_id))
        permid = Permission.objects.get(id=int(permission['perm']))
        groupid.permissions.add(permid)

    group_permissions = Permission.objects.filter(group=int(group_id))
    template = loader.get_template(
        'user_management/list_group_permissions.html')
    context = {
        'group_permissions': group_permissions,
        'grp': grpname,
        'grpid': group_id,
    }

    return HttpResponse(template.render(context, request))


def remove_group_permissions(request):
    group_id = request.GET.get('grpid')
    grpname = request.GET.get('grpname')
    permission_id = request.GET.get('pid')

    groupid = Group.objects.get(id=int(group_id))
    permid = Permission.objects.get(id=int(permission_id))
    groupid.permissions.remove(permid)

    group_permissions = Permission.objects.filter(group=int(group_id))
    template = loader.get_template(
        'user_management/list_group_permissions.html')
    context = {
        'group_permissions': group_permissions,
        'grp': grpname,
        'grpid': group_id,
    }

    return HttpResponse(template.render(context, request))


def delete_user_group(request):
    group_id = request.GET.get('grpid')
    group_ext_id = request.GET.get('grpextid')

    GroupExtend.objects.filter(id=int(group_ext_id)).delete()
    Group.objects.filter(id=int(group_id)).delete()

    company_id = request.session['company_id']
    all_user_groups = Group.objects.filter(
        initialgroup__company_id=company_id).annotate(num_user=Count('initialgroup'))
    template = loader.get_template('user_management/list_groups.html')
    context = {
        'all_userGroups': all_user_groups,
    }

    return HttpResponse(template.render(context, request))


def delete_global_user_group(request):
    group_id = request.GET.get('grpid')
    group_ext_id = request.GET.get('grpextid')

    GroupExtend.objects.filter(id=int(group_ext_id)).delete()
    Group.objects.filter(id=int(group_id)).delete()

    all_user_groups = Group.objects.annotate(num_user=Count('initialgroup'))
    template = loader.get_template('user_management/list_global_groups.html')
    context = {
        'all_userGroups': all_user_groups,
    }

    return HttpResponse(template.render(context, request))


def remove_user_from_group(request):
    user_id = request.GET.get('uid')
    group_id = request.GET.get('grpid')
    grpname = request.GET.get('grpname')
    company_id = request.session['company_id']

    User.objects.filter(pk=int(user_id)).update(group_id=None)

    group_users = User.objects.filter(
        group_id=int(group_id), company=company_id)
    template = loader.get_template('user_management/list_group_users.html')
    context = {
        'group_users': group_users,
        'grp': grpname,
        'grpid': group_id,
    }

    return HttpResponse(template.render(context, request))


def remove_user_from_global_group(request):
    user_id = request.GET.get('uid')
    group_id = request.GET.get('grpid')
    grpname = request.GET.get('grpname')

    User.objects.filter(pk=int(user_id)).update(group_id=None)

    group_users = User.objects.filter(group_id=int(group_id))
    template = loader.get_template(
        'user_management/list_global_group_users.html')
    context = {
        'group_users': group_users,
        'grp': grpname,
        'grpid': group_id,
    }

    return HttpResponse(template.render(context, request))


def add_user_to_global_group(request):
    user_id = request.GET.get('uid')
    user_name = request.GET.get('user_name')
    grpid = request.GET.get('grpid')
    grp_name = request.GET.get('grpname')
    company_name = request.GET.get('company')
    company_id = request.GET.get('cid')

    template = loader.get_template(
        'user_management/add_user_to_global_group.html')
    context = {
        'uid': user_id,
        'u_name': user_name,
        'grpid': grpid,
        'grp_name': grp_name,
        'company_name': company_name,
    }

    return HttpResponse(template.render(context, request))


def check_internet_connection(request):
    try:
        socket.create_connection(("www.google.com", 80))
        status = True
    except OSError:
        status = False

    data = {
        'test': status
    }
    return JsonResponse(data)

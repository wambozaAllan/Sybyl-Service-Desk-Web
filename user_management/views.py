from django.contrib.auth.hashers import make_password
from django.views import generic
from django.views.generic import View, CreateView, ListView, DetailView, UpdateView, DeleteView
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from .models import User, UserTeam, UserTeamMember, GroupExtend, Company, Branch, Department, UserPhoneContact
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
               branch_id=branch, department_id=department, username=username, user_type="normaluser",
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


class ProfileView(UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'gender', 'company', 'department', 'groups',
              'branch', 'username', 'email', 'city', 'nationality', 'postal_code', 'address', 'secondary_email']
    
    template = loader.get_template('user_management/user_profile.html')

    template_name = 'user_management/user_profile.html'
    success_url = reverse_lazy('listUsers')
    context_object_name = 'user_update'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_dl = UserPhoneContact.objects.filter(user_id=self.get_object().pk).first()
        if user_dl is not None:
            context['contact'] = user_dl.phone_contact
            context['userphonecontact_id'] = user_dl.id
        else:
            context['contact'] = ''
            context['userphonecontact_id'] = ''

        return context


# Detailed view of a specific user
class DetailsUser(DetailView):
    model = User
    context_object_name = 'user_details'
    template_name = 'user_management/detailsUser.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_group_data = User.objects.filter(id=self.get_object().pk).values('groups').first()
        
        if selected_group_data['groups'] is not None:
            selected_group_data2 = Group.objects.get(id=selected_group_data['groups'])
            if selected_group_data2 is not None:
                context['selected_gname'] = selected_group_data2.name
        return context


class UpdateUser(UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'gender', 'company', 'department', 'groups',
              'branch', 'username', 'password', 'email', 'is_superuser', 'is_staff', 'is_active']

    template_name = 'user_management/update_user.html'
    success_url = reverse_lazy('listUsers')
    context_object_name = 'user_update'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comp_id = self.request.session['company_id']

        comp_branches = Branch.objects.filter(company=comp_id)
        comp_department = Department.objects.filter(company=comp_id)
        groups = Group.objects.all()
        context['branches'] = comp_branches
        context['dept'] = comp_department
        context['group_detail'] = groups
        selected_group_data = User.objects.filter(id=self.get_object().pk).values('groups').first()
        
        if selected_group_data['groups'] is not None:
            selected_group_data2 = Group.objects.get(id=selected_group_data['groups'])
            if selected_group_data2 is not None:
                context['selected_pk'] = selected_group_data2.pk
                context['selected_gname'] = selected_group_data2.name
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
    super_user_status = request.GET.get('is_superuser')

    User.objects.filter(pk=int(uid)).update(first_name=first_name.title(), last_name=last_name.title(), gender=gender,
                                            branch_id=branch, department_id=department, username=username, email=email,
                                            is_active=int(active), company_id=company, is_superuser=int(super_user_status))
    
    if group is not "":
        user_id1 = User.objects.get(id=int(uid))
        groupid1 = Group.objects.get(id=int(group))
        user_id1.groups.add(groupid1)
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
        groups__company_id=company_id).annotate(num_user=Count('groups'))
    template = loader.get_template('user_management/list_groups.html')
    context = {
        'all_userGroups': all_user_groups,
    }

    name = request.GET.get('name')
    desc = request.GET.get('desc')
    active = request.GET.get('active')
    user_id = request.user.id

    group_obj = Group(name=name)
    group_obj.save()

    if group_obj.id != "":
        if desc != "":
            group_extend_obj = GroupExtend(
                group_id=group_obj.id, description=desc, active=active, created_by_id = user_id)
        else:
            group_extend_obj = GroupExtend(
                group_id=group_obj.id, active=active, created_by_id = user_id)
        group_extend_obj.save()

    return HttpResponse(template.render(context, request))


def save_global_user_group(request):
    all_user_groups = Group.objects.annotate(num_user=Count('groups'))
    template = loader.get_template('user_management/global_user_groups.html')
    context = {
        'all_userGroups': all_user_groups,
    }

    name = request.GET.get('name')
    desc = request.GET.get('desc')
    active = request.GET.get('active')
    user_id = request.user.id

    group_obj = Group(name=name)
    group_obj.save()

    if group_obj.id != "":
        if desc != "":
            group_extend_obj = GroupExtend(
                group_id=group_obj.id, description=desc, active=active, created_by_id = user_id)
        else:
            group_extend_obj = GroupExtend(
                group_id=group_obj.id, active=active, created_by_id = user_id)
        group_extend_obj.save()

    return HttpResponse(template.render(context, request))


def save_global_user_group(request):
    all_user_groups = Group.objects.annotate(num_user=Count('groups'))
    template = loader.get_template('user_management/list_global_groups.html')
    context = {
        'all_userGroups': all_user_groups,
    }

    name = request.GET.get('name')
    desc = request.GET.get('desc')
    active = request.GET.get('active')
    user_id = request.user.id

    group_obj = Group(name=name)
    group_obj.save()

    if group_obj.id != "":
        if desc != "":
            group_extend_obj = GroupExtend(
                group_id=group_obj.id, description=desc, active=active, created_by_id = user_id)
        else:
            group_extend_obj = GroupExtend(
                group_id=group_obj.id, active=active, created_by_id = user_id)
        group_extend_obj.save()

    return HttpResponse(template.render(context, request))


def update_user_group(request):
    name = request.GET.get('name')
    desc = request.GET.get('desc')
    active = request.GET.get('active')
    grp_extid = request.GET.get('grpextid')
    group_id = request.GET.get('grpid')

    GroupExtend.objects.filter(id=grp_extid).update(description=desc, active=active)
    Group.objects.filter(id=group_id).update(name=name)

    company_id = request.session['company_id']
    all_user_groups = Group.objects.filter(groups__company_id=company_id).annotate(num_user=Count('groups'))
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

    GroupExtend.objects.filter(id=grp_extid).update(description=desc, active=active)
    Group.objects.filter(id=group_id).update(name=name)

    company_id = request.session['company_id']
    all_user_groups = Group.objects.annotate(num_user=Count('groups'))
    template = loader.get_template('user_management/list_global_groups.html')
    context = {
        'all_userGroups': all_user_groups,
    }

    return HttpResponse(template.render(context, request))


def list_manage_group(request):
    grpid = request.GET.get('grpid')
    grpname = request.GET.get('grp')
    company_id = request.session['company_id']

    group_users = User.objects.filter(groups=grpid, company=company_id)
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

    group_users = User.objects.filter(groups=grpid)
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
        (Q(first_name__icontains=search_value) | Q(last_name__icontains=search_value)) & Q(groups__isnull=True) & Q(company=company_id))
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
        (Q(first_name__icontains=search_value) | Q(last_name__icontains=search_value)) & Q(groups__isnull=True))
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

    user_id1 = User.objects.get(id=int(user_id))
    groupid1 = Group.objects.get(id=int(group_id))
    user_id1.groups.add(groupid1)

    group_users = User.objects.filter(
        groups=int(group_id), company=company_id)
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

    # MANY TO MANY SAVE
    user_id1 = User.objects.get(id=int(user_id))
    groupid1 = Group.objects.get(id=int(group_id))
    user_id1.groups.add(groupid1)

    group_users = User.objects.filter(groups=int(group_id))
    template = loader.get_template('user_management/list_global_group_users.html')
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
        return Group.objects.filter(groups__company_id=company_id).annotate(num_user=Count('groups'))


# All user groups list view
class GlobalUserGroups(ListView):
    template_name = 'user_management/global_user_groups.html'
    context_object_name = 'all_userGroups'

    def get_queryset(self, *args, **kwargs):
        return Group.objects.annotate(num_user=Count('groups'))


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

    permission_obj = Permission.objects.filter(content_type_id=int(module_id), group=int(grpid1))

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
        groups__company_id=company_id).annotate(num_user=Count('groups'))
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

    all_user_groups = Group.objects.annotate(num_user=Count('groups'))
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

    user_id1 = User.objects.get(id=int(user_id))
    groupid1 = Group.objects.get(id=int(group_id))
    user_id1.groups.remove(groupid1)

    group_users = User.objects.filter(
        groups=int(group_id), company=company_id)
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
    
    user_id1 = User.objects.get(id=int(user_id))
    groupid1 = Group.objects.get(id=int(group_id))
    user_id1.groups.remove(groupid1)

    group_users = User.objects.filter(groups=int(group_id))
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


def save_profile_user_update(request):
    template = loader.get_template('user_management/user_updated_profile.html')

    first_name = request.GET.get('first_name')
    last_name = request.GET.get('last_name')
    gender = request.GET.get('gender')
    uid = request.GET.get('user_id')
    secondary_email = request.GET.get('id_secondary_email')
    address = request.GET.get('id_address')
    city = request.GET.get('city')
    nationality = request.GET.get('nationality')
    postal_code = request.GET.get('postal_code')
    contact_value = request.GET.get('contact')
    id_userphonecontact = request.GET.get('id_userphonecontact')
    dept = request.GET.get('dept')
    username = request.GET.get('username')

    company = request.GET.get('company')
    branch = request.GET.get('branch')
    email = request.GET.get('email')

    User.objects.filter(pk=int(uid)).update(first_name=first_name.title(), last_name=last_name.title(), gender=gender,
        address=address, city=city, postal_code=postal_code, secondary_email=secondary_email, nationality=nationality)

    if id_userphonecontact is not '':
        UserPhoneContact.objects.filter(pk=int(id_userphonecontact)).update(phone_contact=contact_value)
    else:
        obj33 = UserPhoneContact(phone_contact=contact_value, user_id=uid)
        obj33.save()
        id_userphonecontact = obj33.id

    context = {
        'first_name': first_name,
        'last_name': last_name,
        'gender': gender,
        'uid': uid,
        'secondary_email': secondary_email,
        'address': address,
        'city': city,
        'nationality': nationality,
        'postal_code': postal_code,
        'contact': contact_value,
        'userphonecontact_id': id_userphonecontact,
        'company': company,
        'branch': branch,
        'dept': dept,
        'email': email,
        'username': username,
    }

    return HttpResponse(template.render(context, request))


# CUSTOMERS
def list_customer_users(request):
    """list users under customer company"""
    company_id = request.GET.get('company_id')
    
    template = loader.get_template('user_management/list_customer_users.html')

    user = User.objects.filter(company_id=int(company_id))
    company = Company.objects.get(id=int(company_id))
    
    context = {
        "users": user,
        "company_id": company_id,
        "company_name": company.name
    }

    return HttpResponse(template.render(context, request))
        

def add_customer_user(request):
    company_id = request.GET.get('company_id')
    company_name = request.GET.get('company_name')
    
    template = loader.get_template('user_management/add_customer_user.html')
    context = {
        'company_id': company_id,
        'company_name': company_name,
    }

    return HttpResponse(template.render(context, request))


def save_customer_user(request):
    company_id = request.GET.get('company_id')

    template = loader.get_template('user_management/list_customer_users.html')

    user = User.objects.filter(company_id=int(company_id))
    company = Company.objects.get(id=int(company_id))
    
    context = {
        "users": user,
        "company_id": company_id,
        "company_name": company.name
    }

    first_name = request.GET.get('first_name')
    last_name = request.GET.get('last_name')
    gender = request.GET.get('gender')
    username = request.GET.get('username')
    email = request.GET.get('email')
    random_password = User.objects.make_random_password()
    password = make_password(random_password)
    created_by = request.user.id

    obj = User(first_name=first_name.title(), last_name=last_name.title(), gender=gender, company_id=company_id,
               username=username, user_type="clientuser",
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


class DetailsCustomerUser(DetailView):
    model = User
    context_object_name = 'user_details'
    template_name = 'user_management/details_customer_user.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_group_data = User.objects.filter(id=self.get_object().pk).values('groups').first()
        
        if selected_group_data['groups'] is not None:
            selected_group_data2 = Group.objects.get(id=selected_group_data['groups'])
            if selected_group_data2 is not None:
                context['selected_gname'] = selected_group_data2.name
        return context


def delete_customer_user(request):
    user_id = request.GET.get('user_id')
    company_id = request.GET.get('company_id')

    User.objects.filter(id=int(user_id)).delete()
    company = Company.objects.get(id=int(company_id))
    user = User.objects.filter(company_id=int(company_id))

    template = loader.get_template('user_management/list_customer_users.html')
    context = {
        "users": user,
        "company_id": company_id,
        "company_name": company.name
    }

    return HttpResponse(template.render(context, request))


def update_resend_customer_email(request):
    uid = request.GET.get('uid')
    username = request.GET.get('username')
    email = request.GET.get('email')
    first_name = request.GET.get('fname')
    last_name = request.GET.get('lname')
    company_id = request.GET.get('company_id')
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

    company = Company.objects.get(id=int(company_id))
    users = User.objects.filter(company_id=int(company_id))
    template = loader.get_template('user_management/list_customer_users.html')
    context = {
        'users': users,
        "company_id": company_id,
        "company_name": company.name
    }

    return HttpResponse(template.render(context, request))


class UpdateCustomerUser(UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'gender', 'company', 'department', 'groups',
              'branch', 'username', 'password', 'email', 'is_superuser', 'is_staff', 'is_active']

    template_name = 'user_management/update_customer_user.html'
    success_url = reverse_lazy('listUsers')
    context_object_name = 'user_update'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        groups = Group.objects.all()
        context['group_detail'] = groups

        selected_group_data = User.objects.filter(id=self.get_object().pk).values('groups').first()
        
        if selected_group_data['groups'] is not None:
            selected_group_data2 = Group.objects.get(id=selected_group_data['groups'])
            if selected_group_data2 is not None:
                context['selected_pk'] = selected_group_data2.pk
                context['selected_gname'] = selected_group_data2.name
        return context


def save_system_customer_update(request):
    first_name = request.GET.get('first_name')
    last_name = request.GET.get('last_name')
    gender = request.GET.get('gender')
    uid = request.GET.get('user_id')
    username = request.GET.get('username')
    email = request.GET.get('email')
    group = request.GET.get('group')
    active = request.GET.get('status')
    company = request.GET.get('company')
    super_user_status = request.GET.get('is_superuser')

    all_users = User.objects.filter(company=int(company))
    company = Company.objects.get(id=int(company))

    template = loader.get_template('user_management/list_customer_users.html')
    context = {
        'users': all_users,
        'company_id': company.id,
        'company_name': company.name
    }

    User.objects.filter(pk=int(uid)).update(first_name=first_name.title(), last_name=last_name.title(), gender=gender,
                                            username=username, email=email,
                                            is_active=int(active), company_id=company, is_superuser=int(super_user_status))
    
    if group is not "":
        user_id1 = User.objects.get(id=int(uid))
        groupid1 = Group.objects.get(id=int(group))
        user_id1.groups.add(groupid1)
    return HttpResponse(template.render(context, request))
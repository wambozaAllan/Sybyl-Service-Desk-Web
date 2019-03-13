from django.contrib.auth.hashers import make_password
from django.views import generic
from django.views.generic import View, CreateView, ListView, DetailView, UpdateView, DeleteView
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy

from .forms import CustomUserCreationForm, UserTeamMeamberForm, CreateUserForm
from .models import User, UserGroup, UserTeam, UserTeamMember

from core.models import UsrGrpPermissions

# Used to add new users
def user_createview(request):
    #permission_list = list(request.user.get_all_permissions())
    form = CreateUserForm()
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            obj = User.objects.create(
                first_name    = form.cleaned_data.get('first_name'),
                last_name     = form.cleaned_data.get('last_name'),
                gender        = form.cleaned_data.get('gender'),
                company       = form.cleaned_data.get('company'),
                branch        = form.cleaned_data.get('branch'),
                department    = form.cleaned_data.get('department'),
                usergroup     = form.cleaned_data.get('usergroup'),
                category      = form.cleaned_data.get('category'),
                username      = form.cleaned_data.get('username'),
                password      = make_password(form.cleaned_data.get('password'))
                )
        return HttpResponseRedirect("/userManagement/listUsers/")
    template_name = 'user_management/addUser.html'
    #template_name = 'user_management/user_profile.html'
    context = {'form': form,}
    return render(request, template_name, context)

class AddUser(CreateView):
    form_class = CreateUserForm
    print('HEre..')
    template_name = 'user_management/addUser.html'

    def form_valid(self, form):
        instance = form.save(commit=False)
        #instance.owner = self.request.user
        instance.password = make_password()
        return super(AddUser,  self).form_valid(form)

    success_url = reverse_lazy('listUsers')

# All user groups list view
class ListUsers(ListView):
    template_name = 'user_management/listUsers.html'
    context_object_name = 'all_users'

    def get_queryset(self):
        return User.objects.all()

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
              , 'branch', 'department', 'usergroup', 'category'
              , 'username', 'password', 'email','is_superuser','is_staff', 'is_active',]

    template_name = 'user_management/updateUser.html'
    success_url = reverse_lazy('listUsers')

# Used to add new user groups
class AddUserGroup(CreateView):
    model = UserGroup
    fields = ['name',]
    template_name = 'user_management/addUserGroup.html'
    success_url = reverse_lazy('listUserGroups')

# All user groups list view
class ListUserGroups(ListView):
    template_name = 'user_management/listUserGroups.html'
    context_object_name = 'all_userGroups'

    def get_queryset(self):
        return UserGroup.objects.all()

# Detailed view of a specific user group
class DetailsUserGroup(DetailView):
    model = UserGroup
    context_object_name = 'userGroup'
    template_name = 'user_management/detailsUserGroup.html'

class UpdateUserGroup(UpdateView):
    model = UserGroup
    fields = ['name', ]
    template_name = 'user_management/updateUserGroup.html'
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
    fields = ['user','user_team']
    template_name = 'user_management/addUserToTeam.html'
    success_url = reverse_lazy('listTeams')

def load_teams(request):
    #project_id = request.GET.get('project')
    #milestones = Milestone.objects.filter(project_id=project_id).order_by('name')
    userGroups = UserTeam.objects.all
    return render(request, 'user_management/listUserGroupsExtended.html', {'userGroups': userGroups})

def load_team_members(request):
    project_id = request.GET.get('project')
    members = UserTeamMember.objects.filter(user_team=project_id) #.order_by('name')
    #members = UserTeamMember.objects.all
    return render(request, 'user_management/team_member_dropdown_list_options.html', {'members': members})


# All user group menus list view
def load_user_group_menus(request):
    #project_id = request.GET.get('project')
    #milestones = Milestone.objects.filter(project_id=project_id).order_by('name')
    userGroups = UserGroup.objects.all
    return render(request, 'user_management/listUserGroupMenusExtended.html', {'userGroups': userGroups})

def load_group_menus(request):
    project_id = request.GET.get('project')
    members = UsrGrpPermissions.objects.filter(usergroup=project_id) #.order_by('name')
    #members = UserTeamMember.objects.all
    return render(request, 'user_management/user_group_menu_dropdown_list_options.html', {'members': members})


# Used to add Menus to User Groups
class addMenuToGroup(CreateView):
    model = UsrGrpPermissions
    fields = ['usergroup','privilege']
    template_name = 'user_management/addMenuToGroup.html'
    success_url = reverse_lazy('listTeams')
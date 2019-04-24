from django.urls import path
from . import views

urlpatterns = [

    path('addUserToTeam/', views.AddUserToTeam.as_view(), name='addUserToTeam'),
    path('teams/', views.load_teams, name='teams'),
    path('ajax/load_team_members/', views.load_team_members, name='load_team_members'),

    # USER GROUPS
    path('addUserGroup/', views.AddUserGroup.as_view(), name='addUserGroup'),
    path('listUserGroups/', views.ListUserGroups.as_view(), name='listUserGroups'),
    path('updateUserGroup/<int:pk>/', views.UpdateUserGroup.as_view(), name='updateUserGroup'),
    path('saveUserGroup/', views.save_user_group, name='saveUserGroup'),
    path('updateGroup/', views.update_user_group, name='updateGroup'),
    path('manageGroups/', views.list_manage_group, name='manageUserGroups'),

    # SYSTEM USERS
    path('addUser/', views.AddUser.as_view(), name='addUser'),
    path('', views.user_createview, name='saveUser'),
    path('listUsers/', views.ListUsers.as_view(), name='listUsers'),
    path('detailsUser/<int:pk>/', views.DetailsUser.as_view(), name='detailsUser'),
    path('updateUser/<int:pk>/', views.UpdateUser.as_view(), name='updateUser'),
    path('validateUserName', views.validate_user_name, name='validateUserName'),
    path('searchUnAssignedUsers', views.search_unassigned_users, name='searchUnAssignedUsers'),
    path('save', views.save_user_to_group, name='saveUserToGroup'),

    path('addTeam/', views.AddTeam.as_view(), name='addTeam'),
    path('listTeams/', views.ListTeams.as_view(), name='listTeams'),
    path('detailsTeam/<int:pk>/', views.DetailsTeam.as_view(), name='detailsTeam'),
    path('updateTeam/<int:pk>/', views.UpdateTeam.as_view(), name='updateTeam'),

    path('profile/', views.ProfileView.as_view(), name='my_profile'),

    # ACCESS RIGHTS
    path('listModules/', views.ListSystemModules.as_view(), name='listModules'),
    path('permissionCount/', views.get_permission_count, name='permissionCount'),
    path('modulePermissions/<int:pk>/', views.ListModulePermissions.as_view(), name='listModulePermissions'),
    path('filterSystemModules/', views.filter_system_modules, name='filterSystemModules'),
]

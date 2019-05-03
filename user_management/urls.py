from django.urls import path
from . import views

urlpatterns = [

    path('addUserToTeam/', views.AddUserToTeam.as_view(), name='addUserToTeam'),
    path('teams/', views.load_teams, name='teams'),
    path('ajax/load_team_members/', views.load_team_members, name='load_team_members'),

    # USER GROUPS
    path('addUserGroup/', views.AddUserGroup.as_view(), name='addUserGroup'),
    path('addGlobalUserGroup/', views.AddGlobalUserGroup.as_view(), name='addGlobalUserGroup'),
    path('listUserGroups/', views.ListUserGroups.as_view(), name='listUserGroups'),
    path('manageGlobalGroups/', views.GlobalUserGroups.as_view(), name='manageGlobalGroups'),
    path('updateUserGroup/<int:pk>/', views.UpdateUserGroup.as_view(), name='updateUserGroup'),
    path('updateUserGlobalGroup/<int:pk>/', views.UpdateUserGlobalGroup.as_view(), name='updateUserGlobalGroup'),
    path('saveUserGroup/', views.save_user_group, name='saveUserGroup'),
    path('saveGlobalUserGroup/', views.save_global_user_group, name='saveGlobalUserGroup'),
    path('updateGroup/', views.update_user_group, name='updateGroup'),
    path('updateGlobalGroup/', views.update_global_user_group, name='updateGlobalGroup'),
    path('manageGroups/', views.list_manage_group, name='manageUserGroups'),
    path('manageUserGlobalGroups/', views.list_manage_global_group, name='manageUserGlobalGroups'),
    path('manageGroupPermissions/', views.manage_group_permissions, name='manageGroupPermissions'),
    path('manageGlobalGroupPermissions/', views.manage_global_group_permissions, name='manageGlobalGroupPermissions'),
    path('assignPermissions/', views.ListContentTypes.as_view(), name='assignPermissionsToGroup'),
    path('groupPermissions', views.fetch_permissions_by_module, name='selectPermissionsByModule'),
    path('savePermissions', views.save_group_permissions, name='saveGroupPermissions'),
    path('removePermissions', views.remove_group_permissions, name='deleteGroupPermission'),
    path('deleteGroup', views.delete_user_group, name='deleteUserGroup'),
    path('deleteGlobalUserGroup', views.delete_global_user_group, name='deleteGlobalUserGroup'),

    # SYSTEM USERS
    path('addUser/', views.AddUser.as_view(), name='addUser'),
    path('', views.user_createview, name='saveUser'),
    path('listUsers/', views.ListUsers.as_view(), name='listUsers'),
    path('detailsUser/<int:pk>/', views.DetailsUser.as_view(), name='detailsUser'),
    path('updateUser/<int:pk>/', views.UpdateUser.as_view(), name='updateUser'),
    path('saveUserUpdate/<int:uid>/', views.save_system_user_update, name='saveUserUpdate'),
    path('validateUserName', views.validate_user_name, name='validateUserName'),
    path('searchUnAssignedUsers', views.search_unassigned_users, name='searchUnAssignedUsers'),
    path('searchUnAssignedGlobalUsers', views.search_unassigned_global_users, name='searchUnAssignedGlobalUsers'),
    path('save', views.save_user_to_group, name='saveUserToGroup'),
    path('save', views.save_user_to_global_group, name='saveUserToGlobalGroup'),
    path('removeUser', views.remove_user_from_group, name='removeUserFromGroup'),
    path('removeUserGlobal', views.remove_user_from_global_group, name='removeUserFromGlobalGroup'),
    path('addUserToGlobalGroup', views.add_user_to_global_group, name='addUserToGlobalGroup'),

    path('addTeam/', views.AddTeam.as_view(), name='addTeam'),
    path('listTeams/', views.ListTeams.as_view(), name='listTeams'),
    path('detailsTeam/<int:pk>/', views.DetailsTeam.as_view(), name='detailsTeam'),
    path('updateTeam/<int:pk>/', views.UpdateTeam.as_view(), name='updateTeam'),

    path('profile/', views.ProfileView.as_view(), name='my_profile'),

    # ACCESS RIGHTS
    path('listModules/', views.ListSystemModules.as_view(), name='listModules'),
    path('modulePermissions/<int:pk>/', views.ListModulePermissions.as_view(), name='listModulePermissions'),
    path('filterSystemModules/', views.filter_system_modules, name='filterSystemModules'),
]

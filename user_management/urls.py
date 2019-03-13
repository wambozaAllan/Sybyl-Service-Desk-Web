from django.urls import path
from . import views

urlpatterns = [
    path('addUserGroup/', views.AddUserGroup.as_view(), name='addUserGroup'),

    path('addUserToTeam/', views.AddUserToTeam.as_view(), name='addUserToTeam'),
    path('teams/', views.load_teams, name='teams'),
    path('ajax/load_team_members/', views.load_team_members, name='load_team_members'),

    path('listUserGroups/', views.ListUserGroups.as_view(), name='listUserGroups'),
    path('detailsUserGroup/<int:pk>/', views.DetailsUserGroup.as_view(), name='detailsUserGroup'),
    path('updateUserGroup/<int:pk>/', views.UpdateUserGroup.as_view(), name='updateUserGroup'),
    #path('addUser/', views.AddUser.as_view(), name='addUser'),
    path('addUser/', views.user_createview, name='addUser'),
    path('listUsers/', views.ListUsers.as_view(), name='listUsers'),
    path('detailsUser/<int:pk>/', views.DetailsUser.as_view(), name='detailsUser'),
    path('updateUser/<int:pk>/', views.UpdateUser.as_view(), name='updateUser'),
    path('addTeam/', views.AddTeam.as_view(), name='addTeam'),
    path('listTeams/', views.ListTeams.as_view(), name='listTeams'),
    path('detailsTeam/<int:pk>/', views.DetailsTeam.as_view(), name='detailsTeam'),
    path('updateTeam/<int:pk>/', views.UpdateTeam.as_view(), name='updateTeam'),

    path('profile/', views.ProfileView.as_view(), name='my_profile'),

    path('addMenuToGroup/', views.addMenuToGroup.as_view(), name='addMenuToGroup'),
    path('listUserGroupMenus/', views.load_user_group_menus, name='listUserGroupMenus'),
    path('ajax/load_group_menus/', views.load_group_menus, name='load_group_menus')
]
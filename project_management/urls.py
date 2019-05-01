from django.urls import path, re_path
from . import views

# app_name = 'project_management'
urlpatterns = [
    path('projects/', views.load_all_projects, name='full_project_list'),
    path('ongoing/', views.ProjectListView.as_view(), name='project_list'),
    path('ajax/load_selected_projects/', views.load_selected_projects, name='load_selected_projects'),
    path('projectdoc', views.model_form_upload, name='model_form_upload'),
    path('projectdocs/', views.load_project_documents, name='projectdocs_list'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='project_details'),
    path('complete/', views.CompleteProjectListView.as_view(), name='complete_project_list'),
    path('terminated/', views.TerminatedProjectListView.as_view(), name='terminated_project_list'),
    path('new/', views.ProjectCreateView.as_view(), name='new_project'),
    path('update/<int:pk>/', views.ProjectUpdateView.as_view(), name='update_project'),
    path('download-project-csv/', views.projects_download, name='download_projects_csv'),
    path('download-project-excel/', views.export_projects_xls, name='export_projects_xls'),

    path('milestones/', views.MilestoneListView.as_view(), name='milestone_list'),
    path('milestone/<int:pk>/', views.MilestoneDetailView.as_view(), name='milestone_details'),
    re_path(r'^project-milestones/(?P<project_id>\d+)/$', views.milestone_list_by_project,
            name='project_milestone_list'),
    # path('project-milestones/(?P<project_id>\w+)', views.milestone_list_by_project, name='project_milestone_list'),
    # path('milestones/', views.load_milestones, name='milestone_list'),
    path('ajax/load_task_milestoneI_list/', views.load_task_milestoneI_list, name='load_task_milestoneI_list'),
    path('milestones/new/', views.MilestoneCreateView.as_view(), name='new_milestone'),
    path('milestone/update/<int:pk>/', views.MilestoneUpdateView.as_view(), name='update_milestone'),
    path('ajax/load-task-milestones/', views.load_task_milestones, name='load-task-milestones'),

    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('task/<int:pk>/', views.TaskDetailView.as_view(), name='task_details'),
    re_path(r'^tasks-project/(?P<project_id>\d+)/$', views.task_list_by_project, name='project_task_list'),
    re_path(r'^tasks-milestone/(?P<milestone_id>\d+)/$', views.task_list_by_milestone, name='milestone_task_list'),
    path('tasks/new/', views.TaskCreateView.as_view(), name='new_task'),
    path('task-update/<int:pk>/', views.TaskUpdateView.as_view(), name='update_task'),

    path('addIncident/', views.AddIncident.as_view(), name='addIncident'),
    path('listIncidents/', views.ListIncidents.as_view(), name='listIncidents'),
    path('detailsIncident/<int:pk>/', views.DetailsIncident.as_view(), name='detailsIncident'),
    path('updateIncident/<int:pk>/', views.UpdateIncident.as_view(), name='updateIncident'),

    path('listAllPriorities/', views.ListAllPriorities.as_view(), name='listAllPriorities'),
    path('addPriority/', views.AddPriority.as_view(), name='addPriority'),
    path('updatePriority/<int:pk>/', views.UpdatePriority.as_view(), name='updatePriority'),
    path('deletePriority/<int:pk>', views.DeletePriority.as_view(), name="deletePriority"),
    path('validatePriorityName/', views.validatePriorityName, name='validatePriorityName'),

    path('listAllStatuses/', views.ListAllStatuses.as_view(), name='listAllStatuses'),
    path('addStatus/', views.AddStatus.as_view(), name='addStatus'),
    path('updateStatus/<int:pk>/', views.UpdateStatus.as_view(), name='updateStatus'),
    path('deleteStatus/<int:pk>/', views.DeleteStatus.as_view(), name="deleteStatus"),
    path('validateStatusName/', views.ValidateStatusName, name='validateStatusName'),

    path('addProject/', views.AddProject.as_view(), name='addProject'),
    path('listProjects/', views.ListProjects.as_view(), name='listProjects'),
    path('updateProject/<int:pk>', views.UpdateProject.as_view(), name='updateProject'),
    path('detailsProject/<int:pk>', views.DetailProject.as_view(), name='detailsProject'),
    path('validateProjectName/', views.validateProjectName, name='validateProjectName'),

    path('addProjectTeam/', views.AddProjectTeam.as_view(), name='addProjectTeam'),
    path('listProjectTeams/', views.ListProjectTeams.as_view(), name='listProjectTeams'),
    path('updateProjectTeam/<int:pk>', views.UpdateProjectTeam.as_view(), name='updateProjectTeam'),
    path('deleteProjectTeam/<int:pk>', views.DeleteProjectTeam.as_view(), name='deleteProjectTeam'),
    path('validateProjectTeamName/', views.validateProjectTeamName, name='validateProjectTeamName'),

    path('addProjectMember/', views.AddProjectMember.as_view(), name='addProjectMember'),
    path('listProjectMembers/', views.ListProjectMembers.as_view(), name='listProjectMembers'),
    path('deleteProjectMember/<int:pk>', views.DeleteProjectMember.as_view(), name='deleteProjectMember'),
    path('validateProjectMember/', views.validateProjectMember, name='validateProjectMember'),

    path('listAllRoles/', views.ListAllRoles.as_view(), name='listAllRoles'),
    path('addRole/', views.AddRole.as_view(), name='addRole'),
    path('updateRole/<int:pk>/', views.UpdateRole.as_view(), name='updateRole'),
    path('deleteRole/<int:pk>/', views.DeleteRole.as_view(), name="deleteRole"),
    path('validateRoleName/', views.ValidateRoleName, name='validateRoleName'),

]

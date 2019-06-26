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
    path('milestone/detail/<int:pk>/', views.MilestoneDetailView.as_view(), name='milestone_details'),
    re_path(r'^project-milestones/(?P<project_id>\d+)/$', views.milestone_list_by_project,
            name='project_milestone_list'),
    # path('project-milestones/(?P<project_id>\w+)', views.milestone_list_by_project, name='project_milestone_list'),
    # path('milestones/', views.load_milestones, name='milestone_list'),
    path('ajax/load_task_milestoneI_list/', views.load_task_milestoneI_list, name='load_task_milestoneI_list'),
    path('milestones/new/', views.MilestoneCreateView.as_view(), name='new_milestone'),
    path('milestone/update/<int:pk>/', views.MilestoneUpdateView.as_view(), name='update_milestone'),
    path('ajax/load-task-milestones/', views.load_task_milestones, name='load-task-milestones'),
    path('listProjectMilestones/', views.list_project_milestones, name='listProjectMilestones'),
    path('populateMilestone/', views.populate_milestone_view, name='populateMilestone'),
    path('populateMilestoneStatus/', views.populate_milestone_status, name='populateMilestoneStatus'),
    path('saveMilestone', views.save_milestone, name='saveMilestone'),
    path('validateMilestoneName', views.validateMilestoneName, name='validateMilestoneName'),
    path('updateProjectMilestone/', views.update_project_milestone, name='updateProjectMilestone'),
    
    path('populateTaskView', views.populate_task_view, name='populateTaskView'),
    path('populateStatusMilestone', views.populate_status_milestone, name='populateStatusMilestone'),
    path('tasks/', views.TaskListView.as_view(), name='listTasks'),
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('task/<int:pk>/', views.TaskDetailView.as_view(), name='task_details'),
    # re_path(r'^tasks-project/(?P<project_id>\d+)/$', views.task_list_by_project, name='project_task_list'),
    re_path(r'^tasks-milestone/(?P<milestone_id>\d+)/$', views.task_list_by_milestone, name='milestone_task_list'),
    path('tasks/new/', views.TaskCreateView.as_view(), name='new_task'),
    path('task-update/<int:pk>/', views.TaskUpdateView.as_view(), name='update_task'),
    path('listProjectTasks', views.tasklist_by_project, name='listProjectTasks'),
    path('addProjectTasks', views.add_project_tasks, name='addProjectTasks'),
    path('validateTaskName/', views.validateTaskName, name='validateTaskName'),
    path('saveProjectTask', views.save_project_tasks, name='saveProjectTask'),
    path('milestoneTasks', views.view_tasks_under_milestone, name='milestoneTasks'),
    path('addMilestoneTask', views.add_milestone_specific_task, name='addMilestoneTask'),
    path('saveMilestoneTask', views.save_milestone_tasks, name='saveMilestoneTask'),

    path('addIncident/', views.AddIncident.as_view(), name='addIncident'),
    path('addProjectIncident/', views.AddProjectIncident.as_view(), name='addProjectIncident'),
    path('listIncidents/', views.ListIncidents.as_view(), name='listIncidents'),
    path('listProjectIncidents', views.list_project_incidents, name='listProjectIncidents'),
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

    path('addProject/', views.addProject, name='addProject'),
    path('listProjects/', views.ListProjects.as_view(), name='listProjects'),
    path('updateProject/<int:pk>', views.UpdateProject.as_view(), name='updateProject'),
    path('detailsProject/<int:pk>', views.DetailProject.as_view(), name='detailsProject'),
    path('validateProjectName/', views.validateProjectName, name='validateProjectName'),
    path('formatProjectCode/', views.format_project_code, name='formatProjectCode'),

    path('addProjectTeam/', views.add_project_team, name='addProjectTeam'),
    path('listProjectTeams/', views.ListProjectTeams.as_view(), name='listProjectTeams'),
    path('updateProjectTeam/<int:pk>', views.UpdateProjectTeam.as_view(), name='updateProjectTeam'),
    path('deleteProjectTeam/<int:pk>', views.DeleteProjectTeam.as_view(), name='deleteProjectTeam'),
    path('validateProjectTeamName/', views.validateProjectTeamName, name='validateProjectTeamName'),
    path('validateProjectAssigned/', views.validateProjectAssigned, name='validateProjectAssigned'),

    path('addProjectTeamMember/', views.add_project_team_member, name='addProjectTeamMember'),
    path('adminAddProjectTeamMember/', views.AddProjectTeamMember.as_view(), name='adminAddProjectTeamMember'),
    path('listProjectTeamMembers/', views.ListProjectTeamMembers.as_view(), name='listProjectTeamMembers'),
    path('updateProjectTeamMember/<int:pk>', views.UpdateProjectTeamMember.as_view(), name='updateProjectTeamMember'),
    path('detailProjectTeamMembers/', views.detail_team_member, name='detailProjectTeamMembers'),
    path('deleteProjectTeamMember/', views.remove_project_team_member, name='deleteProjectTeamMember'),
    path('validateProjectTeamAssigned/', views.validateProjectTeamAssigned, name='validateProjectTeamAssigned'),
    path('saveTeamMember/', views.save_team_member, name='saveTeamMember'),

    path('listAllRoles/', views.ListAllRoles.as_view(), name='listAllRoles'),
    path('addRole/', views.AddRole.as_view(), name='addRole'),
    path('updateRole/<int:pk>/', views.UpdateRole.as_view(), name='updateRole'),
    path('deleteRole/<int:pk>/', views.DeleteRole.as_view(), name="deleteRole"),
    path('validateRoleName/', views.ValidateRoleName, name='validateRoleName'),

    path('getTeamMembers/', views.get_team_members, name='getTeamMembers'),
    path('setColorCode/', views.set_priority_color_code, name='setColorCode'),
    path('changeIncidentStatus/<int:pk>', views.change_status_on_task, name='changeIncidentStatus'),

    path('projectForum/', views.project_forum, name='tabProjectForum'),
    path('createForum/', views.create_project_forum, name='createProjectForum'),
    path('forumReplies/', views.manage_forum_replies, name='manageForumReplies'),
    path('deleteChatMessage/', views.delete_forum_message, name='deleteChatMessage'),
    path('deleteReply/', views.delete_forum_reply, name='deleteChatReply'),

    path('listTeam/', views.list_project_team, name='tabListTeam'),

    path('projectsla/', views.ProjectSLAList.as_view(), name='projectsla'),
    
    path('addSLA/', views.AddSla.as_view(), name='addSla'),
]

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
    path('updateProjectMilestone/<int:pk>', views.UpdateProjectMilestone.as_view(), name='updateProjectMilestone'),
    path('updateOpenMilestone/<int:pk>', views.UpdateOpenMilestone.as_view(), name='updateOpenMilestone'),
    path('updateOnholdMilestone/<int:pk>', views.UpdateOnholdMilestone.as_view(), name='updateOnholdMilestone'),
    path('updateTerminatedMilestone/<int:pk>', views.UpdateTerminatedMilestone.as_view(), name='updateTerminatedMilestone'),
    path('updateCompletedMilestone/<int:pk>', views.UpdateCompletedMilestone.as_view(), name='updateCompletedMilestone'),
    path('detailsProjectMilestone/<int:pk>', views.DetailsProjectMilestone.as_view(), name='detailsProjectMilestone'),
    path('checkMilestoneStatus/', views.check_milestone_status, name='checkMilestoneStatus'),
    path('deleteProjectMilestone/', views.delete_project_milestone, name='deleteProjectMilestone'),
    path('onholdMilestones/', views.onhold_project_milestones, name='onholdMilestones'),
    path('openMilestones/', views.open_milestones, name='openMilestones'),
    path('terminatedMilestones/', views.terminated_project_milestones, name='terminatedMilestones'),
    path('completedMilestones/', views.completed_project_milestones, name='completedMilestones'),
    path('saveupdateProjectMilestone/<int:pk>', views.save_update_milestone, name='saveupdateProjectMilestone'),
    path('milestoneCount/', views.milestone_count, name='milestoneCount'),
    

  
    path('populateTaskView', views.populate_task_view, name='populateTaskView'),    


    path('tasks/', views.TaskListView.as_view(), name='listTasks'),
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('task/<int:pk>/', views.TaskDetailView.as_view(), name='task_details'),
    # re_path(r'^tasks-project/(?P<project_id>\d+)/$', views.task_list_by_project, name='project_task_list'),
    re_path(r'^tasks-milestone/(?P<milestone_id>\d+)/$', views.task_list_by_milestone, name='milestone_task_list'),
    path('tasks/new/', views.TaskCreateView.as_view(), name='new_task'),
    path('task-update/<int:pk>/', views.TaskUpdateView.as_view(), name='update_task'),
    path('listProjectTasks', views.tasklist_by_project, name='listProjectTasks'),
    path('validateTaskName/', views.validateTaskName, name='validateTaskName'),
    path('saveProjectTask', views.save_project_tasks, name='saveProjectTask'),
    path('milestoneTasks', views.view_tasks_under_milestone, name='milestoneTasks'),
    path('addMilestoneTask', views.add_milestone_specific_task, name='addMilestoneTask'),
    path('addMilestoneTasks', views.add_milestone_tasks, name='addMilestoneTasks'),
    path('saveMilestoneTask', views.save_milestone_tasks, name='saveMilestoneTask'),
    path('updateProjectTask/<int:pk>', views.UpdateProjectTask.as_view(), name='updateProjectTask'),
    path('updateMilestoneTask/<int:pk>', views.UpdateMilestoneTask.as_view(), name='updateMilestoneTask'),
    path('detailsProjectTask/<int:pk>', views.DetailsProjectTask.as_view(), name='detailsProjectTask'),
    path('deleteTask/', views.delete_task, name='deleteTask'),
    path('openTasks/', views.open_project_tasks, name="openTasks"),
    path('onholdTasks/', views.onhold_tasks, name="onholdTasks"),
    path('terminatedTasks/', views.terminated_tasks, name="terminatedTasks"),
    path('completedTasks/', views.completed_tasks, name="completedTasks"),
    path('updateOpenTask/<int:pk>', views.UpdateOpenTask.as_view(), name='updateOpenTask'),
    path('updateCompletedTask/<int:pk>', views.UpdateCompletedTask.as_view(), name='updateCompletedTask'),
    path('updateOnholdTask/<int:pk>', views.UpdateOnholdTask.as_view(), name='updateOnholdTask'),
    path('updateTerminatedTask/<int:pk>', views.UpdateTerminatedTask.as_view(), name='updateTerminatedTask'),
    path('saveupdateProjectTask/<int:pk>', views.save_update_task, name='saveupdateProjectTask'),
    path('taskCount/', views.task_count, name='taskCount'),
    path('assignedTaskMembers/', views.assigned_task_members, name="assignedTaskMembers"),
    path('assignedTaskMembersMilestone/', views.assigned_task_members_milestone, name="assignedTaskMembersMilestone"),
    path('assignTaskMembers/', views.assign_task_members, name="assignTaskMembers"),
    path('deassignTaskMembers/', views.deassign_task_members, name="deassignTaskMembers"),
    path('deassignTaskMembersMilestone/', views.deassign_task_members_milestone, name="deassignTaskMembersMilestone"),
    path('checkTeamMembers/', views.check_team_members, name="checkTeamMembers"),
    path('checkAssignedTaskMembers/', views.check_assigned_task_members, name="checkAssignedTaskMembers"),
    path('saveMembersAssignedTask/', views.save_members_assigned_task, name="saveMembersAssignedTask"),

    path('addIncident/', views.AddIncident.as_view(), name='addIncident'),
    path('addProjectIncident/', views.AddProjectIncident.as_view(), name='addProjectIncident'),
    path('listIncidents/', views.ListIncidents.as_view(), name='listIncidents'),
    path('listProjectIncidents', views.list_project_incidents, name='listProjectIncidents'),
    path('detailsIncident/<int:pk>/', views.DetailsIncident.as_view(), name='detailsIncident'),
    path('detailsProjectIncident/<int:pk>/', views.DetailsProjectIncident.as_view(), name='detailsProjectIncident'),
    path('updateIncident/<int:pk>/', views.UpdateIncident.as_view(), name='updateIncident'),
    path('updateProjectIncident/<int:pk>/', views.UpdateProjectIncident.as_view(), name='updateProjectIncident'),
    path('addComment/', views.add_comment, name="addComment"),
    path('listIncidentComments/', views.list_incident_comments, name="listIncidentComments"),
    path('onholdIncidents/', views.onhold_project_incidents, name="onholdIncidents"),
    path('terminatedIncidents/', views.terminated_project_incidents, name="terminatedIncidents"),
    path('completedIncidents/', views.completed_project_incidents, name="completedIncidents"),
    path('validateIncidentName/', views.validate_incident_name, name="validateIncidentName"),
    
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
    path('uploadDocument/', views.UploadDocument.as_view(), name="uploadDocument" ),

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
    path('saveupdateTeamMember/<int:pk>', views.save_update_team_member, name='saveupdateTeamMember'),

    path('listAllRoles/', views.ListAllRoles.as_view(), name='listAllRoles'),
    path('addRole/', views.AddRole.as_view(), name='addRole'),
    path('updateRole/<int:pk>/', views.UpdateRole.as_view(), name='updateRole'),
    path('deleteRole/<int:pk>/', views.DeleteRole.as_view(), name="deleteRole"),
    path('validateRoleName/', views.ValidateRoleName, name='validateRoleName'),

    path('getTeamMembers/', views.get_team_members, name='getTeamMembers'),
    path('setColorCode/', views.set_priority_color_code, name='setColorCode'),

    path('projectForum/', views.project_forum, name='tabProjectForum'),
    path('createForum/', views.create_project_forum, name='createProjectForum'),
    path('forumReplies/', views.manage_forum_replies, name='manageForumReplies'),
    path('deleteChatMessage/', views.delete_forum_message, name='deleteChatMessage'),
    path('deleteReply/', views.delete_forum_reply, name='deleteChatReply'),

    path('listTeam/', views.list_project_team, name='tabListTeam'),
    path('viewAssignedMembers/', views.view_assigned_members, name='viewAssignedMembers'),

    path('projectsla/', views.project_sla_list, name='projectsla'),
    path('addSLA/', views.AddSla.as_view(), name='addSla'),
    path('saveSLA/', views.save_sla, name='saveSLA'),
    path('updateSLA/<int:pk>/', views.UpdateSLA.as_view(), name='updateSLA'),
    path('update2SLA/', views.save_sla_update, name='saveSLAupdate'),

    path('projectEscalations/', views.ProjectEscalationList.as_view(), name='tabProjectEscalation'),
    path('addEscalationLevel/', views.AddEscalation.as_view(), name='addEscalationLevel'),
    path('saveEscalationLevel/', views.save_escation_level, name='saveEscalationLevels'),
    path('updateEscalation/<int:pk>/', views.UpdateEscalationLevel.as_view(), name='updateEscalation'),
    path('saveEscalationUpdate/', views.update_escation_level_update, name='saveEscalationUpdate'),
    path('manageEscalatedUsers/', views.manage_escalated_users, name='manageEscalatedUsers'),
    path('deEscalate/', views.de_escalate_user, name='deEscalateUser'),
    path('escalateUser/', views.escalate_user, name='escalateNewUser'),
    path('saveEscalatedUser/', views.save_escalated_user, name='saveEscalatedUser'),
    path('auditlogs/', views.view_audit_logs, name='listauditlogs'),
    path('auditlogsfilter/', views.filter_audit_logs, name='auditlogsfilter'),
    path('auditlogsfilter2/', views.all_companies_filter_auditlogs, name='auditlogsfilterallcomp'),
    path('manageSLAEscalations/', views.manage_sla_esclations, name='manageSLAEscalations'),
]

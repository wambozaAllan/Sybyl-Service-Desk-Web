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

    path('milestones/', views.project_milestones_by_user, name='milestone_list'),
    path('milestone/detail/<int:pk>/', views.MilestoneDetailView.as_view(), name='milestone_details'),
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
    path('milestonesContainer/', views.milestone_container, name='milestonesContainer'),
    

  
    path('populateTaskView', views.populate_task_view, name='populateTaskView'),    
    path('createTask', views.create_tasks_by_project, name="createTask"),
    path('tasks_list/', views.task_list_by_users, name='task_list'),
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
    path('tasks/', views.tasks_container, name="tasksContainer"),
    path('saveTeamTasks', views.save_team_project_tasks, name='saveTeamTasks'),
    

    path('addIncident/', views.AddIncident.as_view(), name='addIncident'),
    path('addProjectIncident/', views.AddProjectIncident.as_view(), name='addProjectIncident'),
    path('incident_list/', views.list_incidents_by_project, name='listIncidents'),
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
    path('listIncidents/', views.incident_container, name="incidentContainer"),
    path('createIncident/', views.create_incident, name="createIncident"),
    path('saveIncident/', views.save_incident, name="saveIncident"),
    
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
    # path('listProjects/', views.ListProjects.as_view(), name='listProjects'),
    path('listProjects/', views.list_projects, name='listProjects'),
    path('updateProject/<int:pk>', views.UpdateProject.as_view(), name='updateProject'),
    path('detailsProject/<int:pk>', views.DetailProject.as_view(), name='detailsProject'),
    path('validateProjectName/', views.validateProjectName, name='validateProjectName'),
    path('uploadDocument/', views.upload_document, name="uploadDocument" ),

    path('addProjectTeam/', views.add_project_team, name='addProjectTeam'),
    path('adminAddProjectTeam/', views.AdminAddProjectTeam.as_view(), name='adminAddProjectTeam'),
    path('listProjectTeams/', views.ListProjectTeams.as_view(), name='listProjectTeams'),
    path('updateProjectTeam/<int:pk>', views.UpdateProjectTeam.as_view(), name='updateProjectTeam'),
    path('deleteProjectTeam/<int:pk>', views.DeleteProjectTeam.as_view(), name='deleteProjectTeam'),
    path('validateProjectTeamName/', views.validateProjectTeamName, name='validateProjectTeamName'),
    path('validateProjectAssigned/', views.validateProjectAssigned, name='validateProjectAssigned'),

    path('addProjectTeamMember/', views.add_project_team_member, name='addProjectTeamMember'),
    path('adminAddProjectTeamMember/', views.admin_add_project_team_member, name='adminAddProjectTeamMember'),
    path('listProjectTeamMembers/', views.ListProjectTeamMembers.as_view(), name='listProjectTeamMembers'),
    path('detailProjectTeamMembers/', views.detail_team_member, name='detailProjectTeamMembers'),
    path('adminDetailProjectTeamMembers/', views.admin_detail_team_member, name='adminDetailProjectTeamMembers'),
    path('deleteProjectTeamMember/', views.remove_project_team_member, name='deleteProjectTeamMember'),
    path('validateProjectTeamAssigned/', views.validateProjectTeamAssigned, name='validateProjectTeamAssigned'),
    path('saveTeamMember/', views.save_team_member, name='saveTeamMember'),

    path('getTeamMembers/', views.get_team_members, name='getTeamMembers'),
    path('setColorCode/', views.set_priority_color_code, name='setColorCode'),

    path('projectForum/', views.project_forum, name='tabProjectForum'),
    path('createForum/', views.create_project_forum, name='createProjectForum'),
    path('forumReplies/', views.manage_forum_replies, name='manageForumReplies'),
    path('deleteChatMessage/', views.delete_forum_message, name='deleteChatMessage'),
    path('deleteReply/', views.delete_forum_reply, name='deleteChatReply'),

    path('listTeam/', views.list_project_team, name='tabListTeam'),
    path('viewAssignedMembers/', views.view_assigned_members, name='viewAssignedMembers'),

    path('auditlogs/', views.view_audit_logs, name='listauditlogs'),
    path('auditlogsfilter/', views.filter_audit_logs, name='auditlogsfilter'),
    path('auditlogsfilter2/', views.all_companies_filter_auditlogs, name='auditlogsfilterallcomp'),    
    
    # TIMESHEETS 
    path('addTimesheet/', views.add_new_timesheet, name='addNewTimesheet'),
    path('addTimesheetOnCalender/', views.add_new_timesheet_from_calender, name='addTimesheetOnCalender'),
    path('addTimesheetOnDatePaginator/', views.add_new_timesheet_from_datepaginator, name='addTimesheetOnDatePaginator'),
    path('projectMilestone', views.fetch_milestones_by_project, name='selectMilestonesByProject'),
    path('tasksMilestone', views.fetch_tasks_by_milestone, name='selectTasksByMilestone'),
    path('myTimesheets/', views.daily_timesheets_pane, name='myTimesheets'),
    path('approveTimesheets/', views.approve_timesheet_pane, name='approveTimesheets'),
    path('saveTimeSheet', views.save_new_timesheet, name='saveTimeSheet'),
    path('updateTimesheet', views.update_timesheet, name='updateTimesheet'),
    path('updateTimesheetPaginator', views.update_timesheet_paginator, name='updateTimesheetPaginator'),
    path('saveUpdateTimesheet', views.save_update_timesheet, name='saveUpdateTimesheet'),
    path('deleteTimesheet', views.delete_timesheet, name='deleteTimesheet'),
    path('deleteTimesheetPaginator', views.delete_timesheet_in_paginator, name='deleteTimesheetPaginator'),
    path('sendTimesheet', views.send_timesheet_for_approval, name='sendTimesheetForApproval'),
    path('sendPaginatorTimesheetForApproval', views.send_timesheet_for_approval_paginator, name='sendPaginatorTimesheetForApproval'),
    path('pendingApproval', views.timesheet_pending_approval, name='timesheetPendingApproval'),
    path('saveTimesheetApprovals', views.save_timesheet_approvals, name='saveTimesheetApprovals'),
    path('approvedTimesheetsTab', views.manage_approved_timesheets, name='approvedTimesheetsTab'),
    path('updateTimesheetApproval', views.update_timesheet_approval, name='updateTimesheetApproval'),
    path('userApprovedTimesheets', views.view_user_approved_timesheets, name='userApprovedTimesheets'),
    path('filterPenddingTimesheets', views.filter_pending_daily_timesheets_by_date, name='filterPendingTimesheets'),
    path('filterDailyProvedTimesheets', views.filter_daily_proved_timesheets, name='filterDailyProvedTimesheets'),
    path('filterAllUsersPendingTMs', views.filter_all_member_unapproved_timesheets, name='filterAllUsersPendingTMs'),
    path('filterAllUsersApprovedTMs', views.filter_all_member_approved_timesheets, name='filterAllUsersApprovedTMs'),
    path('analyseAllTimesheets', views.timesheets_report, name='analyseAllTimesheets'),
    path('userGeneralTimesheetReport', views.user_general_timesheet_report, name='userGeneralTimesheetReport'),

    path('viewTaskDetails/<int:pk>', views.DetailsProjectTask.as_view(), name='viewTaskDetails'),
    path('userRejectedTimesheets', views.manage_rejected_timesheets, name='userRejectedTimesheets'),
    path('resubmitTimesheet', views.resubmit_timesheet, name='resubmitTimesheet'),
    path('saveResentTimesheet', views.save_resent_timesheet, name='saveResentTimesheet'),
    path('paginatorResubmitTimesheet', views.paginator_resubmit_timesheet, name='paginatorResubmitTimesheet'),
    path('saveResentPaginatorTimesheet', views.save_resent_paginator_timesheet, name='saveResentPaginatorTimesheet'),
    path('viewTimesheetResubmissions', views.manage_timesheet_resubmissions, name='viewTimesheetResubmissions'),
    path('updateApproverComment', views.update_approver_comment, name='updateApproverComment'),
    path('savecalenderTimeSheet', views.save_calender_timesheet, name='savecalenderTimeSheet'),
    path('savePaginatorTimeSheet', views.save_paginator_timesheet, name='savePaginatorTimeSheet'),
    path('calenderTimesheetView', views.calenderTimesheetView, name='calenderTimesheetView'),
    path('timesheetWeeklyReport', views.timesheets_weekly_report, name='timesheetWeeklyReport'),
    path('filterTimesheetsByWeek', views.filter_users_timesheets_by_week, name='filterTimesheetsByWeek'),
    path('filterTimesheetsByDate', views.filter_timesheets_by_date, name='filterTimesheetsByDate'),
    path('tableTimesheetView', views.table_timesheet_view, name='tableTimesheetView'),
    path('listTimesheetView', views.list_timesheet_view, name='listTimesheetView'),
    path('saveUpdateTimesheetPaginator', views.save_update_paginator_timesheet, name='saveUpdateTimesheetPaginator'),

    path('timesheetProjectReport', views.timesheets_project_report, name='timesheetProjectReport'),
    path('filterProjectTimesheetsByWeek', views.filter_project_timesheets_by_week, name='filterProjectTimesheetsByWeek'),
    path('selectDailyTimesheetsByUser', views.select_daily_timesheets_by_user, name='selectDailyTimesheetsByUser'),
    path('selectTableTimesheetsByUser', views.select_table_timesheets_by_user, name='selectTableTimesheetsByUser'),

    path('timesheetMonthlyReport', views.timesheet_monthly_report, name='timesheetMonthlyReport'),
    path('filterMonthlyTimesheets', views.filter_monthly_timesheets, name='filterMonthlyTimesheets'),
    path('filterMonthlyTimesheetsByDate', views.filter_monthly_timesheets_by_date, name='filterMonthlyTimesheetsByDate'),

    # Schedules plans 
    path('schedulePlan', views.timesheets_schedule_pane, name='schedulePlan'),
    
    # REPORTS
    path('staffUtilization/', views.staff_utilization, name="staffUtilization"),
    path('staffUtilizationReport/', views.staff_utilization_report, name="staffUtilizationReport"),
    path('exportReport/', views.export_staff_utilization, name="exportReport"),
    path('exportPdf/', views.export_pdf_utilization, name="exportPdf"),
    path('taskReport/', views.task_report_page, name="taskReport"),
    path('exportTaskReport/', views.export_task_report, name="exportTaskReport"),
    path('previewTaskReport/', views.preview_task_report, name="previewTaskReport"),


    # Project code
    path('listCodeFormat/', views.ListCodeFormat.as_view(), name='listCodeFormat'),
    path('addCodeFormat/', views.AddCodeFormat.as_view(), name='addCodeFormat'),
    path('updateCodeFormat/<int:pk>/', views.UpdateCodeFormat.as_view(), name='updateCodeFormat'),
    path('deleteCodeFormat/<int:pk>', views.DeleteCodeFormat.as_view(), name="deleteCodeFormat"),
    path('validateProjectCode/', views.validate_project_code, name='validateProjectCode'),
    path('checkProjectCodeExist/', views.check_project_code_exists, name='checkProjectCodeExist'),
    path('populateUpload/', views.populate_upload_document, name='populateUpload'),
    path('addMilestone/', views.load_add_milestone, name='addMilestone'),
    path('selectMembersByProject', views.fetch_members_by_project, name='selectMembersByProject'),

    path('customerRequests/', views.customer_request_home, name="customerRequests"),
    path('customerRequestsReports/', views.customer_requests_reports_home, name="customerRequestsReports"),
    path('addCustomerRequest/', views.AddCustomerRequest.as_view(), name="addCustomerRequest"),
    path('saveCustomerRequest/', views.save_customer_request, name='saveCustomerRequest'),
    path('updateCustomerRequest/<int:pk>/', views.UpdateCustomerRequest.as_view(), name='updateCustomerRequest'),
    path('saveRequestupdate/', views.save_customer_request_update, name='saveRequestupdate'),
    path('viewCustomerRequest/<int:pk>/', views.ViewCustomerRequest.as_view(), name='viewCustomerRequest'),
    path('deleteCustomerRequest', views.delete_customer_request, name='deleteCustomerRequest'),
    path('manageCustomerRequest/', views.manage_customer_request_pane, name="manageCustomerRequest"),
    path('changeRequestState/', views.change_customer_request_state, name="changeRequestState"),
    path('saveUpdateCustomerRequestState/', views.save_update_customer_request_state, name="saveUpdateCustomerRequestState"),
    path('loadCustomerRequestActivities/', views.load_customer_request_activities, name="loadCustomerRequestActivities"),
    path('addNewCustomerRequestActivity/', views.add_customer_request_activity, name="addNewCustomerRequestActivity"),
    path('saveCustomerRequestActivity/', views.save_customer_request_activity, name="saveCustomerRequestActivity"),
    path('loadCustomerRequestTeam/', views.load_customer_request_team_members, name="loadCustomerRequestTeam"),
    path('deleteCustomerRequestEngineer', views.delete_customer_request_engineer, name='deleteCustomerRequestEngineer'),
    path('addCustomerRequestMember', views.add_customer_request_member, name='addCustomerRequestMember'),
    path('customeRequestReload', views.customer_request_reload, name='customeRequestReload'),

    path('listIssueTypes', views.issue_type_home, name="listIssueTypes"),
    path('updateIssueType/<int:pk>/', views.UpdateIssueType.as_view(), name='updateIssueType'),
    path('addIssueType/', views.AddIssueType.as_view(), name='addIssueType'),
    path('validateIssueType', views.validate_issuetype, name='validateIssueType'),
    path('deleteIssueType/<int:pk>', views.DeleteIssueType.as_view(), name="deleteIssueType"),
    path('assignRequests', views.assign_customer_request, name='assignRequests'),
    path('saveAssignedCustomerRequests', views.save_assigned_customerrequests, name='saveAssignedCustomerRequests'),
    path('saveAssignedEngineer', views.save_assigned_engineer, name='saveAssignedEngineer'),
    path('customerRequestSetData', views.customer_request_set_data, name='customerRequestSetData'),
    
    path('SLAsByCustomer', views.fetch_SLAs_by_customer, name='SLAsByCustomer'),
    path('requestsBySLA', views.fetch_requests_by_sla, name='requestsBySLA'),
    
    # CUSTOMER URLS
    path('listCustomerProjects/', views.list_customer_projects, name='listCustomerProjects'),
    path('addCustomerProjects/', views.add_customer_projects, name='addCustomerProjects'),
    path('returnStatus/', views.return_status, name='returnStatus'),
    path('saveProject/', views.save_project, name='saveProject'),
    path('assignedUsers/', views.assigned_users, name='assignedUsers'),
    path('updateCustomerProject/<int:pk>', views.UpdateCustomerProject.as_view(), name='updateCustomerProject'),

    
    path('listCustomerServiceRequests/', views.list_customer_service_requests, name='listCustomerServiceRequests'),
    path('listCustomerSLAs/', views.list_customer_sla, name='listCustomerSLAs'),
    path('checkTask/', views.check_task, name='checkTask'),
    
    path('dailyTimesheetRReport', views.timesheet_daily_report, name='dailyTimesheetRReport'),
    path('filterDailyTimesheetRReport', views.filter_timesheet_daily_report, name='filterDailyTimesheetRReport'),
    path('exportDailyTMReport', views.export_daily_tm_report, name='exportDailyTMReport'),
    path('exportEmailDailyTMReport', views.export_and_send_email_daily_tm_report, name='exportEmailDailyTMReport'),
    path('detailedTaskReport', views.detailed_task_report_pane, name='detailedTaskReport'),
    path('filterDetailedTaskTimesheetRReport', views.filter_detailed_task_timesheet_report, name='filterDetailedTaskTimesheetRReport'),

    path('exportTimesheetTaskReport', views.export_timesheet_task_report, name='exportTimesheetTaskReport'),
    path('exportEmailTimesheetTaskReport', views.export_email_timesheet_task_report, name='exportEmailTimesheetTaskReport'),

    path('timesheetDefaulterList', views.timesheet_defaulter_list, name='timesheetDefaulterList'),
    path('sendTimesheetEmailReminder', views.send_timesheet_email_reminder, name='sendTimesheetEmailReminder'),
]

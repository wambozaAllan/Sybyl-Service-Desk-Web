import datetime, time
from datetime import date, datetime, timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone

from company_management.models import Company
from user_management.models import User, UserTeamMember

from ckeditor.fields import RichTextField
# color palette import
from colorfield.fields import ColorField
from simple_history.models import HistoricalRecords


# PRIORITIES
class Priority(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=255, blank=True)
    color = ColorField(default="#fff")
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# STATUS
class Status(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=255, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Stage(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)


# ROLE
class Role(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=255, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# PROJECT
class Project(models.Model):
    name = models.CharField(max_length=100)
    project_status = models.ForeignKey(Status, null=True, blank=True, on_delete=models.SET_NULL)
    company = models.ManyToManyField(Company)
    description = RichTextField(null=True, blank=True)
    project_code = models.CharField(max_length=255, null=True, blank=True)
    estimated_cost = models.FloatField(default=0.00)
    final_cost = models.FloatField(null=True, blank=True)
    logo = models.ImageField(null=True, blank=True, upload_to='logos/')
    estimated_start_date = models.DateField(null=True, blank=True)
    estimated_end_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    @property
    def completion(self):
        status_complete = Status.objects.get(name="Completed")
        status_terminate = Status.objects.get(name="Terminated")
        
        terminated_milestones = Milestone.objects.filter(project_id=self.id, status=status_terminate.id).count()
        completed_milestones = Milestone.objects.filter(project_id=self.id, status=status_complete.id).count()
        completed = terminated_milestones + completed_milestones
        # completed           = Milestone.objects.filter(project_id=self.id, status='Completed').count()
        total_milestones    = Milestone.objects.filter(project_id=self.id).count()
        completion_level    = 0
        if total_milestones > 0:
            if completed > 0:
                completion_level  = round(((completed / total_milestones) * 100),2)
        return completion_level
    
    @property
    def task_completion(self):
        status_complete = Status.objects.get(name="Completed")
        status_terminate = Status.objects.get(name="Terminated")

        terminated_tasks = Task.objects.filter(project_id=self.id, status=status_terminate.id).count()
        tasks_complete = Task.objects.filter(project_id=self.id, status=status_complete.id).count()

        total_tasks         = Task.objects.filter(project_id=self.id).count()
        completed_tasks = terminated_tasks + tasks_complete
    
        completion_percet = 0
        if total_tasks > 0 and completed_tasks > 0:
            completion_percet = round(((completed_tasks / total_tasks) * 100),2)
        return completion_percet
    
    @property
    def incident_completion(self):
        status_complete = Status.objects.get(name="Completed")
        status_terminate = Status.objects.get(name="Terminated")

        incidents_terminated = Incident.objects.filter(project_id=self.id, status=status_terminate.id).count()
        incidents_complete = Incident.objects.filter(project_id=self.id, status=status_complete.id).count()

        completed_incidents = incidents_terminated + incidents_complete
        total_incidents         = Incident.objects.filter(project_id=self.id).count()
    
        incident_completion_percet = 0
        if total_incidents > 0 and completed_incidents > 0:
            incident_completion_percet = round(((completed_incidents / total_incidents) * 100),2)
        return incident_completion_percet
    
    @property
    def milestone_count(self):
        status_complete = Status.objects.get(name="Completed")
        status_terminate = Status.objects.get(name="Terminated")

        milestones_terminate = Milestone.objects.filter(project_id=self.id, status=status_terminate.id).count()
        milestones_complete = Milestone.objects.filter(project_id=self.id, status=status_complete.id).count()

        milestone = milestones_complete + milestones_terminate
        
        milestone_total = Milestone.objects.filter(project_id=self.id).count()
        milestone_str = str(milestone) + '/' +str(milestone_total)
        return milestone_str
    
    @property
    def task_count(self):
        status_complete = Status.objects.get(name="Completed")
        status_terminate = Status.objects.get(name="Terminated")

        tasks_terminate = Task.objects.filter(project_id=self.id, status=status_terminate.id).count()
        tasks_completed = Task.objects.filter(project_id=self.id, status=status_complete.id).count()

        task = tasks_terminate + tasks_complete

        task_total  = Task.objects.filter(project_id=self.id).count()
        task_str = str(task) + '/' +str(task_total)
        return task_str
    
    @property
    def incident_count(self):
        status_complete = Status.objects.get(name="Completed")
        status_terminate = Status.objects.get(name="Terminated")

        incidents_terminate = Incident.objects.filter(project_id=self.id, status=status_terminate.id).count()
        incidents_complete = Incident.objects.filter(project_id=self.id, status=status_complete.id).count()

        incident = incidents_terminate + incidents_complete
        incident_total  = Incident.objects.filter(project_id=self.id).count()
        incident_str = str(incident) + '/' +str(incident_total)
        return incident_str
    
    @property
    def time_now(self):
        time = datetime.now()
        return time

    class Meta:
        db_table = 'project'


class ProjectTeam(models.Model):
    name = models.CharField(max_length=100)
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProjectTeamMember(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE, default='')
    project_team = models.ManyToManyField(ProjectTeam)
    responsibility = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL )
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.member)


class ProjectDocument(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    document_description = models.CharField(max_length=255, null=True, blank=True)
    document = models.FileField(upload_to='documents/projects/')
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now=True)
    modified_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# ProjectAttachments
class ProjectAttachments(models.Model):
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=45)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta():
        db_table = 'project_attachment'


class Milestone(models.Model):
    name = models.CharField(max_length=100)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, blank=True, null=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    startdate = models.DateField(null=True, blank=True)
    enddate = models.DateField(null=True, blank=True)
    actual_startdate = models.DateField(null=True, blank=True)
    actual_enddate = models.DateField(null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=True, null=True)
    created_time = models.DateTimeField(auto_now_add=True)
    creator  = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='milestone_creator')
    modified_time = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    @property
    def completion(self):
        status_complete = Status.objects.get(name="Completed")
        status_terminate = Status.objects.get(name="Terminated")

        task_terminate = Task.objects.filter(milestone_id=self.id, status=status_terminate.id).count()
        task_complete = Task.objects.filter(milestone_id=self.id, status=status_complete.id).count()

        completed_tasks = task_terminate + task_complete
        total_tasks         = Task.objects.filter(milestone_id=self.id).count()
        completion_level    = 0
        if total_tasks > 0:
            if completed_tasks > 0:
                completion_level  = round(((completed_tasks / total_tasks) * 100),2)
        return completion_level

    @property
    def time_now(self):
        time = datetime.now()
        return time

    class Meta:
        ordering = ['enddate']


# MilestoneAttachment
class MilestoneAttachment(models.Model):
    milestone = models.ForeignKey(Milestone, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta():
        db_table = 'milestone_attachment'


class Task(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    milestone = models.ForeignKey(Milestone, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='task_creator')
    assigned_to = models.ManyToManyField(ProjectTeamMember, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    class Meta():
        db_table = 'task'


# TaskAttachment
class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)
    attachment_name = models.CharField(max_length=200, blank=True, null=True)
    document = models.FileField(upload_to='documents/tasks/', blank=True, null=True)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta():
        db_table = 'task_attachment'


# Incident
class Incident(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, null=True, blank=True)
    priority = models.ForeignKey(Priority, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.ManyToManyField(Status, blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=True, null=True)
    assigner = models.ManyToManyField(ProjectTeamMember, blank=True, null=True, related_name="assigner")
    assigned_to = models.ManyToManyField(ProjectTeamMember, blank=True, null=True, related_name="assigned_to")
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='incident_creator')
    image = models.ImageField(upload_to='images/incidents/', null=True, blank=True)
    document = models.FileField(upload_to='documents/incidents/', null=True, blank=True)    
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    escalation_status = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

    class Meta():
        db_table = 'incident'


# IncidentAttachment
class IncidentAttachment(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.SET_NULL, null=True, blank=True)
    attachment_name = models.CharField(max_length=45)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta():
        db_table = 'incident_attachment'


# IncidentComment
class IncidentComment(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.DO_NOTHING)
    comment = models.TextField()
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)
    attachment = models.FileField(upload_to="attachments/incidents", null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta():
        db_table = 'incident_comment'


# IncidentCommentAttachments
class IncidentCommentAttachments(models.Model):
    comment = models.ForeignKey(IncidentComment, on_delete=models.DO_NOTHING)
    attachment_name = models.CharField(max_length=45)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta():
        db_table = 'incident_comment_attachment'


# IncidentCommentReply
class IncidentCommentReply(models.Model):
    comment = models.ForeignKey(IncidentComment, on_delete=models.DO_NOTHING)
    reply = models.CharField(max_length=200)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta():
        db_table = 'incident_comment_reply'


# IncidentCommentReplyAttachment
class IncidentCommentReplyAttachment(models.Model):
    comment_reply = models.ForeignKey(IncidentCommentReply, on_delete=models.DO_NOTHING)
    attachment_name = models.CharField(max_length=45)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta():
        db_table = 'incident_comment_reply_attachment'


# ProjectForum
class ProjectForum(models.Model):
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)
    forum_name = models.CharField(max_length=255, default=1)
    chat_room_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta():
        db_table = 'project_forum'


# ProjectForumMessages
class ProjectForumMessages(models.Model):
    projectforum = models.ForeignKey(ProjectForum, on_delete=models.DO_NOTHING)
    team_member = models.ForeignKey(ProjectTeamMember, on_delete=models.DO_NOTHING)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)
    chat_message = RichTextField()

    class Meta():
        db_table = 'project_forum_messages'


# ProjectForumMessageAttachments
class ProjectForumMessageAttachments(models.Model):
    projectforummessage = models.ForeignKey(ProjectForumMessages, on_delete=models.DO_NOTHING)
    attachment_name = models.CharField(max_length=45)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta():
        db_table = 'project_forum_message_attachments'


# ProjectForumMessageReplies
class ProjectForumMessageReplies(models.Model):
    projectforummessage = models.ForeignKey(ProjectForumMessages, on_delete=models.DO_NOTHING)
    team_member = models.ForeignKey(ProjectTeamMember, on_delete=models.DO_NOTHING)
    reply = RichTextField()
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta():
        db_table = 'project_forum_message_replies'


# ProjectForumMessageReplyAttachments
class ProjectForumMessageReplyAttachments(models.Model):
    projectforummessagereply = models.ForeignKey(ProjectForumMessageReplies, on_delete=models.DO_NOTHING)
    attachment_name = models.CharField(max_length=45)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta():
        db_table = 'project_forum_message_reply_attachments'


# Project SLA(Service Level Agreement)
class ServiceLevelAgreement(models.Model):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, null=True, blank=True) 
    response_time = models.IntegerField()
    resolution_time = models.IntegerField()
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)
    TIME_CHOICES = (('1', 'Days'), ('2', 'Weeks'), ('3', 'Months'))
    resolution_duration = models.CharField(max_length=255, choices=TIME_CHOICES, default='Days')
    response_duration = models.CharField(max_length=255, choices=TIME_CHOICES, default='Days')


# Escalation Levels
class EscalationLevel(models.Model):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    description = RichTextField(blank=True, null=True)
    escalated_to = models.ManyToManyField(User)
    escalated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='escalated_by')
    date_escalated = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)
    escalation_on = models.IntegerField(default=1)
    TIME_CHOICES = (('1', 'Days'), ('2', 'Weeks'), ('3', 'Months'))
    escalation_on_duration = models.CharField(max_length=255, choices=TIME_CHOICES, default='Days')


class Timesheet(models.Model):
    log_day = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    notes = RichTextField(blank=True, null=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_by')
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approved_by', blank=True, null=True)
    date_approved = models.DateTimeField(blank=True, null=True)
    created_time = models.DateTimeField(auto_now_add=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    project_team_member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_team_member', null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    is_submitted = models.BooleanField(default=False)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_by', blank=True, null=True)
    date_submitted = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=255, default='INITIAL')
    last_updated_date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='last_updated_by', blank=True, null=True)
    is_resubmitted = models.BooleanField(default=False)
    approver_notes = RichTextField(blank=True, null=True)

    def duration(self):
        start = self.start_time
        end = self.end_time
        start_sec= (start.hour*60+start.minute)*60+start.second
        end_sec= (end.hour*60+end.minute)*60+end.second
        delta = end_sec-start_sec
        if delta >= 3600:
            convert_srt = 'hr(s)'
        elif delta <= 3599 and delta >= 60 :
            convert_srt = 'min(s)'
        else:
            convert_srt = 'sec(s)'
        return '{} {}'.format(str(timedelta(seconds=delta)), convert_srt)

    def get_resubmission_count(self):
        return ResubmittedTimesheet.objects.filter(timesheet=self.id).count()

    def durationsec(self):
        start = self.start_time
        end = self.end_time
        start_sec= (start.hour*60+start.minute)*60+start.second
        end_sec= (end.hour*60+end.minute)*60+end.second
        delta = end_sec-start_sec
        
        return delta

    
class ResubmittedTimesheet(models.Model):
    date_resubmitted = models.DateTimeField(auto_now=True)
    comment = RichTextField(blank=True, null=True)
    resubmitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resubmitted_by')
    timesheet = models.ForeignKey(Timesheet, on_delete=models.CASCADE)
    

# class SchedulePlan(models.Model):
#     title = models.CharField(max_length=255)
#     start_date = models.DateTimeField()
#     end_date = models.DateTimeField()
#     notes = RichTextField(blank=True, null=True)
#     added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_by')
#     created_time = models.DateTimeField(auto_now_add=True)
#     task = models.ForeignKey(Task, on_delete=models.CASCADE)
#     project_team_member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_team_member', null=True)
#     company = models.ForeignKey(Company, on_delete=models.CASCADE)
#     status = models.CharField(max_length=255, default='INITIAL')
#     last_updated_date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
#     last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='last_updated_by', blank=True, null=True)


class DailyLoggedHours(models.Model):
    """class to view exact hours to be logged daily"""
    logged_hours = models.TimeField()
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="updated_by")

    class Meta():
        db_table = 'daily_logged_hours'


class ProjectCode(models.Model):
    """input to standardize project code for projects"""
    project_code = models.CharField(max_length=255)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta():
        db_table = 'project_code'
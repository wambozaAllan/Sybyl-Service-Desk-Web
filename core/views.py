from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.template import Context
from django.template.loader import get_template
from django.core.mail import EmailMessage
from django.conf import settings
from django.views.generic import View
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from .models import UsrGrpPermissions
from .forms import LoginForm
from user_management.forms import CustomUserCreationForm
from project_management.models import Project, Milestone, Incident, Company, Task
from static.fusioncharts import FusionCharts

class SignUp(generic.CreateView):
    form_class = CustomUserCreationForm
    template_name = 'signup.html'

    def form_valid(self, form):
        firstname = form.cleaned_data['first_name']
        username = form.cleaned_data['username']
        receiver_mail = form.cleaned_data['email']
        user = form.save()
        user.refresh_from_db()
        user.is_active = False
        user.save()

        cxt = {
            'firstname' : firstname,
            'username'  : username
        }

        subject = 'You are Welcome'
        message  = get_template('mails/signup_email.html').render(cxt)
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [receiver_mail]
        mail_to_send    = EmailMessage(subject, message, to=recipient_list, from_email=email_from)
        mail_to_send.content_subtype = 'html'
        mail_to_send.send()
        return HttpResponseRedirect('/login')
    success_url = reverse_lazy('login')

class Login(auth_views.LoginView):
    template_name = 'core/login.html'

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm()
        username = request.POST['username']
        password = request.POST['password']

        # Authenticate user
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                # Create user session
                login(request, user)
                return redirect("/home/")
        return render(request, self.template_name, {'form': form})

@login_required()
def logout_view(request):
    logout(request)
    return redirect("/login/")

#@login_required()
def home(request):
    permission_list = list(request.user.get_all_permissions())
    #permission_list2 =
    print(permission_list[0])
    request.session['usrgrpid'] = request.user.usergroup_id
    usrgrpid = request.user.usergroup_id
    print(request.user.usergroup_id)

    total_projects      = Project.objects.all().count()
    total_clients       = Company.objects.filter(category_id=2).count()
    total_vendors       = Company.objects.filter(category_id=3).count()
    total_incidents     = Incident.objects.all().count()
    total_tasks         = Task.objects.all().count()
    total_milestones    = Milestone.objects.all().count()

    datasource  =  {}

    datasource['chart'] = {
        "caption":"Projects Overview",
        "subCaption":"showing all projects",
        "numberSuffix":"%",
        "valueBgColor": "#FFFFFF",
        "valueFontColor": "#000000",
        "rotateValues": "0",
        "placeValuesInside": "0",
        "valueBgColor": "#FFFFFF",
        "valueBgAlpha": "50",
        "xAxisName": "Project",
        "yAxisName": "Completion (%)",
        "theme":"fint",
        "showBorder": "0",
        "formatnumberscale": "1"
    }
    datasource['data'] = []

    for key in Project.objects.all():
        data = {}
        data['label']   = key.name
        data['value']   = key.completion
        datasource['data'].append(data)

    colchart = FusionCharts("column2d", "ex1", "1045", "350", "projects-chart", "json", datasource)

    return render(request, 'core/home.html', {'all_permissions':permission_list,'total_projects':total_projects,
                                            'total_clients':total_clients, 'total_vendors':total_vendors,
                                            'total_incidents':total_incidents,
                                            'total_tasks':total_tasks,
                                            'total_milestones':total_milestones,
                                            'output' : colchart.render()})

def load_user_group_menus(request):
    usrgrpid = request.GET.get('project')
    #usrgrpid = request.session.usrgrpid
    print(usrgrpid)
    grp_privileges = UsrGrpPermissions.objects.filter(usergroup_id=usrgrpid).values("privilege_id")
    #privileges = Privilege.objects.filter(id__in=grp_privileges).values("submenu_id")

    #privileges = Privilege.objects.values("submenu_id")
    return render(request, 'core/user_group_dropdown_list_options.html', {})

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt

from .forms import LoginForm
from user_management.forms import CustomUserCreationForm
from project_management.models import Project, Milestone, Incident, Company, Task, User
from static.fusioncharts import FusionCharts
from django.contrib.auth.hashers import make_password
import datetime

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
            'firstname': firstname,
            'username': username
        }

        subject = 'You are Welcome'
        message = get_template('mails/signup_email.html').render(cxt)
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [receiver_mail]
        mail_to_send = EmailMessage(subject, message, to=recipient_list, from_email=email_from)
        mail_to_send.content_subtype = 'html'
        mail_to_send.send()
        return HttpResponseRedirect('/login')

    success_url = reverse_lazy('login')


class Login(LoginView):
    template_name = 'core/login.html'

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        user_login_state = False
        form = LoginForm()
        username = request.POST['username']
        password = request.POST['password']

        user_in_db = User.objects.filter(username=username).exists()

        if user_in_db == True:
            user_exists = User.objects.get(username=username)
            if user_exists is not None:
                if user_exists.last_login is not None:
                    user_login_state = True
                else:
                    user_login_state = False
            # Authenticate user
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    # Create user session
                    login(request, user)

                    if user.user_type == "clientuser":
                        request.session['pk'] = user.pk
                        request.session['username'] = username
                        request.session['first_name'] = user.first_name
                        request.session['last_name'] = user.last_name
                        request.session['company'] = user.company.name
                        request.session['company_id'] = user.company.id
                        if user_login_state:
                            return redirect("/projectManagement/customerRequests/")
                        else:
                            User.objects.filter(id=user.pk).update(last_login=None)
                            return render(request, 'core/change_password.html', {'user_name': username, 'user_id': user.pk})

                    else:
                        # Other sessions
                        request.session['pk'] = user.pk
                        request.session['username'] = username
                        request.session['first_name'] = user.first_name
                        request.session['last_name'] = user.last_name
                        request.session['company'] = user.company.name
                        request.session['company_id'] = user.company.id
                        request.session['branch'] = user.branch.name
                        request.session['department'] = user.department.name
                        request.session['department_id'] = user.department.id
                        if user_login_state:
                            return redirect("/home/")
                        else:
                            User.objects.filter(id=user.pk).update(last_login=None)
                            return render(request, 'core/change_password.html', {'user_name': username, 'user_id': user.pk})
                return render(request, self.template_name, {'form': form})
            else:
                return render(request, self.template_name, {'form': form}) 
        else:
            return render(request, self.template_name, {'form': form}) 

@login_required()
def logout_view(request):
    logout(request)
    return redirect("/login/")


# @login_required()
def home(request):
    permission_list = list(request.user.get_all_permissions())

    total_projects = []
    # returning projects under department
    current_dept_projects = Project.objects.filter(department=request.session['department_id'])
    
    for v in current_dept_projects:
        project = Project.objects.filter(id=v.id, is_active=True)
        total_projects.append(project)
    
    total_projects = len(total_projects)
    total_clients = Company.objects.filter(category_id=2).count()
    total_vendors = Company.objects.filter(category_id=3).count()
    total_incidents = Incident.objects.all().count()
    total_tasks = Task.objects.all().count()
    total_milestones = Milestone.objects.all().count()

    datasource = {}

    datasource['chart'] = {
        "caption": "Projects Overview",
        "subCaption": "showing all projects",
        "numberSuffix": "%",
        "valueBgColor": "#FFFFFF",
        "valueFontColor": "#000000",
        "rotateValues": "0",
        "placeValuesInside": "0",
        "valueBgColor": "#FFFFFF",
        "valueBgAlpha": "50",
        "xAxisName": "Project",
        "yAxisName": "Completion (%)",
        "theme": "fint",
        "showBorder": "0",
        "formatnumberscale": "1"
    }
    datasource['data'] = []

    dept_projects = []
    # returning projects under department
    current_dept = Project.objects.filter(department=request.session['department_id'])
    
    for v in current_dept:
        project = Project.objects.filter(id=v.id, is_active=True)
        dept_projects.append(project)

    for dept in dept_projects:
        for key in dept:
            data = {}
            data['label'] = key.name
            data['value'] = key.completion
            datasource['data'].append(data)

    colchart = FusionCharts("column2d", "ex1", "1045", "350", "projects-chart", "json", datasource)

    return render(request, 'core/home.html', {'all_permissions': permission_list, 'total_projects': total_projects,
                                            'total_clients': total_clients, 'total_vendors': total_vendors,
                                            'total_incidents': total_incidents,
                                            'total_tasks': total_tasks,
                                            'total_milestones': total_milestones,
                                            'output': colchart.render()})


def save_new_password(request):
    template_name = 'core/login.html'
    new_password = request.GET.get('new_password')
    user_name = request.GET.get('user_name')
    user_id = request.GET.get('user_id')
    now = datetime.datetime.utcnow()
    User.objects.filter(id=int(user_id)).update(username=user_name, password=make_password(new_password), last_login=now.strftime('%Y-%m-%d %H:%M:%S'))
    return redirect("/login/")


def customer_home(request):
    return render(request, 'core/customer_home_page.html',context=None )
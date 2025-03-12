
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *
from .forms import *
from django.http import JsonResponse
from django.contrib.auth import login,authenticate,logout
from django.db.models import Q
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils.timezone import now
from django.db.models import Min, Max
import csv, json
from django.http import HttpResponse, JsonResponse
from django.utils.timezone import localtime
from django.db.models.functions import TruncDate
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseRedirect

# User Authentication

# Home Page
def home(request):
    return render(request, 'website/index.html')
#Account
def account(request):
    return render(request, 'website/account.html')

# Project Description
@login_required
def proj_des(request, project_id=None):
    project = get_object_or_404(Project, id=project_id)
    updates = ProjectUpdate.objects.filter(project=project).order_by("-timestamp")
    for update in updates:
        update.is_late = update.timestamp.date() > project.end_date  

    comments = ProjectComment.objects.filter(update__project=project).order_by("timestamp")

    if request.method == "POST":
        if "add_update" in request.POST:
            # Employee adding a PR update
            description = request.POST.get("description").strip()
            status = request.POST.get("status").strip()

            if description:
                ProjectUpdate.objects.create(
                    project=project,
                    updated_by=request.user,
                    description=description,
                    status=status
                )
                messages.success(request, "Update added successfully.")
            else:
                messages.error(request, "Update description cannot be empty.")

        elif "approved" in request.POST or "disapproved" in request.POST:
            # Manager approving/disapproving PR
            update_id = request.POST.get("update_id")
            comment_text = request.POST.get("comment").strip()
            is_approved = "approved" in request.POST  # True if approved, False if disapproved

            if comment_text:
                update = get_object_or_404(ProjectUpdate, id=update_id)
                ProjectComment.objects.create(
                    update=update,
                    commented_by=request.user,
                    comment=comment_text,
                    approved=is_approved
                )
                if is_approved:
                    messages.success(request, "PR Approved ✅")
                else:
                    messages.success(request, "PR Disapproved ❌")
            else:
                messages.error(request, "Comment cannot be empty.")

        return redirect("proj_des", project_id=project.id)

    return render(request, "website/project_description.html", {
        "project": project,
        "updates": updates,
        "comments": comments,
    })


# User Registration
def register(request):
    if request.method == "POST":
        print("abc")
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            print("def")
            form.save()
            messages.success(request, "Registration successful! You can now log in.")
            return redirect("login")
        else:
            messages.error(request, "There was an error with your registration. Please check the form.")
            print(form.errors) 
    else:
        form = UserRegistrationForm()

    return render(request, "website/register.html", {"form": form})

# User Login
def login_page(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            request.session.set_expiry(86400)  # 1 day session
            return redirect("dashboard")  # Change to your homepage
    return render(request, "website/login.html")

# User Logout
@login_required
def user_logout(request):
    if request.user.is_authenticated:
        attendance_record = Attendance.objects.filter(user=request.user, logout_time__isnull=True).last()

        if attendance_record:
            attendance_record.logout_time = now()  
            attendance_record.save()
        
        logout(request)  

    messages.success(request, "You have been logged out.")
    return redirect('home')

# Dashboard
def dashboard(request):
    return render(request, 'website/dashboard.html')

# Add a Project (Only Managers)
@login_required
def add_project(request):
    managers = User.objects.filter(role="Manager")
    employees = User.objects.filter(role="Employee")

    if request.user.role != "Manager":
        messages.error(request, "You are not authorized to add a project")
        return redirect('project_list')

    if request.method == "POST":
        data = request.POST
        project_name = data.get('project_name', '').strip()
        proj_des = data.get('proj_des', '').strip()
        start_date = data.get('start_date', '').strip()
        end_date = data.get('end_date', '').strip()
        status = data.get('status', '').strip()
        members_list = request.POST.getlist("members_list[]")

        project = Project.objects.create(
            project_name=project_name,
            proj_des=proj_des,
            start_date=start_date,
            end_date=end_date,
            status=status,
            manager=request.user,
        )

        project.members.set(members_list)
        project.save()

        messages.success(request, "Project added successfully!")
        return redirect('/projects/')

    context = {
        'managers': managers,
        'employees': employees
    }
    
    return render(request, 'website/add_project.html', context)

#update project
@login_required
def update_project(request, id=None):
    managers = User.objects.filter(role="Manager")
    employees = User.objects.filter(role="Employee")

    if request.user.role != "Manager":
        messages.error(request, "You are not authorized to update a project")
        return redirect('project_list')

    queryset = get_object_or_404(Project, pk=id)

    if request.method == 'POST':
        data = request.POST
        project_name = data.get('project_name', '').strip()
        proj_des = data.get('proj_des', '').strip()
        start_date = data.get('start_date', '').strip()
        end_date = data.get('end_date', '').strip()
        status = data.get('status', '').strip()
        members_list = request.POST.getlist("members_list[]")

        queryset.project_name = project_name
        queryset.proj_des = proj_des
        queryset.start_date = start_date
        queryset.end_date = end_date
        queryset.status = status
        queryset.members.set(members_list)

        queryset.save()
        return redirect('/projects/')

    context = {
        'project': queryset,
        'managers': managers,
        'employees': employees
    }
    employees = User.objects.all()
    return render(request, 'website/update_project.html', context)

# List All Projects
@login_required
def project_list(request):
    if request.user.role == "Employee":
        projects = Project.objects.filter(members=request.user)
    elif request.user.role == "Manager":
        projects = Project.objects.filter(manager=request.user)
    else:
        projects = Project.objects.all()
    employees = User.objects.filter(role="Employee")
    managers = User.objects.filter(role="Manager")
    context = {
        'projects': projects,
        'managers': managers,
        'employees': employees
    }
    return render(request, 'website/project_list.html', context)

#Delete Project 
@login_required
def delete_project(request, id):
    project = get_object_or_404(Project, pk=id)
    
    if request.method == 'POST':
        project.delete()
        messages.success(request, "Project deleted successfully!")  # Flash message
        return redirect('/projects/')  # Redirect to project list

    return render(request, 'website/project_list.html')

#update status of project
@login_required
def change_status(request, project_id):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "User not authenticated"}, status=401)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

    project = get_object_or_404(Project, id=project_id)

    if request.user.role != "Manager":
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    try:
        data = json.loads(request.body)  # Parse JSON request
        new_status = data.get("status")

        if new_status not in ["In Progress", "Completed"]:
            return JsonResponse({"success": False, "error": "Invalid status"}, status=400)

        project.status = new_status
        project.save()

        return JsonResponse({"success": True, "new_status": project.status})
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON data"}, status=400)
    
# Calendar View
@login_required
def project_calendar(request):
    return render(request, "website/calendar.html")

@login_required
def project_events(request):
    events = []
    if request.user.role == "Employee":
        projects = Project.objects.filter(members=request.user)
    elif request.user.role == "Manager":
        projects = Project.objects.filter(manager=request.user)
    else:
        projects = Project.objects.all()
        
    for project in projects:
        events.append({
            "title": project.project_name,  
            "start": project.start_date.strftime('%Y-%m-%d'),  
            "end": project.end_date.strftime('%Y-%m-%d'),  
            "status": project.status,  
            "color": "#F59E0B" if project.status == "In Progress" else "#10B981",
            "description": project.proj_des
        })
    
    return JsonResponse(events, safe=False)

# Update Account
@login_required
def update_account(request):
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Account updated successfully!")
            return redirect("/account/")
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, "website/account_settings.html", {"form": form})

@login_required
def update_user_role(request):
    if request.user.role != "HR":
        messages.error(request, "You are not authorized to update a user role")
        return redirect('dashboard')

    if request.method == 'POST':
        print("Received POST request:", request.POST)  # Debugging

        user_id = request.POST.get('user_id')
        new_role = request.POST.get('role')

        if not user_id or not new_role:
            messages.error(request, "Invalid request")
            return redirect('update_user_role')

        user = get_object_or_404(User, id=user_id)
        user.role = new_role
        print("Updating user ID:", user_id) 
        print("New Role:", new_role)
  
        user.save()

        messages.success(request, f"Updated role for {user.first_name} {user.last_name} to {new_role}.")
        return redirect('update_user_role')

    users = User.objects.exclude(Q(role="HR") | Q(role="Admin"))

    return render(request, 'website/update_user_role.html', {'users': users})

# Attendance Management
@receiver(user_logged_in)
def log_login(sender,request,user, **kwargs):
    Attendance.objects.create(user=user, login_time=now())

@receiver(user_logged_out)
def log_logout(sender,request,user, **kwargs):
    attendance = Attendance.objects.filter(user=user,logout_time__isnull=True).first()
    if attendance:
        attendance.logout_time=now() 
        attendance.save()

@login_required
def get_user_attendance(request):
    if request.user.role == "HR":
        attendance_records=Attendance.objects.all()
    else:
        attendance_records=Attendance.objects.filter(user=request.user)
    return render(request, 'website/attendance.html', {'attendance_records': attendance_records})

# Export Users
@login_required
def user_list(request):
    if request.user.role!= "HR":
        return HttpResponse("You are not authorized to view this page")
    response= HttpResponse(content_type='text/csv')
    response['Content-Disposition']='attachment; filename="users.csv"'

    writer=csv.writer(response)
    writer.writerow(['First Name','Last Name','Email','Role'])
    users=User.objects.all().values_list('first_name','last_name','email','role')
    for user in users:
        writer.writerow(user)
    return response

# Attendance Summary
@login_required
def get_attendance_summary(request):
    attendance_data = (
        Attendance.objects.annotate(day=TruncDate("login_time"))
        .values("user__id", "user__first_name", "user__last_name", "day")
        .annotate(
            first_login=Min("login_time"),
            last_logout=Max("logout_time")
        )
        .order_by("user__id", "day")
    )

    attendance_summary = []
    standard_work_hours = 8  

    for record in attendance_data:
        if record["last_logout"]:
            total_seconds = (record["last_logout"] - record["first_login"]).total_seconds()
            total_hours = total_seconds / 3600
        else:
            total_hours = None  

        balance_hours = (total_hours - standard_work_hours) if total_hours else None

        attendance_summary.append({
            "user": f"{record['user__first_name']} {record['user__last_name']}",
            "date": record["day"],
            "first_login": localtime(record["first_login"]) if record["first_login"] else None,
            "last_logout": localtime(record["last_logout"]) if record["last_logout"] else None,
            "total_hours": round(total_hours, 2) if total_hours else "Session Active",
            "status": (
                f"Ahead by {round(balance_hours, 2)} hrs" if balance_hours and balance_hours > 0 else
                f"Behind by {abs(round(balance_hours, 2))} hrs" if balance_hours and balance_hours < 0 else
                "Ongoing Session"
            )
        })

    return render(request, "website/attendance_summary.html", {"attendance_summary": attendance_summary})


# Send Email
@login_required
def send_django_mail(request):
    context = {}

    if request.method == 'POST':
        address = request.POST.get('address')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if address and subject and message:
            try:
                send_mail(subject, message, settings.EMAIL_HOST_USER, [address])
                context['result'] = 'Email sent successfully'
                print("Email sent successfully")
                return redirect('send_email_success')
            except Exception as e:
                context['result'] = f'Error sending email: {e}'
                print(f'Error sending email: {e}')
        else:
            context['result'] = 'All fields are required'
            print('All fields are required')
    
    return render(request, "website/mail.html", context)

@login_required
def send_email_success(request):
    return render(request, "website/mail_success.html", {"message": "Email sent successfully!"})

#Resignation

# def send_notification_email(user,message):
#     send_mail(
#         "Resignation Request",
#         message,
#         settings.EMAIL_HOST_USER,
#         [user.email],
#         fail_silently=False,
#     )

@login_required
def resign(request):
    if request.method == 'POST':
        reason = request.POST.get('reason')
        resignation=ResignRequest.objects.create(user=request.user,reason=reason)
        resignation.save()
        return redirect('resignation_status')
    return render(request, 'website/resignation.html', {'user': request.user})

@login_required
def manager_resign(request,id):
    resignations =get_object_or_404(ResignRequest,pk=id)  
    if request.user.role == 'Manager':
        resignations.manager_approved=True
        resignations.save()

        return redirect('manager_dashboard')
    return render(request, 'website/manager_review.html', {'resignations': resignations})

@login_required
def hr_resign(request, id):
    resignations = get_object_or_404(ResignRequest, pk=id)
    
    if request.user.role == 'HR' and resignations.manager_approved:
        resignations.hr_approved = True
        resignations.status = 'Approved'
        resignations.save()
        return redirect('hr_dashboard')
    return render(request, 'website/hr_review.html', {'resignations': resignations})

@login_required
def resignation_status(request):
    if request.user.role == "Employee":
        resignations = ResignRequest.objects.filter(user=request.user)
    elif request.user.role == "Manager":
        resignations = ResignRequest.objects.filter(user__manager=request.user) | ResignRequest.objects.filter(user=request.user)
    else:
        resignations = ResignRequest.objects.all()
    
    context = {
        'resignations': resignations.distinct()
    }

    return render(request, 'website/resignation_status.html', {'resignations': resignations})

@login_required
def delete_resign(request):
    if request.method == 'POST':
        resignation_id = request.POST.get('resignation_id')
        resignation = get_object_or_404(ResignRequest, pk=resignation_id)
        resignation.delete()
        return redirect('resignation_status')
    return render(request, 'website/resignation_status.html')

@login_required
def resignation_feedback(request, resignation_id):
    resignation = get_object_or_404(ResignRequest, id=resignation_id)

    if request.method == 'POST':
        form = ResignationFeedbackForm(request.POST, instance=resignation)
        if form.is_valid():
            form.save()
            messages.success(request, "Your feedback has been submitted successfully.")
            return redirect('resignation_status')  # Redirect to resignation status page
    else:
        form = ResignationFeedbackForm(instance=resignation)

    return render(request, 'website/resignation_feedback.html', {'form': form, 'resignation': resignation})


def process_resignation(request, resignation_id):
    resignation = ResignRequest.objects.get(id=resignation_id)            

    if request.method == 'POST':
        form = ResignationFeedbackForm(request.POST, instance=resignation)
        if form.is_valid():
            form.save()
            messages.success(request, "Your feedback has been submitted successfully.")
            return redirect('resignation_status')  # Redirect to resignation status page
        else:
            form = ResignationFeedbackForm(instance=resignation)
        # Process manager approval
        if request.user.role == "Manager" or request.user.is_superuser:
            form=ManagerFeedback(request.POST, instance=resignation)
            if form.is_valid():
                form.save()
                messages.success(request, "Your feedback has been submitted successfully.")
                return redirect('resignation_status')

        
        # Process HR approval
        if request.user.role == "HR" or request.user.is_superuser:
            form=HRFeedback(request.POST, instance=resignation)
            if form.is_valid():
                form.save()
                messages.success(request, "Your feedback has been submitted successfully.")
                return redirect('resignation_status')
        
        # Update overall status
        if resignation.manager_approved and resignation.hr_approved:
            resignation.status = 'Approved'
        elif resignation.manager_approved == False or resignation.hr_approved == False:
            resignation.status = 'Rejected'
        
        resignation.save()
        messages.success(request, "Resignation request processed successfully.")
        return redirect('resignation')  # or wherever you want to redirect
    
    return redirect('resignation_approval', resignation_id=resignation_id)
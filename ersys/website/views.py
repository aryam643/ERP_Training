from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from .models import Reimbursement  # adjust the import if model is elsewhere
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *
from .forms import *
from django.http import JsonResponse
from django.contrib.auth import login,authenticate,logout,get_backends
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
import requests
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import random,redis
from django.core.cache import cache

redis_client = redis.Redis(host='localhost', port=6379, db=0)



def request_otp_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        request.session["email"] = email

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, "website/request_otp.html", {"error": "No user found with that email."})

        otp = str(random.randint(100000, 999999))
        redis_client.setex(f"otp:{email}", 300, otp)  # OTP expires in 5 minutes

        send_mail(
            subject="Your ERP Login OTP",
            message=f"Your OTP for login is: {otp}",
            from_email="no-reply@erp.com",
            recipient_list=[email],
            fail_silently=False,
        )

        return redirect("verify_otp")

    return render(request, "website/request_otp.html")

def verify_otp_view(request):
    if request.method == "POST":
        otp = request.POST.get("otp")
        email = request.session.get("email")

        if not email:
            return redirect("request_otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, "website/verify_otp.html", {"error": "User not found."})

        stored_otp = redis_client.get(f"otp:{email}")
        if stored_otp and stored_otp.decode() == otp:
            backend = get_backends()[0]
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"

            login(request, user)
            return redirect("dashboard")  # Make sure you have a named URL called `dashboard`
        else:
            return render(request, "website/verify_otp.html", {"error": "Invalid OTP"})

    return render(request, "website/verify_otp.html")

@login_required
def hr_review_reimbursements(request):
    reimbursements = Reimbursement.objects.all()
    return render(request, "website/hr_review_re.html", {"reimbursements": reimbursements})

@login_required
def approve_reimbursement(request, reimbursement_id):
    reimbursement = get_object_or_404(Reimbursement, id=reimbursement_id)
    reimbursement.status = "Approved"
    reimbursement.approved_by_hr = request.user
    reimbursement.reviewed_at = now()
    reimbursement.save()
    
    # Notify employee via email
    send_mail(
        "Reimbursement Approved",
        f"Your reimbursement request for {reimbursement.amount} has been approved.",
        "aryamsharma59@gmail.com",
        [reimbursement.user.email],
        fail_silently=True,
    )

    return redirect("hr_review_reimbursements")

@login_required
def reject_reimbursement(request, reimbursement_id):
    reimbursement = get_object_or_404(Reimbursement, id=reimbursement_id)
    reimbursement.status = "Rejected"
    reimbursement.approved_by_hr = request.user
    reimbursement.reviewed_at = now()
    reimbursement.save()

    # Notify employee via email
    send_mail(
        "Reimbursement Rejected",
        f"Your reimbursement request for {reimbursement.amount} has been rejected.",
        "aryamsharma59@gmail.com",
        [reimbursement.user.email],
        fail_silently=True,
    )

    return redirect("hr_review_reimbursements")

@login_required
def reimbursement(request):
    employees = User.objects.all()

    if request.method == "POST":
        print("entering the condition")
        employee = request.user
        members_list = request.POST.getlist("members_list[]")
        date = request.POST.get("date")
        amount = request.POST.get("amount")
        description = request.POST.get("description")
        bill_file = request.FILES.get("bill_file")
        print("2")

        reimbursement = Reimbursement.objects.create(
            user=employee,
            date=date,
            amount=amount,
            description=description,
            bill_file=bill_file,
            status="Pending",
        )
        print("1")

        for member_id in members_list:
            member = User.objects.get(id=member_id)
            reimbursement.members_list.add(member)

        reimbursement.save()

        # Email notification to HR
        hr_users = User.objects.filter(groups__name="HR")
        hr_emails = [hr.email for hr in hr_users if hr.email]

        if hr_emails:
            send_mail(
                "Reimbursement Request for Review",
                f"A new reimbursement request has been submitted by {employee.username}. Please review it.",
                "aryamsharma59@gmail.com",
                hr_emails,
                fail_silently=True,
            )
        print("Email sent to HR")

        messages.success(request, "Reimbursement submitted successfully!")
        return redirect("reimbursement")
    reimbursements= Reimbursement.objects.filter(user=request.user)

    return render(request, "website/reimbursement.html", {
        "employees": employees
        , "reimbursements": reimbursements
    })

@login_required
def view_bill_file(request, reimbursement_id):
    reimbursement = get_object_or_404(Reimbursement, id=reimbursement_id)

    if not reimbursement.bill_file:
        raise Http404("Bill file not found.")

    file_path = reimbursement.bill_file.path
    file_name = os.path.basename(file_path)

    try:
        return FileResponse(open(file_path, 'rb'), content_type='application/octet-stream', filename=file_name)
    except FileNotFoundError:
        raise Http404("File does not exist.")

@login_required
def finance(request):
    salaries = Finance.objects.filter(description__startswith="Salary").order_by("-created_at")
    search_query = request.GET.get("search", "").strip()
    month_filter = request.GET.get("month", "")
    status_filter = request.GET.get("status", "")

    if search_query:
        salaries = salaries.filter(user__username__icontains=search_query)

    if month_filter:
        salaries = salaries.filter(created_at__month=timezone.datetime.strptime(month_filter, "%B %Y").month)

    if status_filter and status_filter != "All Status":
        salaries = salaries.filter(status=status_filter)

    return render(request, "website/finance.html", {"salaries": salaries})

@login_required
def export_salaries(request):
    salaries = Finance.objects.filter(description__startswith="Salary").order_by("-created_at")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="salaries.csv"'

    writer = csv.writer(response)
    writer.writerow(["Employee", "Month", "Net Salary", "Status"])

    for salary in salaries:
        writer.writerow([salary.user.username, salary.created_at.strftime("%B %Y"), salary.amount, salary.status])

    return response

SALARY_CONFIG = {
    "Employee": {"basic_salary": 30000, "allowances": 3000, "deductions": 1000, "tax_percentage": 10.0},
    "Manager": {"basic_salary": 70000, "allowances": 5000, "deductions": 2000, "tax_percentage": 15.0},
    "HR": {"basic_salary": 40000, "allowances": 4000, "deductions": 3000, "tax_percentage": 20.0},
    "Other": {"basic_salary": 20000, "allowances": 6000, "deductions": 500, "tax_percentage": 5.0},
}

# Fetch predefined salary based on user role (for AJAX)
@login_required
def get_salary_details(request):
    user_id = request.GET.get("user_id")
    try:
        user = User.objects.get(id=user_id)
        role = getattr(user, "role", "Other")  # Default to "Other" if role doesn't exist
        return JsonResponse(SALARY_CONFIG.get(role, SALARY_CONFIG["Other"]))
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

# Salary Entry View
@login_required
def add_salary(request):
    if request.method == "POST":
        user_id = request.POST.get("user")
        status = request.POST.get("status", "Unpaid")

        try:
            user = User.objects.get(id=user_id)
            role = getattr(user, "role", "Other")
            salary_details = SALARY_CONFIG.get(role, SALARY_CONFIG["Other"])

            # Calculate net salary
            tax_amount = (salary_details["basic_salary"] * salary_details["tax_percentage"]) / 100
            net_salary = salary_details["basic_salary"] + salary_details["allowances"] - salary_details["deductions"] - tax_amount

            # Create salary entry
            Finance.objects.create(
                user=user,
                amount=net_salary,
                basic_salary=salary_details["basic_salary"],
                allowances=salary_details["allowances"],
                deductions=salary_details["deductions"],
                tax_percentage=salary_details["tax_percentage"],
                status=status,
                created_at=timezone.now()
            )

            messages.success(request, f"Salary for {user.username} added successfully!")
        except User.DoesNotExist:
            messages.error(request, "Invalid user selected.")

        return redirect('/finance/')  # Redirect to the finance page

    employees = User.objects.all()
    return render(request, 'website/add_Salary.html', {'employees': employees})


# User Authentication
@login_required
def project_timeline(request):
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
    return render(request, 'website/project_timeline.html', context)
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
def holiday_calendar(request):
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
    00
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

#Resignation
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



#room booking
def room_booking_calendar(request):
    return render(request, "website/room_booking.html")

def room_booking(request):
    return render(request, "website/my_booking.html")

def book_room(request):
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.save()
            return redirect("booking_list")
        else:
            print("Form Errors:", form.errors)  

    else:
        form = BookingForm()

    rooms = Room.objects.all() 

    return render(request, "website/room_booking.html", {"form": form, "rooms": rooms})


@login_required
def booking_list(request):
    bookings = Booking.objects.filter(user=request.user).order_by("-start_time")
    return render(request, "website/my_bookings.html", {"bookings": bookings})

def get_bookings(request):
    bookings = Booking.objects.all()
    events = []
    for booking in bookings:
        events.append({
            "title": f"Booked: {booking.room.name}",
            "start": booking.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "end": booking.end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "color": "#ff4d4d",
        })
    return JsonResponse(events, safe=False)

@csrf_exempt
def check_availability(request):
    if request.method == "POST":
        data = json.loads(request.body)
        room_id = data.get("room")
        start_time = datetime.fromisoformat(data.get("start_time"))
        end_time = datetime.fromisoformat(data.get("end_time"))

        overlapping_bookings = Booking.objects.filter(
            room_id=room_id,
            start_time__lt=end_time,  # Existing booking must end before new start
            end_time__gt=start_time,  # Existing booking must start after new end
        )

        available = not overlapping_bookings.exists()
        return JsonResponse({"available": available})

    return JsonResponse({"error": "Invalid request"}, status=400)

API_KEY = "y47W1WOKSykWSWif4ZW4AnhbEpdbd5hj"

def get_main_holidays(request):
    country = request.user.location  
    country_code_mapping = {"IN": "IN", "USA": "US", "UK": "GB", "CA": "CA", "AU": "AU"}
    country_code = country_code_mapping.get(country, "US")  

    year = 2025  
    url = f"https://calendarific.com/api/v2/holidays?api_key={API_KEY}&country={country_code}&year={year}"

    response = requests.get(url)

    if response.status_code != 200:
        return JsonResponse({"error": "Failed to fetch holidays", "details": response.json()}, status=response.status_code)

    holidays_data = response.json()

    if "response" not in holidays_data or "holidays" not in holidays_data["response"]:
        return JsonResponse({"error": "Invalid API response"}, status=500)

    holidays_list = holidays_data["response"]["holidays"]

    # Format the holidays for FullCalendar
    all_holidays = [
        {
            "title": holiday["name"],  
            "start": holiday["date"]["iso"],  
            "allDay": True  
        }
        for holiday in holidays_list
    ]


    return JsonResponse(all_holidays, safe=False)

def leave(request):
    if request.method == 'POST':
        form = LeaveApplicationForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.user = request.user
            leave.save()
            messages.success(request, "Leave request submitted successfully.")
            return redirect('leave_status')
        else:
            messages.error(request, "There was an error with your form submission.")
    
    else:
        form = LeaveApplicationForm()

    return render(request, "website/leave.html", {"form": form})

def leave_status(request):
    if request.user.role == "Employee":
        leaves = Leave.objects.filter(user=request.user)
    elif request.user.role == "Manager":
        leaves = Leave.objects.filter(user__manager=request.user) | Leave.objects.filter(user=request.user)
    else:  # Admin or higher role
        leaves = Leave.objects.all()
    
    return render(request, 'website/leave_status.html', {'leaves': leaves.distinct()})

def manager_approval(request, leave_id):
    leave = get_object_or_404(Leave, pk=leave_id)

    if request.user.role == "Manager":
        leave.manager_approved = True
        leave.status = "Approved"
        leave.save()
        messages.success(request, "Leave request approved successfully.")
    else:
        messages.error(request, "You do not have permission to approve this leave.")

    return redirect('leave_status')

def process_leave(request, leave_id):
    leave = get_object_or_404(Leave, id=leave_id)

    if request.method == "POST":
        print(1)
        manager_approved = request.POST.get("manager_approved") == "true"

        if request.user.role == "Manager" or request.user.is_superuser:
            print(3)
            leave.manager_approved = manager_approved
            leave.status = "Approved" if manager_approved else "Rejected"
            leave.save()
            messages.success(request, "Leave decision submitted successfully.")
        
        return redirect('leave_status')

    return render(request,'website/leave_approval.html', {'leave': leave})
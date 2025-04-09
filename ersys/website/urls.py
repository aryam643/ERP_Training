from django.urls import path
from . import views

urlpatterns = [
    # Home Page
    path('', views.home, name='home'),
    path('dashboard/',views.dashboard,name='dashboard'),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Project Management
    path('projects/', views.project_list, name='project_list'),
    path('project_events/', views.project_events, name='project_events'),
    path('project_timeline/', views.project_timeline, name='project_timeline'),
    path('projects/add/', views.add_project, name='add_project'),
    path('proj_des/<int:project_id>/', views.proj_des, name='proj_des'),
    path('update-project/<int:id>/', views.update_project, name='update_project'),
    path('delete_project/<int:id>/', views.delete_project, name='delete_project'),
    path('change-status/<int:project_id>/', views.change_status, name='change_status'),

    #Calendar
    path("holiday_calendar/", views.holiday_calendar, name="holiday_calendar"),
    path("holidays/", views.get_main_holidays, name="get_main_holidays"),
    # path("calendar/events/", views.calendar_events, name="calendar_events"),
    path("calendar/room_events/", views.get_bookings, name="get_bookings"),

    #Account
    path('account/', views.account, name='account'),
    path("account/update", views.update_account, name="update"),

    #User Management
    path('update_role',views.update_user_role,name='update_user_role'),
    path('attendance',views.get_user_attendance,name='attendance'),
    path('userlist',views.user_list,name='user_list'),
    path("attendance-summary/", views.get_attendance_summary, name="attendance_summary"),

    #mail
    path('send_mail',views.send_django_mail,name='send_mail'),
    path('send_email_success/', views.send_email_success, name='send_email_success'),

    #room_booking
    path("book/", views.book_room, name="book_room"),
    path("my-bookings/", views.booking_list, name="booking_list"),
    path("get-bookings/", views.get_bookings, name="get_bookings"),
    path('check-availability/', views.check_availability, name='check_availability'),


    
    #resignation
    path('resignation',views.resign,name='resignation'),
    path('resignation/manager', views.manager_resign, name='manager_review_resignation'),
    path('resignation/hr/<int:id>/', views.hr_resign, name='hr_review_resignation'),
    path('resignation/status/', views.resignation_status, name='resignation_status'),
    path('resign/delete',views.delete_resign,name='delete_resign'),
    path('resignation/status/feedback/<int:resignation_id>/', views.resignation_feedback, name='resignation_feedback'),
    path('change-status/<int:resignation_id>/', views.change_status, name='change_status'),
    path('resignation/<int:resignation_id>/process/', views.process_resignation, name='process_resignation'),

    #leave
    path('leave/',views.leave,name='leave'),
    path('leave/status/',views.leave_status,name='leave_status'),
    path('leave/manager', views.manager_approval, name='manager_review_resignation'),
    path('leave/status/approval/<int:leave_id>/', views.process_leave, name='process_leave'),


    #finance
    path('finance/',views.finance,name='finance'),
    path("add-salary/", views.add_salary, name="add_salary"),
    path("get-salary-details/", views.get_salary_details, name="get_salary_details"),
    path("finance/export/", views.export_salaries, name="export_salaries"),
    path("reimbursement/", views.reimbursement, name="reimbursement"),
    path("hr/review/", views.hr_review_reimbursements, name="hr_review_reimbursements"),
    path("hr/approve/<int:reimbursement_id>/", views.approve_reimbursement, name="approve_reimbursement"),
    path("hr/reject/<int:reimbursement_id>/", views.reject_reimbursement, name="reject_reimbursement"),
    path('view-bill/<int:reimbursement_id>/', views.view_bill_file, name='view_bill'),



    path("login/otp/", views.request_otp_view, name="request_otp"),
    path("login/verify/", views.verify_otp_view, name="verify_otp"),






    
]

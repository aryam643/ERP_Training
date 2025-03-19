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

    path('projects/add/', views.add_project, name='add_project'),
    path('proj_des/<int:project_id>/', views.proj_des, name='proj_des'),
    path('update-project/<int:id>/', views.update_project, name='update_project'),
    path('delete_project/<int:id>/', views.delete_project, name='delete_project'),
    path('change-status/<int:project_id>/', views.change_status, name='change_status'),

    #Calendar
    path("calendar/", views.project_calendar, name="calendar"),
    path("calendar/events/", views.calendar_events, name="calendar_events"),

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

    #resignation
    path('resignation',views.resign,name='resignation'),
    path('resignation/manager', views.manager_resign, name='manager_review_resignation'),
    path('resignation/hr/<int:id>/', views.hr_resign, name='hr_review_resignation'),
    path('resignation/status/', views.resignation_status, name='resignation_status'),
    path('resign/delete',views.delete_resign,name='delete_resign'),
    path('resignation/status/feedback/<int:resignation_id>/', views.resignation_feedback, name='resignation_feedback'),
    path('change-status/<int:resignation_id>/', views.change_status, name='change_status'),
    path('resignation/<int:resignation_id>/process/', views.process_resignation, name='process_resignation'),


    
]

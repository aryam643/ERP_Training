from django.contrib import admin
from .models import *

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display=('id','email','first_name','last_name','role','is_active')
    search_fields=('email','first_name','last_name','role')
    list_filter=('role','is_active')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display=('id','project_name','manager','start_date','end_date','status')
    search_fields=('project_name','manager__email')
    list_filter=('status','start_date','end_date')
    filter_horizontal=('members',)

admin.site.register(Attendance)
admin.site.register(ProjectUpdate)
admin.site.register(ProjectComment)
admin.site.register(ResignRequest)
admin.site.register(Holiday)
admin.site.register(Room)
admin.site.register(Booking)
admin.site.register(Leave)
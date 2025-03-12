from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.contrib.auth.models import BaseUserManager, PermissionsMixin, AbstractBaseUser
from django.utils.timezone import now


# Custom Manager for User Model
class UserManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, password=None, role="Employee"):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=role,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, first_name, last_name, password):
        user = self.create_user(email=email,
                                 username=username,
                                first_name=first_name,
                                last_name =last_name,
                                password =password, 
                                role="Admin",)
        user.is_staff=True
        user.is_superuser=True 
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):  # ✅ Make sure you inherit PermissionsMixin
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('HR', 'HR'),
        ('Manager', 'Manager'),
        ('Employee', 'Employee'),
    ]
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Employee')
    manager=models.ForeignKey('self',on_delete=models.SET_NULL,null=True,related_name='team',blank=True)

    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  # ✅ This is required for Django Admin

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = UserManager()

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"



class Project(models.Model):
    project_name = models.CharField(max_length=200)  # Changed from TextField to CharField
    manager = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='managed_projects')
    members = models.ManyToManyField('User', related_name='projects', blank=True)
    proj_des = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()

    STATUS_CHOICES = [
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions=[
            ('can_view_project','Can view project'),
            ('can_add_project','Can add project'),
            ('can_edit_project','Can edit project'),
            ('can_delete_project','Can delete project'),
        ]

    def __str__(self):
        return f"{self.project_name} {self.status} {self.members} {self.manager}"
    

class Attendance(models.Model):
    user=models.ForeignKey('User',on_delete=models.CASCADE)
    login_time=models.DateTimeField()
    logout_time=models.DateTimeField(null=True,blank=True)
    duration=models.DurationField(null=True,blank=True)

    def save(self,*args, **kwargs):
        if self.logout_time:
            self.duration=self.logout_time-self.login_time
        super().save(*args,**kwargs)
    def __str__(self):
        return f"{self.login_time}"


class ProjectUpdate(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="updates")
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[('Started', 'Started'), ('Updated', 'Updated'), ('Completed', 'Completed')])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.project_name} - {self.updated_by.username} ({self.status})"

class ProjectComment(models.Model):
    update = models.ForeignKey(ProjectUpdate, on_delete=models.CASCADE, related_name="comments")
    commented_by = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    approved=models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.commented_by.username} on {self.update.project.project_name}"

class ResignRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    feedback=models.TextField(blank=True)
    manager_approved = models.BooleanField(default=False)
    hr_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Feedback fields
    overall_satisfaction = models.CharField(max_length=20, blank=True)
    work_environment = models.CharField(max_length=20, blank=True)
    reason_for_leaving = models.TextField(blank=True)
    manager_experience = models.CharField(max_length=20, blank=True)
    growth_opportunities = models.CharField(max_length=20, blank=True)
    compensation_satisfaction = models.CharField(max_length=20, blank=True)
    work_life_balance = models.CharField(max_length=20, blank=True)
    recommend_company = models.CharField(max_length=10, blank=True)
    additional_feedback = models.TextField(blank=True)
    hr_comments=models.TextField(blank=True)
    manager_comments=models.TextField(blank=True)



    def __str__(self):
        return f"{self.user.username} - {self.status}"
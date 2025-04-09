from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.contrib.auth.models import BaseUserManager, PermissionsMixin, AbstractBaseUser
from django.utils.timezone import now
from django.utils import timezone



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


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('HR', 'HR'),
        ('Manager', 'Manager'),
        ('Employee', 'Employee'),
    ]
    LOCATION_CHOICES=[
        ('IN','IN'),
        ('USA','USA'),
        ('UK','UK'),
        ('CA','CA'),
        ('AU','AU'),
    ]
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Employee')
    location=models.CharField(max_length=50,choices=LOCATION_CHOICES,default='India')
    manager=models.ForeignKey('self',on_delete=models.SET_NULL,null=True,related_name='team',blank=True)

    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False) 

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
        return f"({self.login_time}-{self.user.username})"


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
    
class Holiday(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    country = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name} - {self.date} ({self.country})"
    
class Room(models.Model):
    name = models.CharField(max_length=50, unique=True)
    capacity = models.IntegerField(default=1)
    amenities = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)


    def __str__(self):
        return self.name

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.room.name} booked by {self.user.username}"

    class Meta:
        unique_together = ("room", "start_time", "end_time")


class Leave(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    start_date=models.DateField()
    end_date=models.DateField()
    reason=models.TextField()
    STATUS_CHOICES=[
        ('Pending','Pending'),
        ('Approved','Approved'),
        ('Rejected','Rejected'),
    ]
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default='Pending')
    manager_approved=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user.username} - {self.status}"
    
class Finance(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    amount=models.DecimalField(max_digits=10,decimal_places=2)
    description=models.TextField()
    STATUS_CHOICES=[
        ('Paid','Paid'),
        ('Unpaid','Unpaid'),

    ]
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default='Unpaid')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    # Salary-related fields
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # Default 10% tax

    def calculate_salary(self):
        tax_amount = (self.basic_salary * self.tax_percentage) / 100
        return self.basic_salary + self.allowances - self.deductions - tax_amount

    def save(self, *args, **kwargs):
        salary_date = self.created_at if self.created_at else timezone.now()
        self.description = f"Salary for {salary_date.strftime('%B %Y')}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.status})"
    

class Reimbursement(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    members_list = models.ManyToManyField(User, related_name="reimbursement_members")
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    bill_file = models.FileField(upload_to="reimbursements/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    approved_by_hr = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="hr_approver"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Reimbursement - {self.user.username} ({self.amount})"


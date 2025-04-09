from django import forms
from .models import *
from django.core.exceptions import ValidationError


class UserRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=254, required=True)
    username = forms.CharField(max_length=150, required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password", required=True)
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password", required=True)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):

        user = User.objects.create_user( 
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            email=self.cleaned_data["email"],
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password1"],  
        )

        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """User login form"""
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["project_name", "members", "proj_des", "start_date", "end_date", "status"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username"]

class ResignationFeedbackForm(forms.ModelForm):
    SATISFACTION_CHOICES = [
        ('Very Satisfied', 'Very Satisfied'),
        ('Satisfied', 'Satisfied'),
        ('Neutral', 'Neutral'),
        ('Dissatisfied', 'Dissatisfied'),
        ('Very Dissatisfied', 'Very Dissatisfied'),
    ]
    
    RECOMMEND_CHOICES = [
        ('Yes', 'Yes'),
        ('Maybe', 'Maybe'),
        ('No', 'No'),
    ]

    overall_satisfaction = forms.ChoiceField(choices=SATISFACTION_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    work_environment = forms.ChoiceField(choices=SATISFACTION_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    reason_for_leaving = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-textarea'}), required=True)
    manager_experience = forms.ChoiceField(choices=SATISFACTION_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    growth_opportunities = forms.ChoiceField(choices=SATISFACTION_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    compensation_satisfaction = forms.ChoiceField(choices=SATISFACTION_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    work_life_balance = forms.ChoiceField(choices=SATISFACTION_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    recommend_company = forms.ChoiceField(choices=RECOMMEND_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    additional_feedback = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-textarea'}), required=False)

    class Meta:
        model = ResignRequest
        fields = [
            'overall_satisfaction',
            'work_environment',
            'reason_for_leaving',
            'manager_experience',
            'growth_opportunities',
            'compensation_satisfaction',
            'work_life_balance',
            'recommend_company',
            'additional_feedback'
        ]
class ManagerFeedback(forms.ModelForm):
    manager_comments=forms.CharField(widget=forms.Textarea(attrs={'class': 'form-textarea'}), required=True)

    class Meta:
        model=ResignRequest
        fields=['manager_comments']

class HRFeedback(forms.ModelForm):
    hr_comments=forms.CharField(widget=forms.Textarea(attrs={'class': 'form-textarea'}), required=True)
    
    class Meta:
        model=ResignRequest
        fields=['hr_comments']

class BookingForm(forms.ModelForm):
    room = forms.ModelChoiceField(
        queryset=Room.objects.all(),  # Dynamically fetch rooms
        empty_label="Select a Room",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )

    class Meta:
        model = Booking
        fields = ["room", "start_time", "end_time"]

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time:
            if start_time < now():
                raise forms.ValidationError("Start time cannot be in the past.")
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time.")

        return cleaned_data

class LeaveApplicationForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    reason = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-textarea'}), required=True)

    class Meta:
        model = Leave
        fields = ["start_date", "end_date", "reason"]

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date:
            if start_date < now().date():
                raise forms.ValidationError("Start date cannot be in the past.")
            if start_date >= end_date:
                raise forms.ValidationError("End date must be after the start date.")

        return cleaned_data
    


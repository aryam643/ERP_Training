from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import *
import csv
from io import StringIO

class UserAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            email="employee@example.com",
            username="employee",
            first_name="John",
            last_name="Doe",
            password="password123",
            role="Employee"
        )
        self.manager = get_user_model().objects.create_user(
            email="manager@example.com",
            username="manager",
            first_name="Jane",
            last_name="Smith",
            password="password123",
            role="Manager"
        )

    def test_employee_access_project_list(self):
        self.client.login(email="employee@example.com", password="password123")
        response = self.client.get('/projects/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Project List")

    def test_manager_access_project_list(self):
        self.client.login(email="manager@example.com", password="password123")
        response = self.client.get('/projects/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Project List")

class ProjectTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.manager = get_user_model().objects.create_user(
            email="manager@example.com",
            username="manager",
            first_name="Jane",
            last_name="Smith",
            password="password123",
            role="Manager"
        )
        self.project = Project.objects.create(
            project_name="Test Project",
            manager=self.manager,
            start_date="2025-01-01",
            end_date="2025-12-31"
        )

    def test_manager_can_delete_project(self):
        self.client.login(email="manager@example.com", password="password123")
        response = self.client.post(reverse('delete_project', args=[self.project.id]))
        self.assertEqual(response.status_code, 302)  # Redirect after deletion
        self.assertFalse(Project.objects.filter(id=self.project.id).exists())

class LeaveApprovalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.manager = get_user_model().objects.create_user(
            email="manager@example.com",
            username="manager",
            first_name="Jane",
            last_name="Smith",
            password="password123",
            role="Manager"
        )
        self.employee = get_user_model().objects.create_user(
            email="employee@example.com",
            username="employee",
            first_name="John",
            last_name="Doe",
            password="password123",
            role="Employee"
        )
        self.leave = Leave.objects.create(
            user=self.employee,
            start_date="2025-05-01",
            end_date="2025-05-05",
            reason="Vacation",
            status="Pending"
        )

    def test_manager_approves_leave(self):
        self.client.login(email="manager@example.com", password="password123")
        response = self.client.post(reverse('process_leave', args=[self.leave.id]), {'manager_approved': 'true'})
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.status, "Approved")

class ReimbursementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.employee = get_user_model().objects.create_user(
            email="employee@example.com",
            username="employee",
            first_name="John",
            last_name="Doe",
            password="password123",
            role="Employee"
        )

    def test_create_reimbursement_request(self):
        self.client.login(email="employee@example.com", password="password123")
        response = self.client.post('/reimbursement/', {
            'date': '2025-04-29',
            'amount': 1000,
            'description': 'Travel expenses',
            'bill_file': ''
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertEqual(Reimbursement.objects.count(), 1)

class SalaryExportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr = get_user_model().objects.create_user(
            email="hr@example.com",
            username="hr",
            first_name="Alice",
            last_name="Johnson",
            password="password123",
            role="HR"
        )

    def test_export_salaries(self):
        self.client.login(email="hr@example.com", password="password123")
        response = self.client.get('/finance/export/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

        # Validate CSV content
        csv_file = StringIO(response.content.decode('utf-8'))
        reader = csv.reader(csv_file)
        header = next(reader)
        self.assertEqual(header, ["Employee", "Month", "Net Salary", "Status"])


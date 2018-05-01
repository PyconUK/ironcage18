from django.test import TestCase

from accounts.tests import factories as accounts_factories
from tickets.tests import factories as tickets_factories

from reports import reports


class ReportsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = accounts_factories.create_staff_user(
            name='Alice',
            email_addr='alice@example.com',
        )
        cls.bob = accounts_factories.create_user(
            name='Bob',
            email_addr='bob@example.com',
        )

    def setUp(self):
        self.client.force_login(self.alice)


class TestIndex(ReportsTestCase):
    def test_get(self):
        rsp = self.client.get('/reports/')
        self.assertEqual(rsp.status_code, 200)
        self.assertContains(rsp, '<li><a href="/reports/attendance-by-day/">Attendance by day</a></li>', html=True)

    def test_get_when_not_staff(self):
        self.client.force_login(self.bob)
        rsp = self.client.get('/reports/', follow=True)
        self.assertContains(rsp, "Your account doesn't have access to this page")
        self.assertRedirects(rsp, '/accounts/login/?next=/reports/')

    def test_get_when_not_authenticated(self):
        self.client.logout()
        rsp = self.client.get('/reports/', follow=True)
        self.assertRedirects(rsp, '/accounts/login/?next=/reports/')


class TestAttendanceByDayReport(ReportsTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        tickets_factories.create_ticket(num_days=1)
        tickets_factories.create_ticket(num_days=2, rate='corporate')
        tickets_factories.create_ticket(num_days=3)
        tickets_factories.create_ticket(num_days=4, rate='corporate')
        tickets_factories.create_ticket(num_days=5)

    def test_get_context_data(self):
        report = reports.AttendanceByDayReport()
        expected = {
            'title': 'Attendance by day',
            'headings': ['Day', 'Individual rate', 'Corporate rate', 'Unwaged rate', 'Free', 'Total'],
            'rows': [
                ['Saturday', 3, 2, 0, 0, 5],
                ['Sunday', 2, 2, 0, 0, 4],
                ['Monday', 2, 1, 0, 0, 3],
                ['Tuesday', 1, 1, 0, 0, 2],
                ['Wednesday', 1, 0, 0, 0, 1],
            ],
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/attendance-by-day/')
        self.assertEqual(rsp.status_code, 200)

    def test_get_when_not_staff(self):
        self.client.force_login(self.bob)
        rsp = self.client.get('/reports/attendance-by-day/', follow=True)
        self.assertContains(rsp, "Your account doesn't have access to this page")
        self.assertRedirects(rsp, '/accounts/login/?next=/reports/attendance-by-day/')

    def test_get_when_not_authenticated(self):
        self.client.logout()
        rsp = self.client.get('/reports/attendance-by-day/', follow=True)
        self.assertRedirects(rsp, '/accounts/login/?next=/reports/attendance-by-day/')


class TestTicketSalesReport(ReportsTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        tickets_factories.create_ticket(num_days=1)
        tickets_factories.create_ticket(num_days=2, rate='corporate')
        tickets_factories.create_ticket(num_days=3)
        tickets_factories.create_ticket(num_days=4, rate='corporate')
        tickets_factories.create_ticket(num_days=5)

    def test_get_context_data(self):
        report = reports.TicketSalesReport()
        expected = {
            'title': 'Ticket sales',
            'headings': ['Days', 'Individual rate', 'Corporate rate', 'Unwaged rate', 'Free', 'Total'],
            'num_tickets_rows': [
                [1, 1, 0, 0, 0, 1],
                [2, 0, 1, 0, 0, 1],
                [3, 1, 0, 0, 0, 1],
                [4, 0, 1, 0, 0, 1],
                [5, 1, 0, 0, 0, 1],
            ],
            'ticket_cost_rows': [
                [1, '£65', '£0', '£0', '£0', '£65'],
                [2, '£0', '£195', '£0', '£0', '£195'],
                [3, '£125', '£0', '£0', '£0', '£125'],
                [4, '£0', '£315', '£0', '£0', '£315'],
                [5, '£185', '£0', '£0', '£0', '£185'],
            ]
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/ticket-sales/')
        self.assertEqual(rsp.status_code, 200)

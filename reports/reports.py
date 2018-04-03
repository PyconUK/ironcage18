from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.generic import TemplateView

from accounts.models import User
from tickets.constants import DAYS
from tickets.models import Order, Ticket
from tickets.prices import PRICES_EXCL_VAT, cost_incl_vat


@method_decorator(staff_member_required(login_url='login'), name='dispatch')
class ReportView(TemplateView):
    template_name = 'reports/report.html'

    def get_context_data(self):
        return {
            'title': self.title,
            'headings': self.headings,
            'rows': self.get_rows(),
        }

    def get_rows(self):
        return [self.presenter(item) for item in self.get_queryset()]

    @classmethod
    def path(cls):
        return f'^{slugify(cls.title)}/$'

    @classmethod
    def url_name(cls):
        return slugify(cls.title)

    @classmethod
    def namespaced_url_name(cls):
        return f'reports:{cls.url_name()}'


class TicketSummaryReport(ReportView):
    title = 'Ticket summary'

    def get_context_data(self):
        tickets = Ticket.objects.all()

        rows = [
            ['Tickets', len(tickets)],
            ['Days', sum(t.num_days() for t in tickets)],
            ['Cost (excl. VAT)', f'£{sum(t.cost_excl_vat() for t in tickets)}'],
        ]

        return {
            'title': self.title,
            'rows': rows,
            'headings': [],
        }


class AttendanceByDayReport(ReportView):
    title = 'Attendance by day'

    def get_context_data(self):
        tickets = Ticket.objects.all()

        rows = []

        for day in DAYS:
            num_tickets = {rate: 0 for rate in PRICES_EXCL_VAT}

            for ticket in tickets:
                if getattr(ticket, day):
                    num_tickets[ticket.rate] += 1

            rows.append([
                DAYS[day],
                num_tickets['individual'],
                num_tickets['corporate'],
                num_tickets['education'],
                num_tickets['free'],
                num_tickets['individual'] + num_tickets['corporate'] + num_tickets['education'] + num_tickets['free'],
            ])

        return {
            'title': self.title,
            'headings': ['Day', 'Individual rate', 'Corporate rate', 'Education rate', 'Free', 'Total'],
            'rows': rows,
        }


class UKPAReport(ReportView):
    title = 'UKPA Membership'

    def get_context_data(self):
        members = User.objects.filter(is_ukpa_member=True)
        rows = [[member.name, member.email_addr] for member in members]

        return {
            'title': self.title,
            'headings': ['Name', 'email'],
            'rows': rows,
        }


class TicketSalesReport(ReportView):
    title = 'Ticket sales'
    template_name = 'reports/ticket_sales_report.html'

    def get_context_data(self):
        tickets = Ticket.objects.all()

        num_tickets_rows = []
        ticket_cost_rows = []

        for ix in range(5):
            num_days = ix + 1
            individual_rate = cost_incl_vat('individual', num_days)
            corporate_rate = cost_incl_vat('corporate', num_days)
            education_rate = cost_incl_vat('education', num_days)

            num_tickets = {rate: 0 for rate in PRICES_EXCL_VAT}

            for ticket in tickets:
                if sum(getattr(ticket, day) for day in DAYS) == num_days:
                    num_tickets[ticket.rate] += 1

            num_tickets_rows.append([
                num_days,
                num_tickets['individual'],
                num_tickets['corporate'],
                num_tickets['education'],
                num_tickets['free'],
                num_tickets['individual'] + num_tickets['corporate'] + num_tickets['education'] + num_tickets['free'],
            ])

            ticket_cost_rows.append([
                num_days,
                f'£{num_tickets["individual"] * individual_rate}',
                f'£{num_tickets["corporate"] * corporate_rate}',
                f'£{num_tickets["education"] * education_rate}',
                f'£0',
                f'£{num_tickets["individual"] * individual_rate + num_tickets["corporate"] * corporate_rate + num_tickets["education"] * education_rate}',
            ])

        return {
            'title': self.title,
            'headings': ['Days', 'Individual rate', 'Corporate rate', 'Education rate', 'Free', 'Total'],
            'num_tickets_rows': num_tickets_rows,
            'ticket_cost_rows': ticket_cost_rows,
        }


class OrdersMixin:
    headings = ['ID', 'Rate', 'Purchaser', 'Email', 'Tickets', 'Cost (incl. VAT)', 'Status']

    def presenter(self, order):
        link = {
            'href': reverse('reports:tickets_order', args=[order.order_id]),
            'text': order.order_id,
        }
        return [
            link,
            order.rate,
            order.purchaser.name,
            order.purchaser.email_addr,
            order.num_tickets(),
            f'£{order.cost_incl_vat}',
            order.status,
        ]


class OrdersReport(ReportView, OrdersMixin):
    title = 'All orders'

    def get_queryset(self):
        return Order.objects.all()


class UnpaidOrdersReport(ReportView, OrdersMixin):
    title = 'Unpaid orders'

    def get_queryset(self):
        return Order.objects.exclude(status='successful')


class TicketsMixin:
    headings = ['ID', 'Rate', 'Ticket holder', 'Days', 'Cost (incl. VAT)', 'Status']

    def presenter(self, ticket):
        link = {
            'href': reverse('reports:tickets_ticket', args=[ticket.ticket_id]),
            'text': ticket.ticket_id,
        }
        return [
            link,
            ticket.rate,
            ticket.ticket_holder_name(),
            ', '.join(ticket.days()),
            f'£{ticket.cost_incl_vat}',
            'Assigned' if ticket.owner else 'Unclaimed',
        ]


class TicketsReport(ReportView, TicketsMixin):
    title = 'All tickets'

    def get_queryset(self):
        return Ticket.objects.all()


class UnclaimedTicketsReport(ReportView, TicketsMixin):
    title = 'Unclaimed tickets'

    def get_queryset(self):
        return Ticket.objects.filter(owner=None).order_by('id')


class AttendeesWithAccessibilityReqs(ReportView):
    title = 'Attendees with accessibility requirements'

    headings = [
        'Name',
        'Email',
        'Requirements',
    ]

    def get_queryset(self):
        return User.objects.filter(accessibility_reqs_yn=True)

    def presenter(self, user):
        return [user.name, user.email_addr, user.accessibility_reqs]


class AttendeesWithChildcareReqs(ReportView):
    title = 'Attendees with childcare requirements'

    headings = [
        'Name',
        'Email',
        'Requirements',
    ]

    def get_queryset(self):
        return User.objects.filter(childcare_reqs_yn=True)

    def presenter(self, user):
        return [user.name, user.email_addr, user.childcare_reqs]


class AttendeesWithDietaryReqs(ReportView):
    title = 'Attendees with dietary requirements'

    headings = [
        'Name',
        'Email',
        'Requirements',
    ]

    def get_queryset(self):
        return User.objects.filter(dietary_reqs_yn=True)

    def presenter(self, user):
        return [user.name, user.email_addr, user.dietary_reqs]


class PeopleMixin:
    headings = ['ID', 'Name', 'Email address']

    def presenter(self, user):
        link = {
            'href': reverse('reports:accounts_user', args=[user.user_id]),
            'text': user.user_id,
        }

        return [
            link,
            user.name,
            user.email_addr,
        ]


class PeopleReport(ReportView, PeopleMixin):
    title = 'People'

    def get_queryset(self):
        return User.objects.order_by('name').all()


class StaffReport(ReportView, PeopleMixin):
    title = 'Staff'

    def get_queryset(self):
        return User.objects.filter(is_staff=True).order_by('name')


reports = [
    AttendanceByDayReport,
    TicketSummaryReport,
    TicketSalesReport,
    OrdersReport,
    UnpaidOrdersReport,
    TicketsReport,
    UnclaimedTicketsReport,
    AttendeesWithAccessibilityReqs,
    AttendeesWithChildcareReqs,
    AttendeesWithDietaryReqs,
    PeopleReport,
    StaffReport,
]

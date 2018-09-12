from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from accounts.models import User, Badge
from cfp.models import Proposal
from grants.models import Application
from ironcage.admin import OurActionsOnlyMixin, RequirementsListFilter
from tickets.models import Ticket


class AccessibilityListFilter(RequirementsListFilter):
    title = 'Accessibility Requirements'

    parameter_name = 'accessibility_reqs'


class ChildcareListFilter(RequirementsListFilter):
    title = 'Childcare Requirements'

    parameter_name = 'childcare_reqs'


class DietaryListFilter(RequirementsListFilter):
    title = 'Dietary Requirements'

    parameter_name = 'dietary_reqs'


class TicketInline(OurActionsOnlyMixin, admin.TabularInline):
    model = Ticket
    view_on_site = False

    def link_to_ticket(self, obj):
        url = reverse('admin:tickets_ticket_change', args=[obj.id])
        return format_html("<a href='{}'>{}</a>", url, obj.ticket_id)
    link_to_ticket.admin_order_field = 'ticket_id'
    link_to_ticket.short_description = 'ticket'

    fields = readonly_fields = ('link_to_ticket', 'rate', 'sat', 'sun', 'mon', 'tue', 'wed')


class ProposalInline(OurActionsOnlyMixin, admin.TabularInline):
    model = Proposal
    view_on_site = False

    def link_to_proposal(self, obj):
        url = reverse('admin:cfp_proposal_change', args=[obj.id])
        return format_html("<a href='{}'>{}</a>", url, obj.proposal_id)
    link_to_proposal.admin_order_field = 'proposal_id'
    link_to_proposal.short_description = 'proposal'

    fields = readonly_fields = ('link_to_proposal', 'title', 'state')


class ApplicationInline(OurActionsOnlyMixin, admin.TabularInline):
    model = Application
    view_on_site = False

    def link_to_application(self, obj):
        url = reverse('admin:grants_application_change', args=[obj.id])
        return format_html("<a href='{}'>{}</a>", url, obj.application_id)
    link_to_application.admin_order_field = 'application_id'
    link_to_application.short_description = 'application'

    fields = readonly_fields = ('link_to_application', 'ticket_awarded', 'amount_awarded', 'application_declined')


admin.site.register(Badge)

@admin.register(User)
class UserAdmin(OurActionsOnlyMixin, admin.ModelAdmin):

    inlines = [
        TicketInline,
        ProposalInline,
        ApplicationInline
    ]

    search_fields = ['name', 'email_addr']

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ['name', 'email_addr', 'last_login', 'is_contributor',
                    'is_organiser', 'is_staff', 'is_active', 'is_superuser',
                    'groups', 'user_permissions', 'accessibility_reqs',
                    'childcare_reqs', 'dietary_reqs']
        else:
            return ['name', 'is_contributor', 'is_organiser']

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ['last_login', 'email_addr', 'name', 'accessibility_reqs',
                    'childcare_reqs', 'dietary_reqs']
        else:
            return self.get_fields(request, obj)

    def get_list_display(self, request):

        if request.user.is_superuser:
            fields = ['user_id', 'name', 'email_addr', 'is_staff',
                      'is_contributor', 'is_organiser']

            long_fields = ['accessibility_reqs', 'childcare_reqs', 'dietary_reqs']

            for field in long_fields:
                if request.GET.get(field):
                    fields.append(field)

            return fields
        else:
            return ['user_id', 'name', 'is_contributor', 'is_organiser']

    def get_list_filter(self, request):

        if request.user.is_superuser:
            return ['is_contributor', 'is_organiser', 'is_staff',
                    AccessibilityListFilter, ChildcareListFilter,
                    DietaryListFilter]
        else:
            return ['is_contributor', 'is_organiser']

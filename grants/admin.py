from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from grants.models import Application
from ironcage.admin import OurActionsOnlyMixin


@admin.register(Application)
class ApplicationAdmin(OurActionsOnlyMixin, admin.ModelAdmin):

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ('id', 'link_to_applicant', 'about_you', 'about_why',
                    'requested_ticket_only', 'amount_requested',
                    'cost_breakdown', 'sat', 'sun', 'mon', 'tue', 'wed',
                    'ticket_awarded', 'amount_awarded')

        return []

    def get_readonly_fields(self, request, obj=None):
        fields = list(self.get_fields(request, obj))
        # fields.remove('ticket_awarded')
        # fields.remove('amount_awarded')
        return fields

    list_display = ('applicant_name', 'requested_ticket_only', 'amount_requested', 'ticket_awarded', 'amount_awarded', 'full_amount_awarded', 'application_declined', 'response_sent')

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return ['requested_ticket_only', 'replied_to']

    def get_search_fields(self, request):
        if request.user.is_superuser:
            return ['applicant__name', 'applicant__email_addr']

        return []

    def applicant_name(self, obj):
        return obj.applicant.name

    def link_to_applicant(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.applicant.id])
        return format_html("<a href='{}'>{}</a>", url, obj.applicant.name)
    link_to_applicant.admin_order_field = 'applicant__name'
    link_to_applicant.short_description = 'applicant'

    def response_sent(self, obj):
        return obj.replied_to is not None

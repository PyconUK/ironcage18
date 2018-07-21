from django.contrib import admin
from grants.models import Application
from ironcage.admin import OurActionsOnlyMixin


@admin.register(Application)
class ApplicationAdmin(OurActionsOnlyMixin, admin.ModelAdmin):

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ('id', 'applicant_name', 'about_you', 'about_why',
                    'requested_ticket_only', 'amount_requested',
                    'cost_breakdown', 'sat', 'sun', 'mon', 'tue', 'wed',
                    'ticket_awarded', 'amount_awarded')

        return []

    def get_readonly_fields(self, request, obj=None):
        fields = list(self.get_fields(request, obj))
        fields.remove('ticket_awarded')
        fields.remove('amount_awarded')
        return fields

    list_display = ('applicant_name', 'requested_ticket_only', 'amount_requested', 'ticket_awarded', 'amount_awarded', 'full_amount_awarded', 'application_declined', 'response_sent')

    list_editable = ['ticket_awarded', 'amount_awarded', 'full_amount_awarded', 'application_declined']

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return ['requested_ticket_only']

    def get_search_fields(self, request):
        if request.user.is_superuser:
            return ['applicant__name', 'applicant__email_addr']

        return []

    def applicant_name(self, obj):
        return obj.applicant.name

    def response_sent(self, obj):
        return obj.replied_to is not None

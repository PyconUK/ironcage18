from django.contrib import admin
from grants.models import Application
from ironcage.admin import OurActionsOnlyMixin


@admin.register(Application)
class ApplicationAdmin(OurActionsOnlyMixin, admin.ModelAdmin):

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ('id', 'applicant_name', 'about_you', 'about_why',
                    'requested_ticket_only', 'amount_requested',
                    'cost_breakdown', 'sat', 'sun', 'mon', 'tue', 'wed')

        return []

    def get_readonly_fields(self, request, obj=None):
        return self.get_fields(request, obj)

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('applicant_name', 'requested_ticket_only',
                    'amount_requested')

        return []

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return ['requested_ticket_only']

    def get_search_fields(self, request):
        if request.user.is_superuser:
            return ['applicant__name', 'applicant__email_addr']

        return []

    def applicant_name(self, obj):
        return obj.applicant.name

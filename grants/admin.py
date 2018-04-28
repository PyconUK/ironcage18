from django.contrib import admin
from grants.models import Application
from ironcage.admin import OurActionsOnlyMixin


@admin.register(Application)
class ApplicationAdmin(OurActionsOnlyMixin, admin.ModelAdmin):
    fields = readonly_fields = ('applicant_name', 'about_you', 'about_why',
                                'requested_ticket_only', 'amount_requested',
                                'cost_breakdown', 'sat', 'sun', 'mon', 'tue',
                                'wed')

    list_display = ('applicant_name', 'requested_ticket_only', 'amount_requested')
    list_filter = ('requested_ticket_only', )
    search_fields = ['applicant__name', 'applicant__email_addr']

    def applicant_name(self, obj):
        return obj.applicant.name

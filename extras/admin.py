from django.contrib import admin

from extras.models import ChildrenTicket, DinnerTicket
from ironcage.admin import OurActionsOnlyMixin
from orders.models import OrderRow


@admin.register(ChildrenTicket)
class ChildrenTicketAdmin(OurActionsOnlyMixin, admin.ModelAdmin):

    readonly_fields = fields = ['adult_name', 'adult_email_addr',
                                'adult_phone_number', 'accessibility_reqs',
                                'dietary_reqs', 'name', 'age']


@admin.register(DinnerTicket)
class DinnerTicketAdmin(OurActionsOnlyMixin, admin.ModelAdmin):

    readonly_fields = fields = ['ticket_owner_name', 'dinner', 'starter', 'main', 'dessert', 'is_free']

    search_fields = ['extra_item__owner__name']

    list_display = ['ticket_owner_name', 'dinner', 'starter', 'main', 'dessert', 'is_free']
    list_filter = ['dinner']

    def ticket_owner_name(self, obj):
        return obj.extra_item.get().owner.name

    def is_free(self, obj):
        try:
            obj.extra_item.get().order
            return False
        except OrderRow.DoesNotExist:
            return True

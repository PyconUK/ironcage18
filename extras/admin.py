from django.contrib import admin

from extras.models import ChildrenTicket, DinnerTicket
from ironcage.admin import OurActionsOnlyMixin


@admin.register(ChildrenTicket)
class ChildrenTicketAdmin(OurActionsOnlyMixin, admin.ModelAdmin):

    readonly_fields = fields = ['adult_name', 'adult_email_addr',
                                'adult_phone_number', 'accessibility_reqs',
                                'dietary_reqs', 'name', 'age']


@admin.register(DinnerTicket)
class DinnerTicketAdmin(OurActionsOnlyMixin, admin.ModelAdmin):

    readonly_fields = fields = ['dinner', 'starter', 'main', 'dessert']

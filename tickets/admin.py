from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from tickets.models import Ticket

from django_object_actions import DjangoObjectActions
from ironcage.admin import OurActionsOnlyMixin

@admin.register(Ticket)
class TicketAdmin(DjangoObjectActions, OurActionsOnlyMixin, admin.ModelAdmin):

    view_on_site = False
    fields = readonly_fields = ('ticket_id', 'link_to_owner', 'link_to_order',
                                'sat', 'sun', 'mon', 'tue', 'wed')
    list_display = ('ticket_id', 'link_to_owner', 'link_to_order',
                    'order_status', 'sat', 'sun', 'mon', 'tue', 'wed')
    list_filter = ('order_rows__order__status', 'sat', 'sun', 'mon', 'tue', 'wed')
    search_fields = ['owner__name']

    def link_to_owner(self, obj):
        if obj.owner:
            url = reverse('admin:accounts_user_change', args=[obj.owner.id])
            return format_html("<a href='{}'>{}</a>", url, obj.owner.name)
        else:
            return None
    link_to_owner.admin_order_field = 'owner'
    link_to_owner.short_description = 'owner'

    def link_to_order(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html("<a href='{}'>{}</a>", url, obj.order.order_id)
    link_to_order.admin_order_field = 'order'
    link_to_order.short_description = 'order'

    def order_status(self, obj):
        return obj.order.status

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from tickets.models import Ticket

from django_object_actions import DjangoObjectActions


class OurActionsOnlyMixin():

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


@admin.register(Ticket)
class TicketAdmin(DjangoObjectActions, OurActionsOnlyMixin, admin.ModelAdmin):

    view_on_site = False
    fields = readonly_fields = ('ticket_id', 'link_to_owner', 'link_to_order', 'sat', 'sun', 'mon', 'tue', 'wed')
    list_display = ('ticket_id', 'link_to_owner', 'link_to_order', 'sat', 'sun', 'mon', 'tue', 'wed')
    list_filter = ('sat', 'sun', 'mon', 'tue', 'wed')
    search_fields = ['owner__name']

    def link_to_owner(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.owner.id])
        return format_html("<a href='{}'>{}</a>", url, obj.owner.name)
    link_to_owner.admin_order_field = 'owner'
    link_to_owner.short_description = 'owner'

    def link_to_order(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html("<a href='{}'>{}</a>", url, obj.order.id)
    link_to_order.admin_order_field = 'order'

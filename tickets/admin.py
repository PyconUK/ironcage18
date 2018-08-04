from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from tickets.models import Ticket, TicketInvitation

from ironcage.admin import OurActionsOnlyMixin


@admin.register(Ticket)
class TicketAdmin(OurActionsOnlyMixin, admin.ModelAdmin):

    view_on_site = False
    fields = readonly_fields = ('ticket_id', 'link_to_owner', 'link_to_order',
                                'sat', 'sun', 'mon', 'tue', 'wed', 'free_reason')
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
        if obj.order:
            url = reverse('admin:orders_order_change', args=[obj.order.id])
            return format_html("<a href='{}'>{}</a>", url, obj.order.order_id)
        return None
    link_to_order.admin_order_field = 'order'
    link_to_order.short_description = 'order'

    def order_status(self, obj):
        if obj.order:
            return obj.order.status
        return 'Free Ticket'


@admin.register(TicketInvitation)
class TicketInvitationAdmin(OurActionsOnlyMixin, admin.ModelAdmin):

    view_on_site = False
    list_filter = ('status', )

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ['link_to_ticket', 'email_addr', 'name', 'token', 'status']

        return []

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser and obj and obj.status == 'unclaimed':
            return ['link_to_ticket', 'token', 'status']

        return self.get_fields(request, obj)

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ['link_to_ticket', 'email_addr', 'name', 'token', 'status']

        return []

    def link_to_ticket(self, obj):
        if obj.ticket:
            url = reverse('admin:tickets_ticket_change', args=[obj.ticket.id])
            return format_html("<a href='{}'>{}</a>", url, obj.ticket.ticket_id)
        else:
            return None
    link_to_ticket.admin_order_field = 'ticket'
    link_to_ticket.short_description = 'ticket'

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from orders.models import Order
# from tickets.actions import refund_order

from import_export.admin import ExportMixin
from django_object_actions import DjangoObjectActions
from tickets.admin import OurActionsOnlyMixin


@admin.register(Order)
class OrderAdmin(DjangoObjectActions, OurActionsOnlyMixin, admin.ModelAdmin):

    # def refund(self, request, obj):
    #     refund_order(obj)


    def get_change_actions(self, request, object_id, form_url):
        actions = super().get_change_actions(request, object_id, form_url)
        actions = list(actions)

        obj = self.model.objects.get(pk=object_id)
        # if obj.status == 'successful':
        #     actions.append('refund')

        return actions

    view_on_site = False
    fields = ('link_to_purchaser', 'invoice_number', 'status', 'stripe_charge_id', 'stripe_charge_created',
              'stripe_charge_failure_reason', 'billing_name', 'billing_addr')
    readonly_fields = ('link_to_purchaser', 'invoice_number', 'status', 'stripe_charge_id',
                       'stripe_charge_created', 'stripe_charge_failure_reason')
    list_display = ('order_id', 'link_to_purchaser', 'status')
    list_filter = ('status', )
    search_fields = ['purchaser__name']

    def link_to_purchaser(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.purchaser.id])
        return format_html("<a href='{}'>{}</a>", url, obj.purchaser.name)
    link_to_purchaser.admin_order_field = 'purchaser'
    link_to_purchaser.short_description = 'purchaser'

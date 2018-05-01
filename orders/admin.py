from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from orders.models import Order, OrderRow
# from tickets.actions import refund_order

# from import_export.admin import ExportMixin
# from django_object_actions import DjangoObjectActions
from ironcage.admin import OurActionsOnlyMixin


class OrderRowInline(OurActionsOnlyMixin, admin.TabularInline):
    model = OrderRow

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ['link_to_item', 'item_descr', 'item_descr_extra',
                    'row_cost_inc_vat']
        else:
            return ['link_to_item', 'item_descr', 'item_descr_extra']

    def get_readonly_fields(self, request, obj=None):
        return self.get_fields(request, obj)

    def link_to_item(self, obj):
        url = reverse(
            f'admin:{obj.content_type.app_label}_{obj.content_type}_change',
            args=[obj.object_id]
        )
        return format_html("<a href='{}'>{}: {}</a>", url,
                           str(obj.content_type).capitalize(), obj.item)
    link_to_item.admin_order_field = 'item'
    link_to_item.short_description = 'item'

    def row_cost_inc_vat(self, obj):
        if obj.cost_excl_vat:
            return f'£{obj.cost_incl_vat}'


@admin.register(Order)
class OrderAdmin(OurActionsOnlyMixin, admin.ModelAdmin):  # DjangoObjectActions at beginning

    # # def refund(self, request, obj):
    # #     refund_order(obj)

    # def get_change_actions(self, request, object_id, form_url):
    #     actions = super().get_change_actions(request, object_id, form_url)
    #     actions = list(actions)

    #     obj = self.model.objects.get(pk=object_id)
    #     # if obj.status == 'successful':
    #     #     actions.append('refund')

    #     return actions

    view_on_site = False

    list_filter = ('status', )

    search_fields = ['purchaser__name']

    inlines = [
        OrderRowInline,
    ]

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ['link_to_purchaser', 'invoice_number', 'status',
                    'stripe_charge_id', 'stripe_charge_created',
                    'stripe_charge_failure_reason', 'billing_name',
                    'billing_addr']
        else:
            return ['link_to_purchaser', 'invoice_number', 'status']

    def get_readonly_fields(self, request, obj=None):
        return self.get_fields(request, obj)

    def get_list_display(self, request):

        if request.user.is_superuser:
            return ['order_id', 'link_to_purchaser',
                    'num_tickets', 'order_cost', 'status']
        else:
            return ['order_id', 'link_to_purchaser', 'num_tickets',
                    'status']

    def link_to_purchaser(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.purchaser.id])
        return format_html("<a href='{}'>{}</a>", url, obj.purchaser.name)
    link_to_purchaser.admin_order_field = 'purchaser__name'
    link_to_purchaser.short_description = 'purchaser'

    def purchaser_email(self, obj):
        return obj.purchaser.email_addr
    purchaser_email.admin_order_field = 'purchaser__email_addr'
    purchaser_email.short_description = 'email'

    def order_cost(self, obj):
        return '£{:.2f}'.format(obj.cost_pence_incl_vat / 100)

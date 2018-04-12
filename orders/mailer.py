import re

from django.conf import settings
from django.template.loader import get_template
from django.urls import reverse

from ironcage.emails import send_mail


def send_order_confirmation_mail(order):
    assert not order.payment_required()

    template = get_template('orders/emails/order-confirmation.txt')
    context = {
        'purchaser_name': order.purchaser.name,
        'num_tickets': order.num_tickets(),
        'tickets_for_others': order.tickets_for_others(),
        'ticket_for_self': order.ticket_for_self(),
        'receipt_url': settings.DOMAIN + reverse('orders:order_receipt', args=[order.order_id]),
    }
    body_raw = template.render(context)
    body = re.sub('\n\n\n+', '\n\n', body_raw)

    send_mail(
        f'PyCon UK 2018 order confirmation ({order.order_id})',
        body,
        order.purchaser.email_addr,
    )


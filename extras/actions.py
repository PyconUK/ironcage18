from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from orders.models import Order

import structlog
logger = structlog.get_logger()


def create_pending_children_ticket_order(purchaser, billing_details, unconfirmed_details):
    logger.info('create_pending_children_ticket_order', purchaser=purchaser.id)

    childrens_ticket_content_type = ContentType.objects.get(
        app_label="extras", model="childrenticket"
    )

    with transaction.atomic():
        return Order.objects.create_pending(
            purchaser,
            billing_details,
            unconfirmed_details,
            childrens_ticket_content_type
        )


def update_pending_children_ticket_order(order, billing_details, unconfirmed_details):
    logger.info('update_pending_children_ticket_order', order=order.order_id)
    with transaction.atomic():
        order.update(billing_details, unconfirmed_details)

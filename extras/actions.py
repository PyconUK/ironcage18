from datetime import datetime

import structlog
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Count

from extras.models import DINNERS, DinnerTicket, ExtraItem
from orders.models import Order

logger = structlog.get_logger()


def create_pending_children_ticket_order(purchaser, billing_details, unconfirmed_details):
    logger.info('create_pending_children_ticket_order', purchaser=purchaser.id)

    children_ticket_content_type = ContentType.objects.get(
        app_label="extras", model="childrenticket"
    )

    with transaction.atomic():
        return Order.objects.create_pending(
            purchaser,
            billing_details,
            unconfirmed_details,
            children_ticket_content_type
        )


def update_pending_children_ticket_order(order, billing_details, unconfirmed_details):
    logger.info('update_pending_children_ticket_order', order=order.order_id)
    with transaction.atomic():
        order.update(billing_details, unconfirmed_details)


def create_pending_dinner_ticket_order(purchaser, billing_details, unconfirmed_details):
    logger.info('create_pending_dinner_ticket_order', purchaser=purchaser.id)

    dinner_ticket_content_type = ContentType.objects.get(
        app_label="extras", model="dinnerticket"
    )

    with transaction.atomic():
        return Order.objects.create_pending(
            purchaser,
            billing_details,
            unconfirmed_details,
            dinner_ticket_content_type
        )


def update_pending_dinner_ticket_order(order, billing_details, unconfirmed_details):
    logger.info('update_pending_dinner_ticket_order', order=order.order_id)
    with transaction.atomic():
        order.update(billing_details, unconfirmed_details)


def update_existing_dinner_ticket_order(item, details):
    logger.info('update_existing_dinner_ticket_order', order=item.id)
    with transaction.atomic():
        item.dinner = details['dinner']
        item.starter = details['starter']
        item.main = details['main']
        item.dessert = details['dessert']
        item.save()


def create_free_dinner_ticket_order(purchaser, details):
    assert purchaser.is_contributor
    dinner_ticket_content_type = ContentType.objects.get(app_label="extras", model="dinnerticket")
    assert purchaser.extras.filter(content_type=dinner_ticket_content_type).count() < 1
    logger.info('create_free_dinner_ticket_order', purchaser=purchaser.id)

    dinner_ticket_content_type = ContentType.objects.get(
        app_label="extras", model="dinnerticket"
    )

    with transaction.atomic():
        extra_item = ExtraItem.objects.build(
            content_type=dinner_ticket_content_type,
            owner=purchaser,
            details=details
        )
        sub_item = extra_item.item
        sub_item.save()
        extra_item.item = sub_item
        extra_item.save()

    return extra_item


def check_available_dinners(location_id):
    dinners = DinnerTicket.objects.values('dinner').annotate(num_dinners=Count('dinner'))

    dinner_counts = {x['dinner']: x['num_dinners'] for x in dinners}

    ret_val = []
    # Ugh this is nasty but time is too tight to rearchitect
    for dinner in DINNERS:
        if DINNERS[dinner]['location'] == location_id:
            if (dinner_counts.get(dinner, 0) < DINNERS[dinner]['capacity'] and
                    datetime.now() < datetime.strptime('%s 15:15:00' % DINNERS[dinner]['date'], '%Y-%m-%d %H:%M:%S')):
                ret_val.append(dinner)

    return ret_val

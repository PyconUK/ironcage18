from django_slack import slack_message
import stripe

from django.db import transaction
from django.db.utils import IntegrityError

from ironcage import stripe_integration
from tickets import actions as ticket_actions

from .mailer import send_order_confirmation_mail
from .models import Refund

import structlog
logger = structlog.get_logger()


def process_stripe_charge(order, token):
    logger.info('process_stripe_charge', order=order.order_id, token=token)
    assert order.payment_required()
    try:
        charge = stripe_integration.create_charge_for_order(order, token)
        confirm_order(order, charge.id, charge.created)
    except stripe.error.CardError as e:
        mark_order_as_failed(order, e._message)
    except IntegrityError:
        stripe_integration.refund_charge(charge.id)
        mark_order_as_errored_after_charge(order, charge.id)


def confirm_order(order, charge_id, charge_created):
    logger.info('confirm_order', order=order.order_id, charge_id=charge_id)
    with transaction.atomic():
        order.confirm(charge_id, charge_created)
    send_receipt(order)
    ticket_actions.send_ticket_invitations(order)
    slack_message('orders/order_created.slack', {'order': order})


def refund_ticket(ticket, reason):
    logger.info('refund_ticket', ticket=ticket.ticket_id)
    stripe_refund = stripe_integration.refund_ticket(ticket)
    with transaction.atomic():
        Refund.objects.create_for_ticket(ticket, reason, stripe_refund.id, stripe_refund.created)


def mark_order_as_failed(order, charge_failure_reason):
    logger.info('mark_order_as_failed', order=order.order_id, charge_failure_reason=charge_failure_reason)
    with transaction.atomic():
        order.mark_as_failed(charge_failure_reason)


def mark_order_as_errored_after_charge(order, charge_id):
    logger.info('mark_order_as_errored_after_charge', order=order.order_id, charge_id=charge_id)
    with transaction.atomic():
        order.mark_as_errored_after_charge(charge_id)


def send_receipt(order):
    logger.info('send_receipt', order=order.order_id)
    send_order_confirmation_mail(order)

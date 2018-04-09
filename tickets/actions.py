# The functions defined in this module should be the only way that Orders,
# Tickets, and TicketInvitations are created or updated by the rest of the
# code.
#
# Specifically: if any view, management command, or test changes data for these
# models, that change should be made through functionsin this module.
#
# This has at least two benefits:
#
#  * It makes it easier to see how and when data is changed.
#  * The only way that data can be set up for testing is through calling
#    functions in this module.  This means that test data should always be
#    in a consistent state.

from django.db import transaction

from .mailer import send_invitation_mail
from orders.models import Order

import structlog
logger = structlog.get_logger()


def create_pending_order(purchaser, billing_details, rate, days_for_self=None, email_addrs_and_days_for_others=None):
    logger.info('create_pending_order', purchaser=purchaser.id, rate=rate)
    with transaction.atomic():
        return Order.objects.create_pending(
            purchaser,
            billing_details,
            rate,
            days_for_self,
            email_addrs_and_days_for_others,
        )


def update_pending_order(order, billing_details, rate, days_for_self=None, email_addrs_and_days_for_others=None):
    logger.info('update_pending_order', order=order.order_id, rate=rate)
    with transaction.atomic():
        order.update(billing_details, rate, days_for_self, email_addrs_and_days_for_others)


def send_ticket_invitations(order):
    logger.info('send_ticket_invitations', order=order.order_id)
    for ticket in order.unclaimed_tickets():
        send_invitation_mail(ticket)


def claim_ticket_invitation(owner, invitation):
    logger.info('claim_ticket_invitation', owner=owner.id, invitation=invitation.token)
    with transaction.atomic():
        invitation.claim_for_owner(owner)

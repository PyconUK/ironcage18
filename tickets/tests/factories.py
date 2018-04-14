from accounts.tests.factories import create_user

from tickets import actions
from orders import actions as order_actions


def create_pending_order_for_self(user=None, rate=None, num_days=None):
    user = user or create_user()
    rate = rate or 'individual'
    num_days = num_days or 3
    billing_details = {
        'name': 'Sirius Cybernetics Corp.',
        'addr': 'Eadrax, Sirius Tau',
    }

    return actions.create_pending_order(
        purchaser=user,
        billing_details=billing_details,
        rate=rate,
        days_for_self=['thu', 'fri', 'sat', 'sun', 'mon'][:num_days],
    )


def create_pending_order_for_others(user=None, rate=None):
    user = user or create_user()
    rate = rate or 'individual'
    billing_details = {
        'name': 'Sirius Cybernetics Corp.',
        'addr': 'Eadrax, Sirius Tau',
    }

    return actions.create_pending_order(
        purchaser=user,
        billing_details=billing_details,
        rate=rate,
        email_addrs_and_days_for_others=[
            ('bob@example.com', ['sun', 'mon']),
            ('carol@example.com', ['mon', 'tue']),
        ]
    )


def create_pending_order_for_self_and_others(user=None, rate=None):
    user = user or create_user()
    rate = rate or 'individual'
    billing_details = {
        'name': 'Sirius Cybernetics Corp.',
        'addr': 'Eadrax, Sirius Tau',
    }

    return actions.create_pending_order(
        purchaser=user,
        billing_details=billing_details,
        rate=rate,
        days_for_self=['sat', 'sun', 'mon'],
        email_addrs_and_days_for_others=[
            ('bob@example.com', ['sun', 'mon']),
            ('carol@example.com', ['mon', 'tue']),
        ]
    )


def confirm_order(order):
    order_actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1526887563)


def mark_order_as_failed(order):
    order_actions.mark_order_as_failed(order, 'Your card was declined.')


def mark_order_as_errored_after_charge(order):
    order_actions.mark_order_as_errored_after_charge(order, 'ch_abcdefghijklmnopqurstuvw')


def create_confirmed_order_for_self(user=None, rate=None, num_days=None):
    order = create_pending_order_for_self(user, rate, num_days)
    confirm_order(order)
    return order


def create_confirmed_order_for_others(user=None, rate=None):
    order = create_pending_order_for_others(user, rate)
    confirm_order(order)
    return order


def create_confirmed_order_for_self_and_others(user=None, rate=None):
    order = create_pending_order_for_self_and_others(user, rate)
    confirm_order(order)
    return order


def create_failed_order(user=None, rate=None):
    order = create_pending_order_for_self(user, rate)
    mark_order_as_failed(order)
    return order


def create_errored_order(user=None, rate=None):
    order = create_pending_order_for_self(user, rate)
    mark_order_as_errored_after_charge(order)
    return order


def create_ticket(user=None, rate=None, num_days=None):
    order = create_confirmed_order_for_self(user, rate, num_days)
    return order.all_tickets()[0]


def create_ticket_with_unclaimed_invitation():
    order = create_confirmed_order_for_others()
    return order.all_tickets()[0]


def create_ticket_with_claimed_invitation(owner=None):
    order = create_confirmed_order_for_others()
    ticket = order.all_tickets()[0]
    owner = owner or create_user()
    actions.claim_ticket_invitation(owner, ticket.invitation())
    return ticket

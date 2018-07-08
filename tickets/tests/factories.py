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
        days_for_self=['sat', 'sun', 'mon', 'tue', 'wed'][:num_days],
    )


def create_pending_order_for_educator_self(user=None, rate=None, num_days=None):
    user = user or create_user()
    rate = rate or 'educator-self'
    num_days = num_days or 2
    billing_details = {
        'name': 'University of Maximegalon',
        'addr': 'Dept. of Neomathematics',
    }

    return actions.create_pending_order(
        purchaser=user,
        billing_details=billing_details,
        rate=rate,
        days_for_self=['sat', 'sun'][:num_days],
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
            ('bob@example.com', 'Bob', ['sun', 'mon']),
            ('carol@example.com', 'Carol', ['mon', 'tue']),
        ]
    )


def create_pending_order_for_educator_others(user=None, rate=None):
    user = user or create_user()
    rate = rate or 'educator-self'
    billing_details = {
        'name': 'University of Maximegalon',
        'addr': 'Dept. of Neomathematics',
    }

    return actions.create_pending_order(
        purchaser=user,
        billing_details=billing_details,
        rate=rate,
        email_addrs_and_days_for_others=[
            ('bob@example.com', 'Bob', ['sat', 'sun']),
            ('carol@example.com', 'Carol', ['sat', 'sun']),
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
            ('bob@example.com', 'Bob', ['sun', 'mon']),
            ('carol@example.com', 'Carol', ['mon', 'tue']),
        ]
    )


def create_pending_order_for_educator_self_and_others(user=None, rate=None):
    user = user or create_user()
    rate = rate or 'educator-self'
    billing_details = {
        'name': 'University of Maximegalon',
        'addr': 'Dept. of Neomathematics',
    }

    return actions.create_pending_order(
        purchaser=user,
        billing_details=billing_details,
        rate=rate,
        days_for_self=['sat', 'sun'],
        email_addrs_and_days_for_others=[
            ('bob@example.com', 'Bob', ['sat', 'sun']),
            ('carol@example.com', 'Carol', ['sat', 'sun']),
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


def create_free_ticket(email_addr=None, free_reason='Financial assistance'):
    if email_addr is None:
        email_addr = create_user().email_addr
    return actions.create_free_ticket(email_addr, free_reason)


def create_claimed_free_ticket(user, free_reason='Financial assistance'):
    ticket = create_free_ticket(user.email_addr, free_reason)
    actions.claim_ticket_invitation(user, ticket.invitation())
    return ticket


def create_completed_free_ticket(user, free_reason='Financial assistance'):
    ticket = create_claimed_free_ticket(user, free_reason)
    actions.update_free_ticket(ticket, ['sat', 'sun', 'mon'])
    return ticket

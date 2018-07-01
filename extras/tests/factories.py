from accounts.tests.factories import create_user

from extras import actions
from orders import actions as order_actions


def create_pending_children_ticket_order(user=None):
    user = user or create_user()

    billing_details = {
        'name': 'Sirius Cybernetics Corp.',
        'addr': 'Eadrax, Sirius Tau',
    }

    return actions.create_pending_children_ticket_order(
        purchaser=user,
        billing_details=billing_details,
        unconfirmed_details={
            'adult_name': 'Puff The Elder',
            'adult_email_addr': 'puff@example.com',
            'adult_phone_number': '07700 900001',
            'name': 'Puff',
            'age': 10,
            'accessibility_reqs': 'Occasionally breathe fire',
            'dietary_reqs': 'Allergic to Welsh Cakes',
        }
    )



def confirm_order(order):
    order_actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1526887563)


# def mark_order_as_failed(order):
#     order_actions.mark_order_as_failed(order, 'Your card was declined.')


# def mark_order_as_errored_after_charge(order):
#     order_actions.mark_order_as_errored_after_charge(order, 'ch_abcdefghijklmnopqurstuvw')


def create_confirmed_children_ticket_order(user=None):
    order = create_pending_children_ticket_order(user)
    confirm_order(order)
    return order


# def create_failed_order(user=None, rate=None):
#     order = create_pending_order_for_self(user, rate)
#     mark_order_as_failed(order)
#     return order


# def create_errored_order(user=None, rate=None):
#     order = create_pending_order_for_self(user, rate)
#     mark_order_as_errored_after_charge(order)
#     return order


def create_children_ticket(user=None):
    order = create_confirmed_children_ticket_order(user)
    return order.all_items()[0]


# def create_ticket_with_unclaimed_invitation():
#     order = create_confirmed_order_for_others()
#     return order.all_items()[0]


# def create_ticket_with_claimed_invitation(owner=None):
#     order = create_confirmed_order_for_others()
#     ticket = order.all_items()[0]
#     owner = owner or create_user()
#     actions.claim_ticket_invitation(owner, ticket.invitation())
#     return ticket

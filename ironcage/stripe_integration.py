import stripe

from django.conf import settings


def set_stripe_api_key():
    stripe.api_key = settings.STRIPE_API_KEY_SECRET


def create_charge(amount_pence, description, statement_descriptor, token):
    assert len(statement_descriptor) <= 22
    set_stripe_api_key()
    return stripe.Charge.create(
        amount=amount_pence,
        currency='gbp',
        description=description,
        statement_descriptor=statement_descriptor,
        source=token,
    )


def create_charge_for_order(order, token):
    assert order.payment_required()
    return create_charge(
        order.cost_pence_incl_vat,
        f'PyCon UK order {order.order_id}',
        f'PyCon UK {order.order_id}',
        token,
    )


def refund_charge(charge_id, amount_pence=None):
    set_stripe_api_key()
    if amount_pence is not None:
        return stripe.Refund.create(charge=charge_id, amount=amount_pence)
    else:
        return stripe.Refund.create(charge=charge_id)


def refund_item(item):
    order_row = item.order_row
    charge_id = order_row.order.stripe_charge_id
    return refund_charge(charge_id, order_row.cost_pence_incl_vat)

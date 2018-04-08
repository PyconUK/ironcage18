from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from tickets import actions
from .models import Order, Refund


@login_required
def order(request, order_id):
    order = Order.objects.get_by_order_id_or_404(order_id)

    if request.user != order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can view the order')
        return redirect('index')

    if order.payment_required():
        if request.user.get_ticket() is not None and order.unconfirmed_details['days_for_self']:
            messages.warning(request, 'You already have a ticket.  Please amend your order.')
            return redirect('tickets:order_edit', order.order_id)

    if order.status == 'failed':
        messages.error(request, f'Payment for this order failed ({order.stripe_charge_failure_reason})')
    elif order.status == 'errored':
        messages.error(request, 'There was an error creating your order.  You card may have been charged, but if so the charge will have been refunded.  Please make a new order.')

    ticket = request.user.get_ticket()
    if ticket is not None and ticket.order != order:
        ticket = None

    context = {
        'order': order,
        'ticket': ticket,
        'stripe_api_key': settings.STRIPE_API_KEY_PUBLISHABLE,
    }
    return render(request, 'orders/order.html', context)


@login_required
@require_POST
def order_payment(request, order_id):
    order = Order.objects.get_by_order_id_or_404(order_id)

    if request.user != order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can pay for the order')
        return redirect('index')

    if not order.payment_required():
        messages.error(request, 'This order has already been paid')
        return redirect(order)

    if request.user.get_ticket() is not None and order.unconfirmed_details['days_for_self']:
        messages.warning(request, 'You already have a ticket.  Please amend your order.  Your card has not been charged.')
        return redirect('tickets:order_edit', order.order_id)

    token = request.POST['stripeToken']
    actions.process_stripe_charge(order, token)

    if not order.payment_required():
        messages.success(request, 'Payment for this order has been received.')

    return redirect(order)


@login_required
def order_receipt(request, order_id):
    order = Order.objects.get_by_order_id_or_404(order_id)

    if request.user != order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can view the receipt')
        return redirect('index')

    if order.payment_required():
        messages.error(request, 'This order has not been paid')
        return redirect(order)

    context = {
        'order': order,
        'title': f'PyCon UK 2018 receipt for order {order.order_id}',
        'no_navbar': True,
    }
    return render(request, 'orders/order_receipt.html', context)


@login_required
def refund_credit_note(request, order_id, refund_id):
    refund = Refund.objects.get_by_refund_id_or_404(refund_id)
    order = refund.order

    if order.order_id != order_id:
        raise Http404

    if request.user != order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can view a credit note')
        return redirect('index')

    context = {
        'order': order,
        'refund': refund,
        'title': f'PyCon UK 2018 credit note {refund.refund_id} for order {order.order_id}',
        'no_navbar': True,
    }
    return render(request, 'orders/refund_credit_note.html', context)

from datetime import datetime, timezone

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import mark_safe

from . import actions
from .forms import ChildrenTicketForm
from .models import ExtraItem
from tickets.forms import BillingDetailsForm
from orders.models import Order


def new_children_order(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        form = ChildrenTicketForm(request.POST)
        billing_details_form = BillingDetailsForm(request.POST)

        if form.is_valid():

            valid = billing_details_form.is_valid()
            if valid:
                billing_details = {
                    'name': billing_details_form.cleaned_data['billing_name'],
                    'addr': billing_details_form.cleaned_data['billing_addr'],
                }

            if valid:

                unconfirmed_details = {
                    'adult_name': form.cleaned_data['adult_name'],
                    'adult_email_addr': form.cleaned_data['adult_email_addr'],
                    'adult_phone_number': form.cleaned_data['adult_phone_number'],
                    'name': form.cleaned_data['name'],
                    'age': form.cleaned_data['age'],
                    'accessibility_reqs': form.cleaned_data['accessibility_reqs'],
                    'dietary_reqs': form.cleaned_data['dietary_reqs'],
                }

                order = actions.create_pending_children_ticket_order(
                    purchaser=request.user,
                    billing_details=billing_details,
                    unconfirmed_details=unconfirmed_details
                )

                return redirect(order)

    else:
        if datetime.now(timezone.utc) > settings.TICKET_SALES_CLOSE_AT:
            if request.GET.get('deadline-bypass-token', '') != settings.TICKET_DEADLINE_BYPASS_TOKEN:
                messages.warning(request, "We're sorry, ticket sales have closed")
                return redirect('index')

        form = ChildrenTicketForm()
        billing_details_form = BillingDetailsForm()

    context = {
        'form': form,
        'billing_details_form': billing_details_form,
    }

    return render(request, 'extras/children/new_order.html', context)


def children_order_edit(request, order_id):
    order = Order.objects.get_by_order_id_or_404(order_id)

    if request.user != order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can update the order')
        return redirect('index')

    if not order.payment_required():
        messages.error(request, 'This order has already been paid')
        return redirect(order)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        form = ChildrenTicketForm(request.POST)
        billing_details_form = BillingDetailsForm(request.POST)

        if form.is_valid():

            valid = billing_details_form.is_valid()
            if valid:
                billing_details = {
                    'name': billing_details_form.cleaned_data['billing_name'],
                    'addr': billing_details_form.cleaned_data['billing_addr'],
                }

            if valid:

                unconfirmed_details = {
                    'adult_name': form.cleaned_data['adult_name'],
                    'adult_email_addr': form.cleaned_data['adult_email_addr'],
                    'adult_phone_number': form.cleaned_data['adult_phone_number'],
                    'name': form.cleaned_data['name'],
                    'age': form.cleaned_data['age'],
                    'accessibility_reqs': form.cleaned_data['accessibility_reqs'],
                    'dietary_reqs': form.cleaned_data['dietary_reqs'],
                }

                actions.update_pending_children_ticket_order(
                    order=order,
                    billing_details=billing_details,
                    unconfirmed_details=unconfirmed_details
                )

                return redirect(order)

    else:
        form = ChildrenTicketForm.from_pending_order(order)
        billing_details_form = BillingDetailsForm({
            'billing_name': order.billing_name,
            'billing_addr': order.billing_addr,
        })

    context = {
        'form': form,
        'billing_details_form': billing_details_form,
    }

    return render(request, 'extras/children/order_edit.html', context)


@login_required
def children_ticket(request):
    children_ticket_content_type = ContentType.objects.get(app_label="extras", model="childrenticket")
    tickets = ExtraItem.objects.filter(
        owner=request.user,
        content_type=children_ticket_content_type
    ).all()

    if not len(tickets):
        messages.error(request, 'You do not have any Children\'s Day tickets')
        return redirect('index')

    if not request.user.profile_complete():
        messages.warning(
            request,
            mark_safe('Your profile is incomplete. <a href="{}">Update your profile</a>'.format(reverse('accounts:edit_profile')))
        )

    context = {
        'tickets': tickets,
    }
    return render(request, 'extras/children/ticket.html', context)

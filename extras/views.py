from datetime import datetime, timezone

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import mark_safe

from orders.models import Order
from tickets.forms import BillingDetailsForm

from . import actions
from .forms import (ChildrenTicketForm, CityHallDinnerTicketForm,
                    ClinkDinnerTicketForm, DinnerTicketForm)
from .models import DINNER_LOCATIONS, ExtraItem, DINNERS


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


@login_required
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
        messages.error(request, "You do not have any Young Coders' Day tickets")
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


def new_dinner_order(request, location_id):

    ticket_cost = int(DINNER_LOCATIONS[location_id]['price'] * 1.2)

    if request.method == 'POST':
        if location_id == 'CL':
            form = ClinkDinnerTicketForm(request.POST)
        else:
            form = CityHallDinnerTicketForm(request.POST)
        billing_details_form = BillingDetailsForm(request.POST)

        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        if form.is_valid():

            valid = billing_details_form.is_valid()
            if valid:
                billing_details = {
                    'name': billing_details_form.cleaned_data['billing_name'],
                    'addr': billing_details_form.cleaned_data['billing_addr'],
                }

            if valid:

                unconfirmed_details = {
                    'dinner': form.cleaned_data['dinner'],
                    'starter': form.cleaned_data['starter'],
                    'main': form.cleaned_data['main'],
                    'dessert': form.cleaned_data['dessert'],
                }

                order = actions.create_pending_dinner_ticket_order(
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

        if location_id == 'CL':
            form = ClinkDinnerTicketForm()
        else:
            form = CityHallDinnerTicketForm()
        billing_details_form = BillingDetailsForm()

    context = {
        'form': form,
        'billing_details_form': billing_details_form,
        'ticket_cost': ticket_cost
    }

    return render(request, 'extras/dinner/new_order.html', context)


@login_required
def dinner_order_edit(request, order_id):
    order = Order.objects.get_by_order_id_or_404(order_id)

    if request.user != order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can update the order')
        return redirect('index')

    if not order.payment_required():
        messages.error(request, 'This order has already been paid')
        return redirect(order)

    if request.method == 'POST':
        location_id = DINNERS[request.POST['dinner']]['location']
        ticket_cost = int(DINNER_LOCATIONS[location_id]['price'] * 1.2)

        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        if location_id == 'CL':
            form = ClinkDinnerTicketForm(request.POST)
        else:
            form = CityHallDinnerTicketForm(request.POST)
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
                    'dinner': form.cleaned_data['dinner'],
                    'starter': form.cleaned_data['starter'],
                    'main': form.cleaned_data['main'],
                    'dessert': form.cleaned_data['dessert'],
                }

                actions.update_pending_dinner_ticket_order(
                    order=order,
                    billing_details=billing_details,
                    unconfirmed_details=unconfirmed_details
                )

                return redirect(order)

    else:
        form = DinnerTicketForm.from_pending_order(order)
        location_id = DINNERS[order.unconfirmed_details['dinner']]['location']
        ticket_cost = int(DINNER_LOCATIONS[location_id]['price'] * 1.2)
        billing_details_form = BillingDetailsForm({
            'billing_name': order.billing_name,
            'billing_addr': order.billing_addr,
        })

    context = {
        'form': form,
        'billing_details_form': billing_details_form,
        'ticket_cost': ticket_cost
    }

    return render(request, 'extras/dinner/order_edit.html', context)


@login_required
def dinner_ticket_edit(request, item_id):
    item = ExtraItem.objects.get_by_item_id_or_404(item_id)

    if request.user != item.order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can update the order')
        return redirect('index')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        if DINNERS[request.POST['dinner']]['location'] != DINNERS[item.item.dinner]['location']:
            messages.error(request, "You cannot change location on your dinner ticket")
        else:
            if DINNERS[request.POST['dinner']]['location'] == 'CL':
                form = ClinkDinnerTicketForm(request.POST)
            else:
                form = CityHallDinnerTicketForm(request.POST)

            if form.is_valid():
                details = {
                    'dinner': form.cleaned_data['dinner'],
                    'starter': form.cleaned_data['starter'],
                    'main': form.cleaned_data['main'],
                    'dessert': form.cleaned_data['dessert'],
                }

                actions.update_existing_dinner_ticket_order(
                    item=item.item,
                    details=details,
                )

                messages.success(request, "Your dinner ticket has been updated.")
            else:
                messages.error(request, "There was an error updating your dinner ticket.")

        return redirect('extras:dinner_ticket')

    else:
        form = DinnerTicketForm.from_item(item)

    context = {
        'form': form,
    }

    return render(request, 'extras/dinner/ticket_edit.html', context)


@login_required
def dinner_ticket(request):
    dinner_ticket_content_type = ContentType.objects.get(app_label="extras", model="dinnerticket")
    tickets = ExtraItem.objects.filter(
        owner=request.user,
        content_type=dinner_ticket_content_type
    ).all()

    if not len(tickets):
        messages.error(request, "You do not have any dinner tickets")
        return redirect('index')

    if not request.user.profile_complete():
        messages.warning(
            request,
            mark_safe('Your profile is incomplete. <a href="{}">Update your profile</a>'.format(reverse('accounts:edit_profile')))
        )

    context = {
        'tickets': tickets,
    }
    return render(request, 'extras/dinner/ticket.html', context)

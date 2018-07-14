from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import mark_safe

from . import actions
from .constants import DAYS
from .forms import (
    BillingDetailsForm, TicketForm, TicketForSelfForm,
    TicketForOthersFormSet, EducatorTicketForm, TicketForSelfEducatorForm,
    TicketForOthersEducatorFormSet, FreeTicketForm, FreeTicketUpdateForm
)
from .models import Ticket, TicketInvitation
from .prices import PRICES_INCL_VAT, cost_incl_vat
from orders.models import Order


def new_order(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        form = TicketForm(request.POST)
        self_form = TicketForSelfForm(request.POST)
        others_formset = TicketForOthersFormSet(request.POST)
        billing_details_form = BillingDetailsForm(request.POST)

        if form.is_valid():
            who = form.cleaned_data['who']
            rate = form.cleaned_data['rate']

            if who == 'self':
                valid = self_form.is_valid()
                if valid:
                    days_for_self = self_form.cleaned_data['days']
                    email_addrs_and_days_for_others = None
            elif who == 'others':
                valid = others_formset.is_valid()
                if valid:
                    days_for_self = None
                    email_addrs_and_days_for_others = others_formset.email_addrs_and_days
            elif who == 'self and others':
                valid = self_form.is_valid() and others_formset.is_valid()
                if valid:
                    days_for_self = self_form.cleaned_data['days']
                    email_addrs_and_days_for_others = others_formset.email_addrs_and_days
            else:  # pragma: no cover
                assert False

            if valid:
                valid = billing_details_form.is_valid()
                if valid:
                    billing_details = {
                        'name': billing_details_form.cleaned_data['billing_name'],
                        'addr': billing_details_form.cleaned_data['billing_addr'],
                    }

            if valid:
                order = actions.create_pending_order(
                    purchaser=request.user,
                    billing_details=billing_details,
                    rate=rate,
                    days_for_self=days_for_self,
                    email_addrs_and_days_for_others=email_addrs_and_days_for_others,
                )

                return redirect(order)

    else:
        if datetime.now(timezone.utc) > settings.TICKET_SALES_CLOSE_AT:
            if request.GET.get('deadline-bypass-token', '') != settings.TICKET_DEADLINE_BYPASS_TOKEN:
                messages.warning(request, "We're sorry, ticket sales have closed")
                return redirect('index')

        form = TicketForm()
        self_form = TicketForSelfForm()
        others_formset = TicketForOthersFormSet()
        billing_details_form = BillingDetailsForm()

    context = {
        'form': form,
        'self_form': self_form,
        'others_formset': others_formset,
        'billing_details_form': billing_details_form,
        'user_can_buy_for_self': request.user.is_authenticated and not request.user.get_ticket(),
        'rates_table_data': _rates_table_data(),
        'rates_data': _rates_data(),
        'js_paths': ['tickets/order_form.js'],
    }

    return render(request, 'tickets/new_order.html', context)


def new_educator_order(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        form = EducatorTicketForm(request.POST)
        self_form = TicketForSelfEducatorForm(request.POST)
        others_formset = TicketForOthersEducatorFormSet(request.POST)
        billing_details_form = BillingDetailsForm(request.POST)

        if form.is_valid():
            who = form.cleaned_data['who']
            rate = form.cleaned_data['rate']

            if who == 'self':
                valid = self_form.is_valid()
                if valid:
                    days_for_self = self_form.cleaned_data['days']
                    email_addrs_and_days_for_others = None
            elif who == 'others':
                valid = others_formset.is_valid()
                if valid:
                    days_for_self = None
                    email_addrs_and_days_for_others = others_formset.email_addrs_and_days
            elif who == 'self and others':
                valid = self_form.is_valid() and others_formset.is_valid()
                if valid:
                    days_for_self = self_form.cleaned_data['days']
                    email_addrs_and_days_for_others = others_formset.email_addrs_and_days
            else:  # pragma: no cover
                assert False

            if valid:
                valid = billing_details_form.is_valid()
                if valid:
                    billing_details = {
                        'name': billing_details_form.cleaned_data['billing_name'],
                        'addr': billing_details_form.cleaned_data['billing_addr'],
                    }

            if valid:
                order = actions.create_pending_order(
                    purchaser=request.user,
                    billing_details=billing_details,
                    rate=rate,
                    days_for_self=days_for_self,
                    email_addrs_and_days_for_others=email_addrs_and_days_for_others,
                )

                return redirect(order)

    else:
        if datetime.now(timezone.utc) > settings.TICKET_SALES_CLOSE_AT:
            if request.GET.get('deadline-bypass-token', '') != settings.TICKET_DEADLINE_BYPASS_TOKEN:
                messages.warning(request, "We're sorry, ticket sales have closed")
                return redirect('index')

        form = EducatorTicketForm()
        self_form = TicketForSelfEducatorForm()
        others_formset = TicketForOthersEducatorFormSet()
        billing_details_form = BillingDetailsForm()

    context = {
        'form': form,
        'self_form': self_form,
        'others_formset': others_formset,
        'billing_details_form': billing_details_form,
        'user_can_buy_for_self': request.user.is_authenticated and not request.user.get_ticket(),
        'rates_table_data': _educator_rates_table_data(),
        'rates_data': _rates_data(),
        'js_paths': ['tickets/order_form.js'],
    }

    return render(request, 'tickets/new_educator_order.html', context)


@login_required
def order_edit(request, order_id):
    order = Order.objects.get_by_order_id_or_404(order_id)

    if request.user != order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can update the order')
        return redirect('index')

    if not order.payment_required():
        messages.error(request, 'This order has already been paid')
        return redirect(order)

    if request.method == 'POST':
        educator_order = request.POST['rate'] in ('educator-employer', 'educator-self')

        if educator_order:
            form = EducatorTicketForm(request.POST)
            self_form = TicketForSelfEducatorForm(request.POST)
            others_formset = TicketForOthersEducatorFormSet(request.POST)
        else:
            form = TicketForm(request.POST)
            self_form = TicketForSelfForm(request.POST)
            others_formset = TicketForOthersFormSet(request.POST)
        billing_details_form = BillingDetailsForm(request.POST)

        if form.is_valid():
            who = form.cleaned_data['who']
            rate = form.cleaned_data['rate']

            if who == 'self':
                valid = self_form.is_valid()
                if valid:
                    days_for_self = self_form.cleaned_data['days']
                    email_addrs_and_days_for_others = None
            elif who == 'others':
                valid = others_formset.is_valid()
                if valid:
                    days_for_self = None
                    email_addrs_and_days_for_others = others_formset.email_addrs_and_days
            elif who == 'self and others':
                valid = self_form.is_valid() and others_formset.is_valid()
                if valid:
                    days_for_self = self_form.cleaned_data['days']
                    email_addrs_and_days_for_others = others_formset.email_addrs_and_days
            else:  # pragma: no cover
                assert False

            if valid:
                valid = billing_details_form.is_valid()
                if valid:
                    billing_details = {
                        'name': billing_details_form.cleaned_data['billing_name'],
                        'addr': billing_details_form.cleaned_data['billing_addr'],
                    }

            if valid:
                actions.update_pending_order(
                    order,
                    billing_details=billing_details,
                    rate=rate,
                    days_for_self=days_for_self,
                    email_addrs_and_days_for_others=email_addrs_and_days_for_others,
                )

                return redirect(order)

    else:
        educator_order = order.unconfirmed_details['rate'] in ('educator-employer', 'educator-self')

        if educator_order:
            form = EducatorTicketForm.from_pending_order(order)
            self_form = TicketForSelfEducatorForm.from_pending_order(order)
            others_formset = TicketForOthersEducatorFormSet.from_pending_order(order)
        else:
            form = TicketForm.from_pending_order(order)
            self_form = TicketForSelfForm.from_pending_order(order)
            others_formset = TicketForOthersFormSet.from_pending_order(order)

        billing_details_form = BillingDetailsForm({
            'billing_name': order.billing_name,
            'billing_addr': order.billing_addr,
        })

    context = {
        'form': form,
        'self_form': self_form,
        'others_formset': others_formset,
        'billing_details_form': billing_details_form,
        'user_can_buy_for_self': not request.user.get_ticket(),
        'rates_table_data': _educator_rates_table_data() if educator_order else _rates_table_data(),
        'rates_data': _rates_data(),
        'js_paths': ['tickets/order_form.js'],
        'educator_order': educator_order,
    }

    return render(request, 'tickets/order_edit.html', context)


@login_required
def ticket(request, ticket_id):
    ticket = Ticket.objects.get_by_ticket_id_or_404(ticket_id)

    if request.user != ticket.owner:
        messages.warning(request, 'Only the owner of a ticket can view the ticket')
        return redirect('index')

    if not request.user.profile_complete():
        messages.warning(
            request,
            mark_safe('Your profile is incomplete. <a href="{}">Update your profile</a>'.format(reverse('accounts:edit_profile')))
        )

    context = {
        'ticket': ticket,
    }

    if request.method == 'POST':
        if datetime.now(timezone.utc) > settings.TICKET_SALES_CLOSE_AT:
            if request.GET.get('deadline-bypass-token', '') != settings.TICKET_DEADLINE_BYPASS_TOKEN:
                messages.warning(request, "We're sorry, ticket changes are no longer available.")
        else:
            form = FreeTicketUpdateForm(request.POST)

            if form.is_valid() and ticket.is_changeable:
                actions.update_free_ticket(ticket, form.cleaned_data['days'])
                messages.success(request, f'Your ticket has been updated.')

    if ticket.is_free_ticket and ticket.is_changeable:
        form = FreeTicketUpdateForm(
            {'days': [day for day in DAYS if getattr(ticket, day)]}
        )

        context['form'] = form

    return render(request, 'tickets/ticket.html', context)


def ticket_invitation(request, token):
    invitation = get_object_or_404(TicketInvitation, token=token)

    if not request.user.is_authenticated:
        messages.info(request, 'You need to create an account to claim your invitation')
        return redirect(reverse('register') + f'?next={invitation.get_absolute_url()}')

    if request.user.get_ticket() is not None:
        messages.error(request, 'You already have a ticket!  Please contact pyconuk-enquiries@python.org to arrange transfer of this invitaiton to somebody else.')
        return redirect('index')

    ticket = invitation.ticket

    if invitation.status == 'unclaimed':
        assert ticket.owner is None
        actions.claim_ticket_invitation(request.user, invitation)
    elif invitation.status == 'claimed':
        assert ticket.owner is not None
        messages.info(request, 'This invitation has already been claimed')
    else:  # pragma: no cover
        assert False

    return redirect(ticket)


@permission_required('tickets.create_free_ticket', raise_exception=True)
def new_free_ticket(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        form = FreeTicketForm(request.POST)

        if form.is_valid():

            email_addr = form.cleaned_data['email_addr']
            reason = form.cleaned_data['reason']
            days = form.cleaned_data['days']

            order = actions.create_free_ticket(
                email_addr=email_addr,
                free_reason=reason,
                days=days
            )

            messages.success(request, f'Ticket generated for {email_addr}')

            return redirect('tickets:new_free_ticket')

    else:
        form = FreeTicketForm()

    context = {
        'form': form,
    }

    return render(request, 'tickets/new_free_ticket.html', context)


def _rates_data():
    return PRICES_INCL_VAT


def _rates_table_data():
    data = []
    data.append(['', 'Individual rate', 'Corporate rate', "Unwaged rate"])
    for ix in range(5):
        num_days = ix + 1
        individual_rate = cost_incl_vat('individual', num_days)
        corporate_rate = cost_incl_vat('corporate', num_days)
        unwaged_rate = cost_incl_vat('unwaged', num_days)
        row = []
        if num_days == 1:
            row.append('1 day')
        else:
            row.append(f'{num_days} days')
        row.extend([f'£{individual_rate}', f'£{corporate_rate}', f'£{unwaged_rate}'])
        data.append(row)

    return data


def _educator_rates_table_data():
    data = []
    data.append(['', 'Employer funded', 'Self funded'])
    for ix in range(2):
        num_days = ix + 1
        employer_rate = cost_incl_vat('educator-employer', num_days)
        self_rate = cost_incl_vat('educator-self', num_days)
        row = []
        if num_days == 1:
            row.append('1 day')
        else:
            row.append(f'{num_days} days')
        row.extend([f'£{employer_rate}', f'£{self_rate}'])
        data.append(row)

    return data

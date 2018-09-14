from datetime import datetime, timezone, timedelta, date

import pyqrcode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import mark_safe

from orders.models import Order
from accounts.models import Badge
from . import actions
from .constants import DAYS
from .forms import (BillingDetailsForm, EducatorTicketForm, FreeTicketForm,
                    FreeTicketUpdateForm, TicketForm,
                    TicketForOthersEducatorFormSet, TicketForOthersFormSet,
                    TicketForSelfEducatorForm, TicketForSelfForm)
from .models import Ticket, TicketInvitation
from .prices import PRICES_INCL_VAT, cost_incl_vat


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

    children_ticket_content_type = ContentType.objects.get(app_label="extras", model="childrenticket")
    dinner_ticket_content_type = ContentType.objects.get(app_label="extras", model="dinnerticket")

    if order.content_type == children_ticket_content_type:
        return redirect('extras:children_order_edit', order_id=order_id)
    elif order.content_type == dinner_ticket_content_type:
        return redirect('extras:dinner_order_edit', order_id=order_id)

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

    code = pyqrcode.create(ticket.ticket_id)
    png_base64 = code.png_as_base64_str(scale=5)

    context = {
        'ticket': ticket,
        'qr_code_base64': png_base64
    }

    if request.method == 'POST':
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
        messages.info(request, 'You need an account to claim your invitation')
        return redirect(reverse('login') + f'?next={invitation.get_absolute_url()}')

    if request.user.get_ticket() is not None:
        messages.error(request, 'You already have a ticket!  Please contact pyconuk@uk.python.org to arrange transfer of this invitaiton to somebody else.')
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

            actions.create_free_ticket(
                email_addr=email_addr,
                free_reason=reason,
                days=days
            )

            messages.success(request, f'Ticket generated for {email_addr}')

            return redirect('tickets:new_free_ticket')
        else:
            messages.error(request, f'There was an error with your request.')

    else:
        form = FreeTicketForm()

    context = {
        'form': form,
    }

    return render(request, 'tickets/new_free_ticket.html', context)


@permission_required('accounts.reg_desk_assistant', raise_exception=True)
def ticket_info(request, ticket_id):
    ticket = Ticket.objects.get_by_ticket_id_or_404(ticket_id)
    dates = {
        'Saturday': date(2018, 9, 15),
        'Sunday': date(2018, 9, 16),
        'Monday': date(2018, 9, 17),
        'Tuesday': date(2018, 9, 18),
        'Wednesday': date(2018, 9, 19),
    }

    if request.method == 'POST':
        response = {}

        badge_id = request.POST.get('badge_id')
        badge = Badge.objects.get_by_badge_id_or_404(badge_id)
        try:
            ticket_badge = ticket.badge.get()
        except Badge.DoesNotExist:
            ticket_badge = None

        if badge_id and badge and not badge.collected and badge.ticket and badge.ticket.ticket_id == ticket_id:
            # Ticket OK, Correct Badge Scanned
            badge.collected = datetime.now()
            badge.save()
        elif badge_id and badge and not badge.collected and badge.ticket and badge.ticket.ticket_id != ticket_id:
            # Ticket OK, Wrong Badge Scanned
            response = {
                'error': 'Badge is assigned to a different ticket! Check the top ID code for the correct ticket ID!',
                'scan_next': 'badge'
            }
        elif badge_id and badge and not badge.collected and ticket_badge is None and badge.ticket is None:
            # Ticket OK, badge never assigned as too late, need to assign one
            badge.ticket = ticket
            badge.collected = datetime.now()
            badge.save()
        elif badge_id and badge and not badge.collected and ticket_badge is not None and badge.ticket is None:
            # Ticket OK, Can’t find badge, need to assign one.
            if request.user.is_staff:
                badge.ticket = ticket
                badge.collected = datetime.now()
                badge.save()
            else:
                response = {
                    'error': 'Only committee members can assign a blank badge to a user with a printed one',
                    'scan_next': 'ticket'
                }
        else:
            print('bad')

    else:
        if ticket.owner is None:
            response = {
                'error': 'Ticket has no owner',
                'scan_next': 'ticket'
            }
        elif dates[ticket.days()[0]] > datetime.now().date():
            response = {
                'error': f'Ticket not yet valid - only valid for {ticket.days_sentence}',
                'scan_next': 'ticket'
            }
        elif dates[ticket.days()[-1]] < datetime.now().date():
            response = {
                'error': f'Ticket no longer valid - only valid for {ticket.days_sentence}',
                'scan_next': 'ticket'
            }
        else:
            try:
                badge = ticket.badge.get()
            except Badge.DoesNotExist:
                badge = None

            if badge and badge.collected:
                # Ticket has already collected badge - go away
                response = {
                    'error': f'Already collected: {ticket.owner.name} at {badge.collected.strftime("%Y-%m-%d %H:%M:%S")}',
                    'scan_next': 'ticket'
                }
            else:
                response = {
                    'id': ticket.ticket_id,
                    'name': badge.name if badge and badge.name else ticket.owner.name,
                    'company': ticket.owner.badge_company,
                    'badge': badge.badge_id if badge else None,
                    'is_contributor': ticket.owner.is_contributor,
                    'is_organiser': ticket.owner.is_organiser,
                    'snake': ticket.owner.badge_snake_colour,
                    'extras': ticket.owner.badge_snake_extras,
                    'accessibility': ticket.owner.accessibility_reqs,
                    'dietary': ticket.owner.dietary_reqs,
                    'childcare': ticket.owner.childcare_reqs,
                }

    return JsonResponse(response)


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

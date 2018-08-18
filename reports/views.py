from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.shortcuts import render

from accounts.models import User
from cfp.models import Proposal
from grants.models import Application
from orders.models import Order
from tickets.models import Ticket

from .reports import reports


@staff_member_required(login_url='login')
def index(request):
    return render(request, 'reports/index.html', {'reports': reports})


@staff_member_required(login_url='login')
def accounts_user(request, user_id):
    user = User.objects.get_by_user_id_or_404(user_id)
    context = {
        'user': user,
        'ticket': user.get_ticket(),
        'orders': user.orders.all(),
    }
    return render(request, 'reports/user.html', context)


@staff_member_required(login_url='login')
def tickets_order(request, order_id):
    order = Order.objects.get_by_order_id_or_404(order_id)
    context = {
        'order': order,
    }
    return render(request, 'reports/order.html', context)


@staff_member_required(login_url='login')
def tickets_ticket(request, ticket_id):
    ticket = Ticket.objects.get_by_ticket_id_or_404(ticket_id)
    context = {
        'ticket': ticket,
    }
    return render(request, 'reports/ticket.html', context)


@staff_member_required(login_url='login')
def finaid_report(request):

    fin_aid_accepted_replied = Application.objects.filter(
        replied_to__isnull=False, amount_awarded__gt=0
    ).aggregate(Sum('amount_awarded'))['amount_awarded__sum'] or 0

    fin_aid_awaiting = Application.objects.filter(
        replied_to__isnull=True, amount_awarded__gt=0
    ).aggregate(Sum('amount_awarded'))['amount_awarded__sum'] or 0

    context = {
        'awarded': fin_aid_accepted_replied,
        'awaiting': fin_aid_awaiting,
        'total': fin_aid_accepted_replied + fin_aid_awaiting,
    }
    return render(request, 'reports/finaid_report.html', context)


@staff_member_required(login_url='login')
def speakers_without_tickets(request):

    accepted_proposals = Proposal.objects.filter(
        state__in=['accept', 'confirm']
    ).all()

    without_tickets = []

    for proposal in accepted_proposals:
        if proposal.proposer.get_ticket() is None:
            without_tickets.append(proposal.proposer)

    context = {
        'without_tickets': set(without_tickets),
    }
    return render(request, 'reports/speakers_without_tickets.html', context)

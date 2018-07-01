from datetime import datetime, timezone

import structlog

from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import mark_safe

logger = structlog.get_logger()


def index(request):
    user = request.user

    if user.is_authenticated:
        ticket_content_type = ContentType.objects.get(app_label="tickets", model="ticket")
        children_ticket_content_type = ContentType.objects.get(app_label="extras", model="childrenticket")

        if user.get_ticket() is not None and not user.profile_complete():
            messages.warning(
                request,
                mark_safe('Your profile is incomplete. <a href="{}">Update your profile</a>'.format(reverse('accounts:edit_profile')))
            )
        context = {
            'ticket': user.get_ticket(),
            'orders': user.orders.filter(content_type=ticket_content_type).all(),
            'childrensday': user.orders.filter(content_type=children_ticket_content_type).all(),
            'proposals': user.proposals.all(),
            'cfp_open': datetime.now(timezone.utc) < settings.CFP_CLOSE_AT,
            'grant_application': user.get_grant_application(),
            'grant_applications_open': datetime.now(timezone.utc) < settings.GRANT_APPLICATIONS_CLOSE_AT,
            'ticket_sales_open': datetime.now(timezone.utc) < settings.TICKET_SALES_CLOSE_AT,
        }
    else:
        context = {
            'cfp_open': datetime.now(timezone.utc) < settings.CFP_CLOSE_AT,
            'grant_applications_open': datetime.now(timezone.utc) < settings.GRANT_APPLICATIONS_CLOSE_AT,
            'ticket_sales_open': datetime.now(timezone.utc) < settings.TICKET_SALES_CLOSE_AT,
        }

    return render(request, 'ironcage/index.html', context)


def error(request):
    1 / 0


def log(request):
    logger.info('Test log')
    return redirect('index')

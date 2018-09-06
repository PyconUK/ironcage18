import re
from datetime import datetime

from django.conf import settings
from django.core.management import BaseCommand
from django.template.loader import get_template

from ironcage.emails import send_mail
from tickets.models import TicketInvitation


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        unclaimed_invites = TicketInvitation.objects.filter(
            status='unclaimed'
        ).all()

        for invite in unclaimed_invites:
            template = get_template('tickets/emails/unclaimed.txt')
            context = {
                'invite': invite,
                'url': settings.DOMAIN + invite.get_absolute_url()
            }
            body_raw = template.render(context)
            body = re.sub('\n\n\n+', '\n\n', body_raw)

            send_mail(
                f'Your unclaimed PyCon UK 2018 Ticket ({invite.ticket.ticket_id})',
                body,
                invite.email_addr,
            )

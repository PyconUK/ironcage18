import re
import io

import pyqrcode
from django.core.management import BaseCommand
from django.template.loader import get_template

from accounts.models import User
from ironcage.emails import send_mail_with_attachment
from tickets.models import Ticket


class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('template', nargs=1, type=str)
        parser.add_argument('subject', nargs=1, type=str)

    def handle(self, template, subject, **kwargs):

        # All ticket holders
        ticket_holders = Ticket.objects.filter(
            owner__isnull=False
        ).all().values_list('owner', flat=True)

        all_emailees = set(list(ticket_holders))

        users_to_email = User.objects.filter(pk__in=all_emailees).all()

        template = get_template(f'emails/{template[0]}.txt')

        for user in users_to_email:
            context = {
                'user': user
            }
            body_raw = template.render(context)
            body = re.sub('\n\n\n+', '\n\n', body_raw)

            code = pyqrcode.create(user.ticket.ticket_id)
            buffer = io.BytesIO()
            code.png(buffer, scale=5)
            buffer.seek(0)

            send_mail_with_attachment(
                f'{subject[0]} ({user.user_id})',
                body,
                user.email_addr,
                [('ticket.png', buffer.read(), 'image/png')]
            )

import re

from django.conf import settings
from django.core.management import BaseCommand
from django.template.loader import get_template

from accounts.models import User
from ironcage.emails import send_mail
from tickets.models import Ticket


class Command(BaseCommand):

    def handle(self, **kwargs):

        # Contributors only
        contributors = Ticket.objects.filter(
            owner__isnull=False,
            owner__is_contributor=True
        ).all().values_list('owner', flat=True)

        all_emailees = set(list(contributors))

        users_to_email = User.objects.filter(pk__in=all_emailees).all()

        template = get_template('accounts/emails/lastminstuff.txt')

        for user in users_to_email:
            context = {
                'user': user,
                'slack_link': settings.SLACK_SIGNUP_LINK,
            }
            body_raw = template.render(context)
            body = re.sub('\n\n\n+', '\n\n', body_raw)

            send_mail(
                f'PyCon UK Speaker information ({user.user_id})',
                body,
                user.email_addr,
            )

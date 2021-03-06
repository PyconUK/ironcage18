import re

from django.core.management import BaseCommand
from django.db.models import Q
from django.template.loader import get_template

from accounts.models import User
from cfp.models import Proposal
from grants.models import Application
from ironcage.emails import send_mail
from orders.models import Order
from tickets.models import Ticket


class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('template', nargs=1, type=str)
        parser.add_argument('subject', nargs=1, type=str)

    def handle(self, template, subject, **kwargs):

        successful_applicants_who_came = Application.objects.filter(
            application_declined=False,
            amount_awarded__gt=0,
            applicant__ticket__badge__collected__isnull=False
        ).all().values_list('applicant', flat=True)

        all_emailees = set(list(successful_applicants_who_came))

        users_to_email = User.objects.filter(pk__in=all_emailees).all()

        template = get_template(f'emails/{template[0]}.txt')

        for user in users_to_email:
            context = {
                'user': user
            }
            body_raw = template.render(context)
            body = re.sub('\n\n\n+', '\n\n', body_raw)

            send_mail(
                f'{subject[0]} ({user.user_id})',
                body,
                user.email_addr,
            )

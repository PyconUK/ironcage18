import re

from django.core.management import BaseCommand
from django.template.loader import get_template
from django.db.models import Q

from accounts.models import Application
from ironcage.emails import send_mail
from tickets.actions import create_free_ticket


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        accepted_applications = Application.objects.filter(
            application_declined=False,
        ).filter(
            Q(ticket_awarded=True) | Q(amount_awarded__isnull=False)
        ).all()

        for application in accepted_applications:
            if application.ticket_awarded:
                create_free_ticket(
                    email_addr=application.applicant.email_addr,
                    free_reason='Financial Assistance',
                    days=application.days()
                )

            if application.amount_awarded:
                template = get_template('grants/emails/how-to-get-grant.txt')
                context = {
                    'application': application,
                }
                body_raw = template.render(context)
                body = re.sub('\n\n\n+', '\n\n', body_raw)

                send_mail(
                    f'Your PyCon UK 2018 Financial Assistance ({application.application_id})',
                    body,
                    application.applicant.email_addr,
                )

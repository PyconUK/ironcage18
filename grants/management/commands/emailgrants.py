import re
from datetime import datetime

from django.conf import settings
from django.core.management import BaseCommand
from django.template.loader import get_template
from django.urls import reverse
from django.db.models import Q

from accounts.models import Application
from ironcage.emails import send_mail


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        ready_to_send_applications = Application.objects.filter(
            replied_to__isnull=True,
        ).filter(
            Q(application_declined=True) | Q(ticket_awarded=True) | Q(amount_awarded__isnull=False)
        ).all()

        for application in ready_to_send_applications:
            template = get_template('grants/emails/email.txt')
            context = {
                'application': application,
            }
            body_raw = template.render(context)
            body = re.sub('\n\n\n+', '\n\n', body_raw)

            send_mail(
                f'Your PyCon UK 2018 Financial Assistance',
                body,
                application.applicant.email_addr,
            )

            application.replied_to = datetime.now()
            application.save()

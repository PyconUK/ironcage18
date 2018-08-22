import re
from datetime import datetime

from django.conf import settings
from django.core.management import BaseCommand
from django.template.loader import get_template
from django.urls import reverse

from cfp.models import Proposal
from ironcage.emails import send_mail
from tickets.models import Ticket
from accounts.models import Badge


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        for ticket in Ticket.objects.all():
            if ticket.badge.count() < 1:
                badge = Badge(ticket=ticket)
                badge.save()

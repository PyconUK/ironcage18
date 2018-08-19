import re
from datetime import datetime

from django.conf import settings
from django.core.management import BaseCommand
from django.template.loader import get_template
from django.urls import reverse

from cfp.models import Proposal
from ironcage.emails import send_mail


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        accepted_proposals = Proposal.objects.filter(
            state__in=['accept', 'confirm']
        ).all()

        for proposal in accepted_proposals:
            if proposal.proposer.get_ticket() is None:
                template = get_template('cfp/emails/not_got_ticket.txt')
                context = {
                    'proposal': proposal,
                }
                body_raw = template.render(context)
                body = re.sub('\n\n\n+', '\n\n', body_raw)

                send_mail(
                    f'Your PyCon UK 2018 Proposal ({proposal.title})',
                    body,
                    proposal.proposer.email_addr,
                )

                proposal.replied_to = datetime.now()
                proposal.save()

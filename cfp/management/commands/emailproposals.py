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

        accepted_proposals = Proposal.objects.filter(state='accept', replied_to__isnull=True).all()

        for proposal in accepted_proposals:
            template = get_template('cfp/emails/proposal_accept.txt')
            context = {
                'proposal': proposal,
                'proposal_url': settings.DOMAIN + reverse('cfp:proposal', args=[proposal.proposal_id]),
                'user_proposal_count': Proposal.objects.filter(proposer=proposal.proposer).count()
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

        rejected_proposals = Proposal.objects.filter(state='reject', replied_to__isnull=True).all()

        for proposal in rejected_proposals:
            template = get_template('cfp/emails/proposal_reject.txt')
            context = {
                'proposal': proposal,
                'user_proposal_count': Proposal.objects.filter(proposer=proposal.proposer).count()
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

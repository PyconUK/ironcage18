import csv

from datetime import datetime, timezone

from django_slack import slack_message

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import StreamingHttpResponse
from django.shortcuts import redirect, render

from .forms import ProposalForm
from .models import Proposal


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def _can_submit(request):
    if datetime.now(timezone.utc) <= settings.CFP_CLOSE_AT:
        return True

    if request.GET.get('deadline-bypass-token', '') == settings.CFP_DEADLINE_BYPASS_TOKEN:
        return True

    return False


def new_proposal(request):
    if not _can_submit(request):
        return _new_proposal_after_cfp_closes(request)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.proposer = request.user
            proposal.save()
            messages.success(request, 'Thank you for submitting your proposal')
            slack_message('cfp/proposal_created.slack', {'proposal': proposal})
            return redirect(proposal)
    else:
        form = ProposalForm()

    context = {
        'form': form,
        'js_paths': ['cfp/cfp_form.js'],
    }
    return render(request, 'cfp/new_proposal.html', context)


def _new_proposal_after_cfp_closes(request):
    if request.method == 'POST':
        messages.warning(request, "We're sorry, the Call For Proposals has closed, and we were not able to process your submission")
    else:
        messages.warning(request, "We're sorry, the Call For Proposals has closed")

    return redirect('index')


@login_required
def proposal_edit(request, proposal_id):
    if not _can_submit(request):
        return _proposal_edit_after_cfp_closes(request, proposal_id)

    proposal = Proposal.objects.get_by_proposal_id_or_404(proposal_id)

    if request.user != proposal.proposer:
        messages.warning(request, 'Only the proposer of a proposal can update the proposal')
        return redirect('index')

    if request.method == 'POST':
        form = ProposalForm(request.POST, instance=proposal)
        if form.is_valid():
            proposal = form.save()
            proposal.save()
            messages.success(request, 'Thank you for updating your proposal')
            return redirect(proposal)
    else:
        form = ProposalForm(instance=proposal)

    context = {
        'form': form,
        'js_paths': ['cfp/cfp_form.js'],
    }
    return render(request, 'cfp/proposal_edit.html', context)


def _proposal_edit_after_cfp_closes(request, proposal_id):
    proposal = Proposal.objects.get_by_proposal_id_or_404(proposal_id)

    if request.method == 'POST':
        messages.warning(request, "We're sorry, the Call For Proposals has closed, and we were not able to process the change to your proposal")
    else:
        messages.warning(request, "We're sorry, the Call For Proposals has closed, and we are not accepting any more changes to proposals")

    return redirect(proposal)


@login_required
def proposal(request, proposal_id):
    proposal = Proposal.objects.get_by_proposal_id_or_404(proposal_id)

    if request.user != proposal.proposer:
        messages.warning(request, 'Only the proposer of a proposal can view the proposal')
        return redirect('index')

    context = {
        'proposal': proposal,
        'form': ProposalForm(),
        'cfp_open': _can_submit(request),
    }
    return render(request, 'cfp/proposal.html', context)

@login_required
def proposal_confirm(request, proposal_id):
    proposal = Proposal.objects.get_by_proposal_id_or_404(proposal_id)

    if request.user != proposal.proposer:
        messages.warning(request, 'Only the proposer of a proposal can confirm the proposal')
        return redirect('index')

    if request.method == 'POST' and proposal.state in ['accept', 'confirm']:
        proposal.state = 'confirm'
        proposal.confirmed = datetime.now()
        proposal.save()
        messages.success(request, "Thank you for confirming you will be able to present your proposal. See you in Cardiff!")
    else:
        messages.success(request, "Unfortunately your proposal has not been accepted, and therefore cannot be confirmed.")

    return redirect(proposal)


@permission_required('cfp.can_review_proposals', raise_exception=True)
def get_schedule_generate_csv(request):
    proposals = Proposal.objects.filter(state='accept').all()

    rows = [(
        'name', 'email_address', 'session_type', 'title',
        'duration', 'tag', 'subtitle', 'description', 'demand'
    )]

    for proposal in proposals:
        rows.append(
            (
                proposal.proposer.name,
                proposal.proposer.email_addr,
                proposal.session_type,
                proposal.title,
                30,  # description
                '',  # tag eg pydata
                proposal.subtitle,
                proposal.description,
                0  # demand
            )
        )

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="proposals.csv"'
    return response

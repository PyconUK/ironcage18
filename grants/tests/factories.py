from accounts.tests.factories import create_user

from grants.models import Application


def create_application(user=None):
    if user is None:
        user = create_user()

    return Application.objects.create(
        applicant=user,
        about_you='I have two thumbs',
        about_why='I use thumbs to press my space bar',
        requested_ticket_only=False,
        amount_requested='£1000',
        cost_breakdown='Train £500. Hotel £500.',
        sat=True,
        sun=True,
        mon=True,
        tue=False,
        wed=False,
    )

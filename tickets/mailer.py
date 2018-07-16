from django.conf import settings

from ironcage.emails import send_mail


INVITATION_TEMPLATE = '''
Hello!

{purchaser_name} has purchased you a ticket for PyCon UK 2018.

Please click here to claim your ticket:

    {url}

We look forward to seeing you in Cardiff!

~ The PyCon UK 2018 team
'''.strip()

FREE_TICKET_INVITATION_TEMPLATE = '''
Hello!

You have been assigned a ticket for PyCon UK 2018.

Please click here to claim your ticket:

    {url}

We look forward to seeing you in Cardiff!

~ The PyCon UK 2018 team
'''.strip()


def send_invitation_mail(ticket):
    invitation = ticket.invitation()
    url = settings.DOMAIN + invitation.get_absolute_url()

    if ticket.order is None:
        body = FREE_TICKET_INVITATION_TEMPLATE.format(url=url)
    else:
        purchaser_name = ticket.order.purchaser.name
        body = INVITATION_TEMPLATE.format(purchaser_name=purchaser_name, url=url)

    send_mail(
        f'PyCon UK 2018 ticket invitation ({ticket.ticket_id})',
        body,
        invitation.email_addr,
    )

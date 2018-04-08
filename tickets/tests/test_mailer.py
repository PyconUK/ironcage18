import re

from django.core import mail
from django.test import TestCase

from . import factories

from tickets.mailer import send_invitation_mail
from tickets.models import TicketInvitation


class MailerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user(email_addr='alice@example.com')

    def test_send_invitation_mail(self):
        factories.create_confirmed_order_for_others(self.alice)
        mail.outbox = []

        invitation = TicketInvitation.objects.get(email_addr='bob@example.com')
        send_invitation_mail(invitation.ticket)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['bob@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'PyCon UK 2018 ticket invitation ({invitation.ticket.ticket_id})')
        self.assertTrue(re.search(r'Alice has purchased you a ticket for PyCon UK 2018', email.body))
        self.assertTrue(re.search(r'http://testserver/tickets/invitations/\w{12}/', email.body))

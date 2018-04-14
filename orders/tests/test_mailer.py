import re

from django.core import mail
from django.test import TestCase

from tickets.tests import factories

from orders.mailer import send_order_confirmation_mail


class MailerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user(email_addr='alice@example.com')

    def test_send_order_confirmation_mail_for_order_for_self(self):
        order = factories.create_confirmed_order_for_self(self.alice)

        mail.outbox = []

        send_order_confirmation_mail(order)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['alice@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'PyCon UK 2018 order confirmation ({order.order_id})')
        self.assertTrue(re.search(r'You have purchased 1 ticket for PyCon UK 2018', email.body))
        self.assertTrue(re.search(fr'http://testserver/orders/{order.order_id}/receipt/', email.body))
        self.assertFalse(re.search('Ticket invitations have been sent to the following', email.body))
        self.assertTrue(re.search('We look forward to seeing you in Cardiff', email.body))

    def test_send_order_confirmation_mail_for_order_for_others(self):
        order = factories.create_confirmed_order_for_others(self.alice)

        mail.outbox = []

        send_order_confirmation_mail(order)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['alice@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'PyCon UK 2018 order confirmation ({order.order_id})')
        self.assertTrue(re.search(r'You have purchased 2 tickets for PyCon UK 2018', email.body))
        self.assertTrue(re.search(fr'http://testserver/orders/{order.order_id}/receipt/', email.body))
        self.assertTrue(re.search('Ticket invitations have been sent to the following', email.body))
        self.assertTrue(re.search('bob@example.com', email.body))
        self.assertTrue(re.search('carol@example.com', email.body))
        self.assertFalse(re.search('We look forward to seeing you in Cardiff', email.body))

    def test_send_order_confirmation_mail_for_order_for_self_and_others(self):
        order = factories.create_confirmed_order_for_self_and_others(self.alice)

        mail.outbox = []

        send_order_confirmation_mail(order)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['alice@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'PyCon UK 2018 order confirmation ({order.order_id})')
        self.assertTrue(re.search(r'You have purchased 3 tickets for PyCon UK 2018', email.body))
        self.assertTrue(re.search(fr'http://testserver/orders/{order.order_id}/receipt/', email.body))
        self.assertTrue(re.search('Ticket invitations have been sent to the following', email.body))
        self.assertTrue(re.search('bob@example.com', email.body))
        self.assertTrue(re.search('carol@example.com', email.body))
        self.assertTrue(re.search('We look forward to seeing you in Cardiff', email.body))

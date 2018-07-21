import re

from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from grants.tests.factories import create_application
from tickets.tests.factories import create_user


class TestEmailGrants(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = create_user(email_addr='alice@example.com')
        cls.bob = create_user(email_addr='bob@example.com')
        cls.clara = create_user(email_addr='clara@example.com')
        cls.donald = create_user(email_addr='donald@example.com')
        cls.erica = create_user(email_addr='erica@example.com')
        cls.frederick = create_user(email_addr='frederick@example.com')

        # Ticket and money awarded but not full amount
        cls.proposal_1 = create_application(cls.alice)
        cls.proposal_1.ticket_awarded = True
        cls.proposal_1.amount_awarded = 23.5
        cls.proposal_1.save()

        # Ticket and full amount of money awarded
        cls.proposal_2 = create_application(cls.bob)
        cls.proposal_2.ticket_awarded = True
        cls.proposal_2.amount_awarded = 23.5
        cls.proposal_2.full_amount_awarded = True
        cls.proposal_2.save()

        # No decisions made yet
        cls.proposal_3 = create_application(cls.clara)

        # Rejected
        cls.proposal_4 = create_application(cls.donald)
        cls.proposal_4.application_declined = True
        cls.proposal_4.save()

        # Ticket only wanted and ticket only given
        cls.proposal_5 = create_application(cls.erica)
        cls.proposal_5.requested_ticket_only = True
        cls.proposal_5.ticket_awarded = True
        cls.proposal_5.save()

        # Ticket and money wanted but ticket only given
        cls.proposal_6 = create_application(cls.frederick)
        cls.proposal_6.ticket_awarded = True
        cls.proposal_6.save()

    def test_propsals_get_email(self):
        mail.outbox = []

        call_command('emailgrants')

        self.assertEqual(len(mail.outbox), 5)

        # Ticket and money awarded but not full amount
        email = mail.outbox[0]
        self.assertEqual(email.to, ['alice@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'Your PyCon UK 2018 Financial Assistance')
        self.assertTrue(re.search(r'Unfortunately we\nare unable to offer you the full amount requested', email.body))
        self.assertTrue(re.search(fr'but we can offer you £{self.proposal_1.amount_awarded}', email.body))
        self.assertFalse(re.search(r'we can offer you the full amount', email.body))
        self.assertFalse(re.search(r'we are unable to meet your request', email.body))
        self.assertFalse(re.search(r'we can offer you a ticket', email.body))
        self.assertFalse(re.search(r'we can offer you\na free ticket', email.body))

        # Ticket and full amount of money awarded
        email = mail.outbox[1]
        self.assertEqual(email.to, ['bob@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'Your PyCon UK 2018 Financial Assistance')
        self.assertFalse(re.search(r'Unfortunately we\nare unable to offer you the full amount requested', email.body))
        self.assertFalse(re.search(fr'we can offer you the full amount (£{self.proposal_2.amount_awarded})', email.body))
        self.assertFalse(re.search(r'we are unable to meet your request', email.body))
        self.assertFalse(re.search(r'we can offer you a ticket', email.body))
        self.assertFalse(re.search(r'we can offer you\na free ticket', email.body))

        # Rejected
        email = mail.outbox[2]
        self.assertEqual(email.to, ['donald@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'Your PyCon UK 2018 Financial Assistance')
        self.assertFalse(re.search(r'Unfortunately we\nare unable to offer you the full amount requested', email.body))
        self.assertFalse(re.search(r'but we can offer you £', email.body))
        self.assertFalse(re.search(r'we can offer you the full amount', email.body))
        self.assertTrue(re.search(r'we\nare unable to meet your request', email.body))
        self.assertFalse(re.search(r'we can offer you a ticket', email.body))
        self.assertFalse(re.search(r'we can offer you\na free ticket', email.body))

        # Ticket only wanted and ticket only given
        email = mail.outbox[3]
        self.assertEqual(email.to, ['erica@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'Your PyCon UK 2018 Financial Assistance')
        self.assertFalse(re.search(r'Unfortunately we\nare unable to offer you the full amount requested', email.body))
        self.assertFalse(re.search(r'but we can offer you £', email.body))
        self.assertFalse(re.search(r'we can offer you the full amount', email.body))
        self.assertFalse(re.search(r'we are unable to meet your request', email.body))
        self.assertTrue(re.search(r'we can offer you a ticket', email.body))
        self.assertFalse(re.search(r'we can offer you\na free ticket', email.body))

        # Ticket and money wanted but ticket only given
        email = mail.outbox[4]
        self.assertEqual(email.to, ['frederick@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'Your PyCon UK 2018 Financial Assistance')
        self.assertTrue(re.search(r'Unfortunately we\nare unable to offer you the full amount requested', email.body))
        self.assertFalse(re.search(r'but we can offer you £', email.body))
        self.assertFalse(re.search(r'we can offer you the full amount', email.body))
        self.assertFalse(re.search(r'we are unable to meet your request', email.body))
        self.assertFalse(re.search(r'we can offer you a ticket', email.body))
        self.assertTrue(re.search(r'we can offer you \na free ticket', email.body))

    def test_propsals_dont_get_email_twice(self):
        mail.outbox = []

        call_command('emailgrants')

        self.assertEqual(len(mail.outbox), 5)

        mail.outbox = []

        call_command('emailgrants')

        self.assertEqual(len(mail.outbox), 0)

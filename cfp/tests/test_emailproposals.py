import re

from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from cfp.tests.factories import create_proposal
from tickets.tests.factories import create_user


class TestEmailProposals(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = create_user(email_addr='alice@example.com')
        cls.bob = create_user(email_addr='bob@example.com')
        cls.clara = create_user(email_addr='clara@example.com')
        cls.proposal_1 = create_proposal(cls.alice, state='accept')
        cls.proposal_2 = create_proposal(cls.alice, state='reject')
        cls.proposal_3 = create_proposal(cls.bob, state='accept')
        cls.proposal_4 = create_proposal(cls.clara, state='')

    def test_propsals_get_email(self):
        mail.outbox = []

        call_command('emailproposals')

        self.assertEqual(len(mail.outbox), 3)

        email = mail.outbox[0]
        self.assertEqual(email.to, ['alice@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'Your PyCon UK 2018 Proposal ({self.proposal_1.title})')
        self.assertTrue(re.search(r'I’m delighted to inform you that we have selected this proposal for our programme.', email.body))
        self.assertTrue(re.search(fr'http://testserver/cfp/proposals/{self.proposal_1.proposal_id}/', email.body))
        self.assertTrue(re.search('If you have submitted other proposals', email.body))
        self.assertFalse(re.search('I’m sorry to inform you that we have not selected this proposal for our programme.', email.body))

        email = mail.outbox[1]
        self.assertEqual(email.to, ['bob@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'Your PyCon UK 2018 Proposal ({self.proposal_3.title})')
        self.assertTrue(re.search(r'I’m delighted to inform you that we have selected this proposal for our programme.', email.body))
        self.assertTrue(re.search(fr'http://testserver/cfp/proposals/{self.proposal_3.proposal_id}/', email.body))
        self.assertFalse(re.search('If you have submitted other proposals', email.body))
        self.assertFalse(re.search('I’m sorry to inform you that we have not selected this proposal for our programme.', email.body))

        email = mail.outbox[2]
        self.assertEqual(email.to, ['alice@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'Your PyCon UK 2018 Proposal ({self.proposal_2.title})')
        self.assertFalse(re.search(r'I’m delighted to inform you that we have selected this proposal for our programme.', email.body))
        self.assertFalse(re.search(fr'http://testserver/cfp/proposals/{self.proposal_2.proposal_id}/', email.body))
        self.assertTrue(re.search('If you have submitted other proposals', email.body))
        self.assertTrue(re.search('I’m sorry to inform you that we have not selected this proposal for our programme.', email.body))

    def test_propsals_dont_get_email_twice(self):
        mail.outbox = []

        call_command('emailproposals')

        self.assertEqual(len(mail.outbox), 3)

        mail.outbox = []

        call_command('emailproposals')

        self.assertEqual(len(mail.outbox), 0)

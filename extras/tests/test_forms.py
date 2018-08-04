from django.test import TestCase

from . import factories
from .utils import build_querydict

from extras.forms import ChildrenTicketForm


class ChildrenTicketFormTests(TestCase):
    def test_from_pending_order(self):
        order = factories.create_pending_children_ticket_order()
        expected = {
            'adult_name': 'Puff The Elder',
            'adult_email_addr': 'puff@example.com',
            'adult_phone_number': '07700 900001',
            'name': 'Puff',
            'age': 10,
            'accessibility_reqs': 'Occasionally breathe fire',
            'dietary_reqs': 'Allergic to Welsh Cakes',
        }
        self.assertEqual(ChildrenTicketForm.from_pending_order(order).data, expected)

    def test_is_not_valid_with_no_email_addr(self):
        post_data = build_querydict({
            'adult_name': 'Puff The Elder',
            'adult_email_addr': '',
            'adult_phone_number': '07700 900001',
            'name': 'Puff',
            'age': 10,
            'accessibility_reqs': 'Occasionally breathe fire',
            'dietary_reqs': 'Allergic to Welsh Cakes',
        })

        form = ChildrenTicketForm(post_data)
        self.assertEqual(
            form.errors,
            {'adult_email_addr': ['This field is required.']}
        )

    def test_is_not_valid_with_bad_age(self):
        post_data = build_querydict({
            'adult_name': 'Puff The Elder',
            'adult_email_addr': 'puff@example.com',
            'adult_phone_number': '07700 900001',
            'name': 'Puff',
            'age': 'ten',
            'accessibility_reqs': 'Occasionally breathe fire',
            'dietary_reqs': 'Allergic to Welsh Cakes',
        })

        form = ChildrenTicketForm(post_data)
        self.assertEqual(
            form.errors,
            {'age': ['Enter a whole number.']}
        )

    def test_is_not_valid_with_no_phone_number(self):
        post_data = build_querydict({
            'adult_name': 'Puff The Elder',
            'adult_email_addr': 'puff@example.com',
            'adult_phone_number': '',
            'name': 'Puff',
            'age': 10,
            'accessibility_reqs': 'Occasionally breathe fire',
            'dietary_reqs': 'Allergic to Welsh Cakes',
        })

        form = ChildrenTicketForm(post_data)
        self.assertEqual(
            form.errors,
            {'adult_phone_number': ['This field is required.']}
        )

    def test_is_valid_with_no_requirements(self):
        post_data = build_querydict({
            'adult_name': 'Puff The Elder',
            'adult_email_addr': 'puff@example.com',
            'adult_phone_number': '07700 900001',
            'name': 'Puff',
            'age': 10,
            'accessibility_reqs': None,
            'dietary_reqs': None,
        })

        form = ChildrenTicketForm(post_data)
        self.assertEqual(
            form.errors,
            {}
        )

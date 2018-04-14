from django.test import TestCase

from . import factories
from .utils import build_querydict

from tickets.forms import TicketForm, TicketForSelfForm, TicketForOthersFormSet


class TicketFormTests(TestCase):
    def test_from_pending_order_for_self(self):
        order = factories.create_pending_order_for_self()
        expected = {
            'who': 'self',
            'rate': 'individual',
        }
        self.assertEqual(TicketForm.from_pending_order(order).data, expected)

    def test_from_pending_order_for_others(self):
        order = factories.create_pending_order_for_others()
        expected = {
            'who': 'others',
            'rate': 'individual',
        }
        self.assertEqual(TicketForm.from_pending_order(order).data, expected)

    def test_from_pending_order_for_self_and_others(self):
        order = factories.create_pending_order_for_self_and_others()
        expected = {
            'who': 'self and others',
            'rate': 'individual',
        }
        self.assertEqual(TicketForm.from_pending_order(order).data, expected)


class TicketForSelfFormTests(TestCase):
    def test_from_pending_order_for_self(self):
        order = factories.create_pending_order_for_self()
        expected = {
            'days': ['sat', 'sun', 'mon'],
        }
        self.assertEqual(TicketForSelfForm.from_pending_order(order).data, expected)

    def test_from_pending_order_for_others(self):
        order = factories.create_pending_order_for_others()
        self.assertEqual(TicketForSelfForm.from_pending_order(order).data, {})

    def test_from_pending_order_for_self_and_others(self):
        order = factories.create_pending_order_for_self_and_others()
        expected = {
            'days': ['sat', 'sun', 'mon'],
        }
        self.assertEqual(TicketForSelfForm.from_pending_order(order).data, expected)


class TicketForOthersFormSetTests(TestCase):
    def test_from_pending_order_for_self(self):
        order = factories.create_pending_order_for_self()
        self.assertEqual(TicketForOthersFormSet.from_pending_order(order).data, {})

    def test_from_pending_order_for_others(self):
        order = factories.create_pending_order_for_others()
        expected = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '2',
            'form-0-days': ['sun', 'mon'],
            'form-0-email_addr': 'bob@example.com',
            'form-1-days': ['mon', 'tue'],
            'form-1-email_addr': 'carol@example.com',
        }
        self.assertEqual(TicketForOthersFormSet.from_pending_order(order).data, expected)

    def test_from_pending_order_for_self_and_others(self):
        order = factories.create_pending_order_for_self_and_others()
        expected = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '2',
            'form-0-days': ['sun', 'mon'],
            'form-0-email_addr': 'bob@example.com',
            'form-1-days': ['mon', 'tue'],
            'form-1-email_addr': 'carol@example.com',
        }
        self.assertEqual(TicketForOthersFormSet.from_pending_order(order).data, expected)

    def test_is_valid_with_valid_data(self):
        post_data = build_querydict({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['sat', 'sun'],
            'form-1-email_addr': 'test2@example.com',
            'form-1-days': ['mon', 'tue', 'wed']
        })

        formset = TicketForOthersFormSet(post_data)
        self.assertTrue(formset.is_valid())

    def test_is_valid_with_valid_data_and_empty_form(self):
        post_data = build_querydict({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['sat', 'sun'],
            'form-1-email_addr': '',
        })

        formset = TicketForOthersFormSet(post_data)
        self.assertTrue(formset.is_valid())

    def test_is_not_valid_with_no_email_addr(self):
        post_data = build_querydict({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['sat', 'sun'],
            'form-1-email_addr': '',
            'form-1-days': ['mon', 'tue', 'wed']
        })

        formset = TicketForOthersFormSet(post_data)
        self.assertEqual(
            formset.errors,
            [{}, {'email_addr': ['This field is required.']}]
        )

    def test_is_not_valid_with_no_days(self):
        post_data = build_querydict({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['sat', 'sun'],
            'form-1-email_addr': 'test2@example.com',
        })

        formset = TicketForOthersFormSet(post_data)
        self.assertEqual(
            formset.errors,
            [{}, {'days': ['This field is required.']}]
        )

    def test_is_not_valid_with_no_nonempty_forms(self):
        post_data = build_querydict({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': '',
            'form-1-email_addr': '',
        })

        formset = TicketForOthersFormSet(post_data)
        self.assertEqual(
            formset.errors,
            [{'email_addr': ['This field is required.'], 'days': ['This field is required.']}, {}]
        )

    def test_is_not_valid_with_all_deleted_forms(self):
        post_data = build_querydict({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-DELETE': 'on',
            'form-1-email_addr': '',
            'form-1-DELETE': 'on',
        })

        formset = TicketForOthersFormSet(post_data)
        self.assertFalse(formset.is_valid())

    def test_email_addrs_and_days(self):
        post_data = build_querydict({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['sat', 'sun'],
            'form-1-email_addr': 'test2@example.com',
            'form-1-days': ['mon', 'tue', 'wed']
        })

        formset = TicketForOthersFormSet(post_data)
        formset.errors  # Trigger full clean
        self.assertEqual(
            formset.email_addrs_and_days,
            [('test1@example.com', ['thu', 'fri']), ('test2@example.com', ['sat', 'sun', 'mon'])]
        )

    def test_email_addrs_and_days_with_valid_data_and_deleted_form(self):
        post_data = build_querydict({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['sat', 'sun'],
            'form-1-email_addr': '',
            'form-1-DELETE': 'on',
        })

        formset = TicketForOthersFormSet(post_data)
        formset.errors  # Trigger full clean
        self.assertEqual(
            formset.email_addrs_and_days,
            [('test1@example.com', ['sat', 'sun'])]
        )

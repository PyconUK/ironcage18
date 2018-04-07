from unittest.mock import patch

from django_slack.utils import get_backend as get_slack_backend

from django.core import mail
from django.test import TestCase

from . import factories
from ironcage.tests import utils

from tickets import actions
from tickets.models import TicketInvitation


class CreatePendingOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_order_for_self_individual(self):
        order = actions.create_pending_order(
            purchaser=self.alice,
            billing_details={'name': 'Alice Apple', 'addr': 'Eadrax, Sirius Tau'},
            rate='individual',
            days_for_self=['thu', 'fri', 'sat']
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertIsNone(self.alice.get_ticket())

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.invoice_number, None)
        self.assertEqual(order.billing_name, 'Alice Apple')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')

    def test_order_for_self_corporate(self):
        order = actions.create_pending_order(
            purchaser=self.alice,
            billing_details={'name': 'Sirius Cybernetics Corp.', 'addr': 'Eadrax, Sirius Tau'},
            rate='corporate',
            days_for_self=['thu', 'fri', 'sat'],
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertIsNone(self.alice.get_ticket())

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.invoice_number, None)
        self.assertEqual(order.billing_name, 'Sirius Cybernetics Corp.')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')

    def test_order_for_others(self):
        order = actions.create_pending_order(
            purchaser=self.alice,
            billing_details={'name': 'Alice Apple', 'addr': 'Eadrax, Sirius Tau'},
            rate='individual',
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertIsNone(self.alice.get_ticket())

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.invoice_number, None)
        self.assertEqual(order.billing_name, 'Alice Apple')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')

    def test_order_for_self_and_others(self):
        order = actions.create_pending_order(
            purchaser=self.alice,
            billing_details={'name': 'Alice Apple', 'addr': 'Eadrax, Sirius Tau'},
            rate='individual',
            days_for_self=['thu', 'fri', 'sat'],
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertIsNone(self.alice.get_ticket())

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.invoice_number, None)
        self.assertEqual(order.billing_name, 'Alice Apple')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')


class UpdatePendingOrderTests(TestCase):
    def test_order_for_self_to_order_for_self(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            billing_details={'name': 'Alice Apple', 'addr': 'Eadrax, Sirius Tau'},
            rate='individual',
            days_for_self=['fri'],
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.invoice_number, None)
        self.assertEqual(order.billing_name, 'Alice Apple')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')

        [row] = order.all_order_rows()

        self.assertEqual(row.cost_excl_vat, 45)
        self.assertEqual(row.item_descr, '1-day individual-rate ticket')
        self.assertEqual(row.item_descr_extra, 'Friday')

        ticket = row.ticket
        self.assertEqual(ticket.owner, order.purchaser)
        self.assertEqual(ticket.rate, 'individual')
        self.assertEqual(ticket.days(), ['Friday'])

    def test_order_for_self_to_order_for_others(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            billing_details={'name': 'Alice Apple', 'addr': 'Eadrax, Sirius Tau'},
            rate='individual',
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.invoice_number, None)
        self.assertEqual(order.billing_name, 'Alice Apple')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')

        [row1, row2] = order.all_order_rows()

        self.assertEqual(row1.cost_excl_vat, 75)
        self.assertEqual(row1.item_descr, '2-day individual-rate ticket')
        self.assertEqual(row1.item_descr_extra, 'Friday, Saturday')

        ticket1 = row1.ticket
        self.assertEqual(ticket1.owner, None)
        self.assertEqual(ticket1.rate, 'individual')
        self.assertEqual(ticket1.days(), ['Friday', 'Saturday'])

        self.assertEqual(row2.cost_excl_vat, 75)
        self.assertEqual(row2.item_descr, '2-day individual-rate ticket')
        self.assertEqual(row2.item_descr_extra, 'Saturday, Sunday')

        ticket2 = row2.ticket
        self.assertEqual(ticket1.owner, None)
        self.assertEqual(ticket2.rate, 'individual')
        self.assertEqual(ticket2.days(), ['Saturday', 'Sunday'])

    def test_order_for_self_to_order_for_self_and_others(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            billing_details={'name': 'Alice Apple', 'addr': 'Eadrax, Sirius Tau'},
            rate='individual',
            days_for_self=['fri', 'sat', 'sun'],
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.invoice_number, None)
        self.assertEqual(order.billing_name, 'Alice Apple')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')

        [row1, row2, row3] = order.all_order_rows()

        self.assertEqual(row1.cost_excl_vat, 105)
        self.assertEqual(row1.item_descr, '3-day individual-rate ticket')
        self.assertEqual(row1.item_descr_extra, 'Friday, Saturday, Sunday')

        ticket1 = row1.ticket
        self.assertEqual(ticket1.owner, order.purchaser)
        self.assertEqual(ticket1.rate, 'individual')
        self.assertEqual(ticket1.days(), ['Friday', 'Saturday', 'Sunday'])

        self.assertEqual(row2.cost_excl_vat, 75)
        self.assertEqual(row2.item_descr, '2-day individual-rate ticket')
        self.assertEqual(row2.item_descr_extra, 'Friday, Saturday')

        ticket2 = row2.ticket
        self.assertEqual(ticket2.owner, None)
        self.assertEqual(ticket2.rate, 'individual')
        self.assertEqual(ticket2.days(), ['Friday', 'Saturday'])

        self.assertEqual(row3.cost_excl_vat, 75)
        self.assertEqual(row3.item_descr, '2-day individual-rate ticket')
        self.assertEqual(row3.item_descr_extra, 'Saturday, Sunday')

        ticket3 = row3.ticket
        self.assertEqual(ticket3.owner, None)
        self.assertEqual(ticket3.rate, 'individual')
        self.assertEqual(ticket3.days(), ['Saturday', 'Sunday'])

    def test_individual_order_to_corporate_order(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            billing_details={'name': 'Sirius Cybernetics Corp.', 'addr': 'Eadrax, Sirius Tau'},
            rate='corporate',
            days_for_self=['fri', 'sat', 'sun'],
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.invoice_number, None)
        self.assertEqual(order.billing_name, 'Sirius Cybernetics Corp.')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')

        [row] = order.all_order_rows()

        self.assertEqual(row.cost_excl_vat, 210)
        self.assertEqual(row.item_descr, '3-day corporate-rate ticket')
        self.assertEqual(row.item_descr_extra, 'Friday, Saturday, Sunday')

        ticket = row.ticket
        self.assertEqual(ticket.owner, order.purchaser)
        self.assertEqual(ticket.rate, 'corporate')
        self.assertEqual(ticket.days(), ['Friday', 'Saturday', 'Sunday'])

    def test_corporate_order_to_individual_order(self):
        order = factories.create_pending_order_for_self(rate='corporate')
        actions.update_pending_order(
            order,
            billing_details={'name': 'Alice Apple', 'addr': 'Eadrax, Sirius Tau'},
            rate='individual',
            days_for_self=['fri', 'sat', 'sun'],
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.invoice_number, None)
        self.assertEqual(order.billing_name, 'Alice Apple')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')

        [row] = order.all_order_rows()

        self.assertEqual(row.cost_excl_vat, 105)
        self.assertEqual(row.item_descr, '3-day individual-rate ticket')
        self.assertEqual(row.item_descr_extra, 'Friday, Saturday, Sunday')

        ticket = row.ticket
        self.assertEqual(ticket.owner, order.purchaser)
        self.assertEqual(ticket.rate, 'individual')
        self.assertEqual(ticket.days(), ['Friday', 'Saturday', 'Sunday'])


class ConfirmOrderTests(TestCase):
    def test_order_for_self(self):
        order = factories.create_pending_order_for_self()
        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1495355163)

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.stripe_charge_created.timestamp(), 1495355163)
        self.assertEqual(order.stripe_charge_failure_reason, '')
        self.assertEqual(order.status, 'successful')
        self.assertEqual(order.invoice_number, 1)

        self.assertEqual(order.order_rows.count(), 1)
        [row] = order.all_order_rows()

        self.assertEqual(row.cost_excl_vat, 105)
        self.assertEqual(row.item_descr, '3-day individual-rate ticket')
        self.assertEqual(row.item_descr_extra, 'Thursday, Friday, Saturday')

        ticket = row.ticket
        self.assertEqual(ticket.owner, order.purchaser)
        self.assertEqual(ticket.rate, 'individual')
        self.assertEqual(ticket.days(), ['Thursday', 'Friday', 'Saturday'])

        self.assertEqual(order.purchaser.orders.count(), 1)
        self.assertIsNotNone(order.purchaser.get_ticket())
        self.assertEqual(len(mail.outbox), 1)

    def test_order_for_others(self):
        order = factories.create_pending_order_for_others()
        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1495355163)

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.stripe_charge_created.timestamp(), 1495355163)
        self.assertEqual(order.stripe_charge_failure_reason, '')
        self.assertEqual(order.status, 'successful')
        self.assertEqual(order.invoice_number, 1)

        self.assertEqual(order.order_rows.count(), 2)
        [row1, row2] = order.all_order_rows()

        self.assertEqual(row1.cost_excl_vat, 75)
        self.assertEqual(row1.item_descr, '2-day individual-rate ticket')
        self.assertEqual(row1.item_descr_extra, 'Friday, Saturday')

        ticket1 = row1.ticket
        self.assertIsNone(ticket1.owner)
        self.assertEqual(ticket1.rate, 'individual')
        self.assertEqual(ticket1.days(), ['Friday', 'Saturday'])

        invitation1 = ticket1.invitation()
        self.assertEqual(invitation1.email_addr, 'bob@example.com')
        self.assertEqual(invitation1.status, 'unclaimed')

        self.assertEqual(row2.cost_excl_vat, 75)
        self.assertEqual(row2.item_descr, '2-day individual-rate ticket')
        self.assertEqual(row2.item_descr_extra, 'Saturday, Sunday')

        ticket2 = row2.ticket
        self.assertIsNone(ticket2.owner)
        self.assertEqual(ticket2.rate, 'individual')
        self.assertEqual(ticket2.days(), ['Saturday', 'Sunday'])

        invitation2 = ticket2.invitation()
        self.assertEqual(invitation2.email_addr, 'carol@example.com')
        self.assertEqual(invitation2.status, 'unclaimed')

        self.assertEqual(order.purchaser.orders.count(), 1)
        self.assertIsNone(order.purchaser.get_ticket())
        self.assertEqual(len(mail.outbox), 3)

    def test_order_for_self_and_others(self):
        order = factories.create_pending_order_for_self_and_others()
        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1495355163)

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.stripe_charge_created.timestamp(), 1495355163)
        self.assertEqual(order.stripe_charge_failure_reason, '')
        self.assertEqual(order.status, 'successful')
        self.assertEqual(order.invoice_number, 1)

        self.assertEqual(order.order_rows.count(), 3)
        [row1, row2, row3] = order.all_order_rows()

        self.assertEqual(row1.cost_excl_vat, 105)
        self.assertEqual(row1.item_descr, '3-day individual-rate ticket')
        self.assertEqual(row1.item_descr_extra, 'Thursday, Friday, Saturday')

        ticket1 = row1.ticket
        self.assertEqual(ticket1.owner, order.purchaser)
        self.assertEqual(ticket1.rate, 'individual')
        self.assertEqual(ticket1.days(), ['Thursday', 'Friday', 'Saturday'])

        self.assertEqual(row2.cost_excl_vat, 75)
        self.assertEqual(row2.item_descr, '2-day individual-rate ticket')
        self.assertEqual(row2.item_descr_extra, 'Friday, Saturday')

        ticket2 = row2.ticket
        self.assertIsNone(ticket2.owner)
        self.assertEqual(ticket2.rate, 'individual')
        self.assertEqual(ticket2.days(), ['Friday', 'Saturday'])

        invitation2 = ticket2.invitation()
        self.assertEqual(invitation2.email_addr, 'bob@example.com')
        self.assertEqual(invitation2.status, 'unclaimed')

        self.assertEqual(row3.cost_excl_vat, 75)
        self.assertEqual(row3.item_descr, '2-day individual-rate ticket')
        self.assertEqual(row3.item_descr_extra, 'Saturday, Sunday')

        ticket3 = row3.ticket
        self.assertIsNone(ticket3.owner)
        self.assertEqual(ticket3.rate, 'individual')
        self.assertEqual(ticket3.days(), ['Saturday', 'Sunday'])

        invitation3 = ticket3.invitation()
        self.assertEqual(invitation3.email_addr, 'carol@example.com')
        self.assertEqual(invitation3.status, 'unclaimed')

        self.assertEqual(order.purchaser.orders.count(), 1)
        self.assertIsNotNone(order.purchaser.get_ticket())
        self.assertEqual(len(mail.outbox), 3)

    def test_after_order_marked_as_failed(self):
        order = factories.create_pending_order_for_self()
        actions.mark_order_as_failed(order, 'There was a problem')

        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1495355163)

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.stripe_charge_created.timestamp(), 1495355163)
        self.assertEqual(order.stripe_charge_failure_reason, '')
        self.assertEqual(order.status, 'successful')
        self.assertEqual(order.invoice_number, 1)

        self.assertEqual(order.purchaser.orders.count(), 1)
        self.assertIsNotNone(order.purchaser.get_ticket())

        ticket = order.purchaser.get_ticket()
        self.assertEqual(ticket.days(), ['Thursday', 'Friday', 'Saturday'])

    def test_invoice_number_increments(self):
        order = factories.create_pending_order_for_self()
        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1495355163)
        self.assertEqual(order.invoice_number, 1)

        order = factories.create_pending_order_for_self()
        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvx', 1495355164)
        self.assertEqual(order.invoice_number, 2)

    def test_sends_slack_message(self):
        backend = get_slack_backend()
        order = factories.create_pending_order_for_self()
        backend.reset_messages()

        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1495355163)

        messages = backend.retrieve_messages()
        self.assertEqual(len(messages), 1)
        text = messages[0]['text']
        self.assertIn('Alice has just placed an order for 1 ticket', text)


class MarkOrderAsFailed(TestCase):
    def test_mark_order_as_failed(self):
        order = factories.create_pending_order_for_self()

        actions.mark_order_as_failed(order, 'There was a problem')

        self.assertEqual(order.stripe_charge_failure_reason, 'There was a problem')
        self.assertEqual(order.status, 'failed')


class MarkOrderAsErroredAfterCharge(TestCase):
    def test_mark_order_as_errored_after_charge(self):
        order = factories.create_pending_order_for_self()

        actions.mark_order_as_errored_after_charge(order, 'ch_abcdefghijklmnopqurstuvw')

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.status, 'errored')


class ProcessStripeChargeTests(TestCase):
    def setUp(self):
        self.order = factories.create_pending_order_for_self()

    def test_process_stripe_charge_success(self):
        token = 'tok_abcdefghijklmnopqurstuvwx'
        with utils.patched_charge_creation_success():
            actions.process_stripe_charge(self.order, token)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'successful')

    def test_process_stripe_charge_failure(self):
        token = 'tok_abcdefghijklmnopqurstuvwx'
        with utils.patched_charge_creation_failure():
            actions.process_stripe_charge(self.order, token)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'failed')

    def test_process_stripe_charge_error_after_charge_1(self):
        # This test checks that an order is marked as errored if an
        # IntegrityError is raised because a user creates an order for a ticket
        # for themselves when they already have a ticket.
        factories.create_confirmed_order_for_self(self.order.purchaser)
        token = 'tok_abcdefghijklmnopqurstuvwx'

        with utils.patched_charge_creation_success(), utils.patched_refund_creation_expected():
            actions.process_stripe_charge(self.order, token)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'errored')
        self.assertEqual(self.order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')

    def test_process_stripe_charge_error_after_charge_2(self):
        # This test checks that an order is marked as errored if two orders are
        # created at exactly the same time, leading to the race condition in
        # Order.confirm.
        order = factories.create_confirmed_order_for_others()
        token = 'tok_abcdefghijklmnopqurstuvwx'

        with utils.patched_charge_creation_success(), utils.patched_refund_creation_expected(), patch('tickets.models.Order.get_next_invoice_number') as mock:
            mock.return_value = order.invoice_number
            actions.process_stripe_charge(self.order, token)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'errored')
        self.assertEqual(self.order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')


class TicketInvitationTests(TestCase):
    def test_claim_ticket_invitation(self):
        factories.create_confirmed_order_for_others()
        bob = factories.create_user('Bob')

        invitation = TicketInvitation.objects.get(email_addr='bob@example.com')
        actions.claim_ticket_invitation(bob, invitation)

        self.assertIsNotNone(bob.get_ticket())

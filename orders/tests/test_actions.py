from unittest.mock import patch

from django_slack.utils import get_backend as get_slack_backend

from django.core import mail
from django.test import TestCase

from ironcage.tests import utils
from tickets.models import Ticket
from tickets.tests import factories
from orders.models import Refund
from orders import actions


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
        self.assertEqual(row.item_descr_extra, 'Saturday, Sunday, Monday')

        ticket = row.item
        self.assertEqual(ticket.owner, order.purchaser)
        self.assertEqual(ticket.rate, 'individual')
        self.assertEqual(ticket.days(), ['Saturday', 'Sunday', 'Monday'])

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
        self.assertEqual(row1.item_descr_extra, 'Sunday, Monday')

        ticket1 = row1.item
        self.assertIsNone(ticket1.owner)
        self.assertEqual(ticket1.rate, 'individual')
        self.assertEqual(ticket1.days(), ['Sunday', 'Monday'])

        invitation1 = ticket1.invitation()
        self.assertEqual(invitation1.email_addr, 'bob@example.com')
        self.assertEqual(invitation1.status, 'unclaimed')

        self.assertEqual(row2.cost_excl_vat, 75)
        self.assertEqual(row2.item_descr, '2-day individual-rate ticket')
        self.assertEqual(row2.item_descr_extra, 'Monday, Tuesday')

        ticket2 = row2.item
        self.assertIsNone(ticket2.owner)
        self.assertEqual(ticket2.rate, 'individual')
        self.assertEqual(ticket2.days(), ['Monday', 'Tuesday'])

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
        self.assertEqual(row1.item_descr_extra, 'Saturday, Sunday, Monday')

        ticket1 = row1.item
        self.assertEqual(ticket1.owner, order.purchaser)
        self.assertEqual(ticket1.rate, 'individual')
        self.assertEqual(ticket1.days(), ['Saturday', 'Sunday', 'Monday'])

        self.assertEqual(row2.cost_excl_vat, 75)
        self.assertEqual(row2.item_descr, '2-day individual-rate ticket')
        self.assertEqual(row2.item_descr_extra, 'Sunday, Monday')

        ticket2 = row2.item
        self.assertIsNone(ticket2.owner)
        self.assertEqual(ticket2.rate, 'individual')
        self.assertEqual(ticket2.days(), ['Sunday', 'Monday'])

        invitation2 = ticket2.invitation()
        self.assertEqual(invitation2.email_addr, 'bob@example.com')
        self.assertEqual(invitation2.status, 'unclaimed')

        self.assertEqual(row3.cost_excl_vat, 75)
        self.assertEqual(row3.item_descr, '2-day individual-rate ticket')
        self.assertEqual(row3.item_descr_extra, 'Monday, Tuesday')

        ticket3 = row3.item
        self.assertIsNone(ticket3.owner)
        self.assertEqual(ticket3.rate, 'individual')
        self.assertEqual(ticket3.days(), ['Monday', 'Tuesday'])

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
        self.assertEqual(ticket.days(), ['Saturday', 'Sunday', 'Monday'])

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

        with utils.patched_charge_creation_success(), utils.patched_refund_creation():
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

        with utils.patched_charge_creation_success(), utils.patched_refund_creation(), patch('orders.models.Order.get_next_invoice_number') as mock:
            mock.return_value = order.invoice_number
            actions.process_stripe_charge(self.order, token)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'errored')
        self.assertEqual(self.order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')


class RefundTicketTests(TestCase):
    def test_refund_item(self):
        ticket = factories.create_ticket()
        order_row = ticket.order_row

        with utils.patched_refund_creation():
            actions.refund_item(ticket, 'Refund requested by user')

        with self.assertRaises(Ticket.DoesNotExist):
            ticket.refresh_from_db()

        order_row.refresh_from_db()
        self.assertIsNone(order_row.item)
        self.assertEqual(order_row.cost_excl_vat, 105)
        self.assertEqual(order_row.item_descr, '3-day individual-rate ticket')
        self.assertEqual(order_row.item_descr_extra, 'Saturday, Sunday, Monday')
        self.assertIsNotNone(order_row.refund)
        self.assertEqual(order_row.refund.reason, 'Refund requested by user')
        self.assertEqual(order_row.refund.credit_note_number, 1)

    def test_multiple_refunds_have_correct_credit_note_numbers(self):
        order1 = factories.create_confirmed_order_for_others()
        order2 = factories.create_confirmed_order_for_self()

        tickets1 = order1.all_tickets()
        tickets2 = order2.all_tickets()

        with utils.patched_refund_creation():
            actions.refund_item(tickets1[0], 'Refund requested by user')

        with utils.patched_refund_creation():
            actions.refund_item(tickets2[0], 'Refund requested by user')

        with utils.patched_refund_creation():
            actions.refund_item(tickets1[1], 'Refund requested by user')

        refunds = Refund.objects.order_by('id')
        credit_note_numbers = [refund.full_credit_note_number for refund in refunds]

        self.assertEqual(
            credit_note_numbers,
            ['R-2018-0001-01', 'R-2018-0002-01', 'R-2018-0001-01']
        )

    def test_ticket_purchase_after_refund(self):
        user = factories.create_user()
        factories.create_confirmed_order_for_self(user)
        ticket = user.get_ticket()

        order = factories.create_pending_order_for_self(user)
        token = 'tok_abcdefghijklmnopqurstuvwx'
        with utils.patched_charge_creation_success(), utils.patched_refund_creation():
            actions.process_stripe_charge(order, token)
        self.assertEqual(order.status, 'errored')

        with utils.patched_refund_creation():
            actions.refund_item(ticket, 'Refund requested by user')

        user.refresh_from_db()
        self.assertIsNone(user.get_ticket())

        order = factories.create_pending_order_for_self(user)
        with utils.patched_charge_creation_success():
            actions.process_stripe_charge(order, token)
        self.assertEqual(order.status, 'successful')

        user.refresh_from_db()
        self.assertIsNotNone(user.get_ticket())

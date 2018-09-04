from django.test import TestCase
from datetime import datetime
from . import factories

from extras import actions
from orders import actions as order_actions


class CreatePendingChildrenTicketOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_order_for_self_individual(self):
        order = actions.create_pending_children_ticket_order(
            purchaser=self.alice,
            billing_details={'name': 'Alice Apple', 'addr': 'Eadrax, Sirius Tau'},
            unconfirmed_details={
                'adult_name': 'Puff The Elder',
                'adult_email_addr': 'puff@example.com',
                'adult_phone_number': '07700 900001',
                'name': 'Puff',
                'age': 10,
                'accessibility_reqs': 'Occasionally breathe fire',
                'dietary_reqs': 'Allergic to Welsh Cakes',
            }
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertIsNone(self.alice.get_ticket())

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.invoice_number, None)
        self.assertEqual(order.billing_name, 'Alice Apple')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')


class UpdatePendingChildrenOrderTests(TestCase):
    def test_order_for_self_to_order_for_self(self):
        order = factories.create_pending_children_ticket_order()
        actions.update_pending_children_ticket_order(
            order,
            billing_details={'name': 'Alice Apple', 'addr': 'Eadrax, Sirius Tau'},
            unconfirmed_details={
                'adult_name': 'Puff The Elder',
                'adult_email_addr': 'puff@example.com',
                'adult_phone_number': '07700 900001',
                'name': 'Puff Jr',
                'age': 10,
                'accessibility_reqs': 'Occasionally breathe fire',
                'dietary_reqs': 'Allergic to Welsh Cakes',
            }
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.invoice_number, None)
        self.assertEqual(order.billing_name, 'Alice Apple')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')

        [row] = order.all_order_rows()

        self.assertEqual(row.cost_excl_vat, 5)
        self.assertEqual(row.item_descr, "Young Coders' day ticket")
        self.assertEqual(row.item_descr_extra, '')

        ticket = row.item
        self.assertEqual(ticket.owner, order.purchaser)
        self.assertEqual(ticket.item.adult_name, 'Puff The Elder')
        self.assertEqual(ticket.item.adult_email_addr, 'puff@example.com')
        self.assertEqual(ticket.item.adult_phone_number, '07700 900001')
        self.assertEqual(ticket.item.name, 'Puff Jr')
        self.assertEqual(ticket.item.age, 10)
        self.assertEqual(ticket.item.accessibility_reqs, 'Occasionally breathe fire')
        self.assertEqual(ticket.item.dietary_reqs, 'Allergic to Welsh Cakes')


class CreatePendingDinnerTicketOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_order_for_self_individual(self):
        order = actions.create_pending_dinner_ticket_order(
            purchaser=self.alice,
            billing_details={'name': 'Alice Apple', 'addr': 'Eadrax, Sirius Tau'},
            unconfirmed_details={
                'dinner': 'CD',
                'starter': 'SESS',
                'main': 'LTAC',
                'dessert': 'ESB',
            }
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertIsNone(self.alice.get_ticket())

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.invoice_number, None)
        self.assertEqual(order.billing_name, 'Alice Apple')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')


class UpdatePendingDinnerOrderTests(TestCase):
    def test_order_for_self_to_order_for_self(self):
        order = factories.create_pending_dinner_ticket_order()
        actions.update_pending_dinner_ticket_order(
            order,
            billing_details={'name': 'Alice Apple', 'addr': 'Eadrax, Sirius Tau'},
            unconfirmed_details={
                'dinner': 'CD',
                'starter': 'SSSE',
                'main': 'SSSS',
                'dessert': 'ENB',
            }
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.invoice_number, None)
        self.assertEqual(order.billing_name, 'Alice Apple')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')

        [row] = order.all_order_rows()

        self.assertEqual(row.cost_excl_vat, 30)
        self.assertEqual(row.item_descr, "Conference Dinner at City Hall on Saturday 15th September dinner ticket")
        self.assertEqual(row.item_descr_extra, '')

        ticket = row.item
        self.assertEqual(ticket.owner, order.purchaser)
        self.assertEqual(ticket.item.dinner, 'CD')
        self.assertEqual(ticket.item.starter, 'SSSE')
        self.assertEqual(ticket.item.main, 'SSSS')
        self.assertEqual(ticket.item.dessert, 'ENB')


class UpdateExistingDinnerTicketTests(TestCase):
    def test_existing_dinner_ticket_can_be_edited(self):
        order = factories.create_pending_dinner_ticket_order()
        order_actions.confirm_order(order, 'id', 12345678)
        [row] = order.all_order_rows()
        ticket = row.item.item

        actions.update_existing_dinner_ticket_order(
            ticket,
            details={
                'dinner': 'CD',
                'starter': 'SSSE',
                'main': 'SSSS',
                'dessert': 'ENB',
            }
        )

        ticket.refresh_from_db()

        self.assertEqual(order.status, 'successful')
        self.assertEqual(order.invoice_number, 1)
        self.assertEqual(order.billing_name, 'Sirius Cybernetics Corp.')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')

        self.assertEqual(row.cost_excl_vat, 30)
        self.assertEqual(row.item_descr, "Conference Dinner at City Hall on Saturday 15th September dinner ticket")
        self.assertEqual(row.item_descr_extra, '')

        self.assertEqual(ticket.dinner, 'CD')
        self.assertEqual(ticket.starter, 'SSSE')
        self.assertEqual(ticket.main, 'SSSS')
        self.assertEqual(ticket.dessert, 'ENB')

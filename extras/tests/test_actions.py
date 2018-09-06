from django.test import TestCase
from . import factories

from extras import actions
from orders import actions as order_actions
from orders.models import OrderRow


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
                'starter': 'HTRP',
                'main': 'RVTT',
                'dessert': 'APS',
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
                'starter': 'RORS',
                'main': 'RSBL',
                'dessert': 'TLT',
            }
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.invoice_number, None)
        self.assertEqual(order.billing_name, 'Alice Apple')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')

        [row] = order.all_order_rows()

        self.assertEqual(row.cost_excl_vat, 34)
        self.assertEqual(row.item_descr, "Conference Dinner at City Hall on Saturday 15th September dinner ticket")
        self.assertEqual(row.item_descr_extra, '')

        ticket = row.item
        self.assertEqual(ticket.owner, order.purchaser)
        self.assertEqual(ticket.item.dinner, 'CD')
        self.assertEqual(ticket.item.starter, 'RORS')
        self.assertEqual(ticket.item.main, 'RSBL')
        self.assertEqual(ticket.item.dessert, 'TLT')


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
                'starter': 'RORS',
                'main': 'RSBL',
                'dessert': 'TLT',
            }
        )

        ticket.refresh_from_db()

        self.assertEqual(order.status, 'successful')
        self.assertEqual(order.invoice_number, 1)
        self.assertEqual(order.billing_name, 'Sirius Cybernetics Corp.')
        self.assertEqual(order.billing_addr, 'Eadrax, Sirius Tau')

        self.assertEqual(row.cost_excl_vat, 34)
        self.assertEqual(row.item_descr, "Conference Dinner at City Hall on Saturday 15th September dinner ticket")
        self.assertEqual(row.item_descr_extra, '')

        self.assertEqual(ticket.dinner, 'CD')
        self.assertEqual(ticket.starter, 'RORS')
        self.assertEqual(ticket.main, 'RSBL')
        self.assertEqual(ticket.dessert, 'TLT')


class CreateFreeDinnerTicketOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_order_fails_if_not_contributor(self):
        self.alice.is_contributor = False
        self.alice.save()

        with self.assertRaises(AssertionError):
            actions.create_free_dinner_ticket_order(
                purchaser=self.alice,
                details={
                    'dinner': 'CD',
                    'starter': 'HTRP',
                    'main': 'RVTT',
                    'dessert': 'APS',
                }
            )

        self.assertEqual(self.alice.orders.count(), 0)
        self.assertEqual(self.alice.extras.count(), 0)
        self.assertIsNone(self.alice.get_ticket())

    def test_order_for_contributor(self):
        self.alice.is_contributor = True
        self.alice.save()

        item = actions.create_free_dinner_ticket_order(
            purchaser=self.alice,
            details={
                'dinner': 'CD',
                'starter': 'HTRP',
                'main': 'RVTT',
                'dessert': 'APS',
            }
        )

        self.assertEqual(self.alice.orders.count(), 0)
        self.assertEqual(self.alice.extras.count(), 1)

        self.assertEqual(item.owner, self.alice)

        with self.assertRaises(OrderRow.DoesNotExist):
            item.order

    def test_order_for_contributor_who_already_has_a_ticket(self):
        self.alice.is_contributor = True
        self.alice.save()

        order = factories.create_pending_dinner_ticket_order(self.alice)
        order_actions.confirm_order(order, 'id', 12345678)

        with self.assertRaises(AssertionError):
            actions.create_free_dinner_ticket_order(
                purchaser=self.alice,
                details={
                    'dinner': 'CD',
                    'starter': 'HTRP',
                    'main': 'RVTT',
                    'dessert': 'APS',
                }
            )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertEqual(self.alice.extras.count(), 1)

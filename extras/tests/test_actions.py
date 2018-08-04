from django.test import TestCase

from . import factories

from extras import actions


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


class UpdatePendingOrderTests(TestCase):
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
        self.assertEqual(row.item_descr, "Children's day ticket")
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

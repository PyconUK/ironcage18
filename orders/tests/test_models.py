from django.test import TestCase

from tickets.tests import factories


class OrderTests(TestCase):
    def test_cost_incl_vat_for_confirmed_order(self):
        order = factories.create_confirmed_order_for_self_and_others()
        self.assertEqual(order.cost_incl_vat, 378)  # 378 == 2 * 114 + 1 * 150

    def test_cost_incl_vat_for_unconfirmed_order(self):
        order = factories.create_pending_order_for_self_and_others()
        self.assertEqual(order.cost_incl_vat, 378)  # 378 == 2 * 114 + 1 * 150

    def test_cost_excl_vat_for_confirmed_order(self):
        order = factories.create_confirmed_order_for_self_and_others()
        self.assertEqual(order.cost_excl_vat, 315)  # 315 == 2 * 95 + 1 * 125

    def test_cost_excl_vat_for_unconfirmed_order(self):
        order = factories.create_pending_order_for_self_and_others()
        self.assertEqual(order.cost_excl_vat, 315)  # 315 == 2 * 95 + 1 * 125

    def test_order_rows_summary(self):
        order = factories.create_confirmed_order_for_self_and_others()
        expected_summary = [{
            'item_descr': '2-day individual-rate ticket',
            'quantity': 2,
            'per_item_cost_excl_vat': 95,
            'per_item_cost_incl_vat': 114,
            'total_cost_excl_vat': 190,
            'total_cost_incl_vat': 228,
        }, {
            'item_descr': '3-day individual-rate ticket',
            'quantity': 1,
            'per_item_cost_excl_vat': 125,
            'per_item_cost_incl_vat': 150,
            'total_cost_excl_vat': 125,
            'total_cost_incl_vat': 150,
        }]
        self.assertEqual(order.order_rows_summary(), expected_summary)

    def test_ticket_for_self_for_order_for_self(self):
        order = factories.create_confirmed_order_for_self()
        self.assertIsNotNone(order.ticket_for_self())

    def test_ticket_for_self_for_order_for_self_and_others(self):
        order = factories.create_confirmed_order_for_self_and_others()
        self.assertIsNotNone(order.ticket_for_self())

    def test_ticket_for_self_for_order_for_others(self):
        order = factories.create_confirmed_order_for_others()
        self.assertIsNone(order.ticket_for_self())

    def test_tickets_for_others_for_order_for_self(self):
        order = factories.create_confirmed_order_for_self()
        self.assertEqual(len(order.tickets_for_others()), 0)

    def test_tickets_for_others_for_order_for_self_and_others(self):
        order = factories.create_confirmed_order_for_self_and_others()
        self.assertEqual(len(order.tickets_for_others()), 2)

    def test_tickets_for_others_for_order_for_others(self):
        order = factories.create_confirmed_order_for_others()
        self.assertEqual(len(order.tickets_for_others()), 2)

    def test_billing_addr_formatted(self):
        order = factories.create_pending_order_for_self(rate='corporate')
        order.billing_addr = '''
City Hall,
Cathays Park
Cardiff
'''.strip()
        self.assertEqual(order.billing_addr_formatted(), 'City Hall, Cathays Park, Cardiff')

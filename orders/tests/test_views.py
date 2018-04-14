from django.test import TestCase

from ironcage.tests import utils
from tickets.tests import factories

from orders import actions


class OrderTests(TestCase):
    def test_for_confirmed_order_for_self(self):
        order = factories.create_confirmed_order_for_self()
        self.client.force_login(order.purchaser)
        rsp = self.client.get(f'/orders/{order.order_id}/', follow=True)
        self.assertContains(rsp, f'Details of your order ({order.order_id})')
        self.assertNotContains(rsp, '<div id="stripe-form">')
        self.assertContains(rsp, 'View your ticket')

        self.assertContains(rsp, '''
        <tr>
            <td>Alice</td>
            <td>3-day individual-rate ticket</td>
            <td>Saturday, Sunday, Monday</td>
            <td>£126</td>
        </tr>
        ''', html=True)

    def test_for_confirmed_order_for_others(self):
        order = factories.create_confirmed_order_for_others()
        self.client.force_login(order.purchaser)
        rsp = self.client.get(f'/orders/{order.order_id}/', follow=True)
        self.assertContains(rsp, f'Details of your order ({order.order_id})')
        self.assertNotContains(rsp, '<div id="stripe-form">')
        self.assertNotContains(rsp, 'View your ticket')

        self.assertContains(rsp, '''
        <tr>
            <td>bob@example.com</td>
            <td>2-day individual-rate ticket</td>
            <td>Sunday, Monday</td>
            <td>£90</td>
        </tr>
        ''', html=True)

        self.assertContains(rsp, '''
        <tr>
            <td>carol@example.com</td>
            <td>2-day individual-rate ticket</td>
            <td>Monday, Tuesday</td>
            <td>£90</td>
        </tr>
        ''', html=True)

    def test_for_confirmed_order_for_self_and_others(self):
        order = factories.create_confirmed_order_for_self_and_others()
        self.client.force_login(order.purchaser)
        rsp = self.client.get(f'/orders/{order.order_id}/', follow=True)
        self.assertContains(rsp, f'Details of your order ({order.order_id})')
        self.assertNotContains(rsp, '<div id="stripe-form">')
        self.assertContains(rsp, 'View your ticket')

        self.assertContains(rsp, '''
        <tr>
            <td>Alice</td>
            <td>3-day individual-rate ticket</td>
            <td>Saturday, Sunday, Monday</td>
            <td>£126</td>
        </tr>
        ''', html=True)

        self.assertContains(rsp, '''
        <tr>
            <td>bob@example.com</td>
            <td>2-day individual-rate ticket</td>
            <td>Sunday, Monday</td>
            <td>£90</td>
        </tr>
        ''', html=True)

        self.assertContains(rsp, '''
        <tr>
            <td>carol@example.com</td>
            <td>2-day individual-rate ticket</td>
            <td>Monday, Tuesday</td>
            <td>£90</td>
        </tr>
        ''', html=True)

    def test_for_partially_refunded_order_for_self_and_others(self):
        order = factories.create_confirmed_order_for_self_and_others()
        ticket = order.all_tickets()[-1]

        with utils.patched_refund_creation():
            actions.refund_item(ticket, 'Refund requested by user')

        self.client.force_login(order.purchaser)
        rsp = self.client.get(f'/orders/{order.order_id}/', follow=True)
        self.assertContains(rsp, f'Details of your order ({order.order_id})')
        self.assertNotContains(rsp, '<div id="stripe-form">')
        self.assertContains(rsp, 'View your ticket')

        self.assertContains(rsp, '''
        <tr>
            <td>Alice</td>
            <td>3-day individual-rate ticket</td>
            <td>Saturday, Sunday, Monday</td>
            <td>£126</td>
        </tr>
        ''', html=True)

        self.assertContains(rsp, '''
        <tr>
            <td>bob@example.com</td>
            <td>2-day individual-rate ticket</td>
            <td>Sunday, Monday</td>
            <td>£90</td>
        </tr>
        ''', html=True)

        self.assertContains(rsp, '''
        <tr>
            <td>Refunded</td>
            <td>2-day individual-rate ticket</td>
            <td>Monday, Tuesday</td>
            <td>£90</td>
        </tr>
        ''', html=True)

    def test_for_pending_order(self):
        user = factories.create_user(email_addr='alice@example.com')
        order = factories.create_pending_order_for_self(user)
        self.client.force_login(user)
        rsp = self.client.get(f'/orders/{order.order_id}/', follow=True)
        self.assertContains(rsp, f'Details of your order ({order.order_id})')
        self.assertContains(rsp, '<div id="stripe-form">')
        self.assertContains(rsp, 'data-amount="12600"')
        self.assertContains(rsp, 'data-email="alice@example.com"')

        self.assertContains(rsp, '''
        <tr>
            <td>Alice</td>
            <td>3-day individual-rate ticket</td>
            <td>Saturday, Sunday, Monday</td>
            <td>£126</td>
        </tr>
        ''', html=True)

    def test_for_pending_order_for_self_when_already_has_ticket(self):
        user = factories.create_user(email_addr='alice@example.com')
        factories.create_confirmed_order_for_self(user)
        order = factories.create_pending_order_for_self(user)
        self.client.force_login(user)
        rsp = self.client.get(f'/orders/{order.order_id}/', follow=True)
        self.assertRedirects(rsp, f'/tickets/orders/{order.order_id}/edit/')
        self.assertContains(rsp, 'You already have a ticket.  Please amend your order.')

    def test_for_failed_order(self):
        order = factories.create_failed_order()
        self.client.force_login(order.purchaser)
        rsp = self.client.get(f'/orders/{order.order_id}/', follow=True)
        self.assertContains(rsp, f'Details of your order ({order.order_id})')
        self.assertContains(rsp, 'Payment for this order failed (Your card was declined.)')
        self.assertContains(rsp, '<div id="stripe-form">')
        self.assertNotContains(rsp, 'View your ticket')

    def test_for_errored_order(self):
        order = factories.create_errored_order()
        self.client.force_login(order.purchaser)
        rsp = self.client.get(f'/orders/{order.order_id}/', follow=True)
        self.assertContains(rsp, f'Details of your order ({order.order_id})')
        self.assertContains(rsp, 'There was an error creating your order')
        self.assertNotContains(rsp, '<div id="stripe-form">')
        self.assertNotContains(rsp, 'View your ticket')

    def test_when_not_authenticated(self):
        order = factories.create_confirmed_order_for_self()
        rsp = self.client.get(f'/orders/{order.order_id}/', follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next=/orders/{order.order_id}/')

    def test_when_not_authorized(self):
        order = factories.create_confirmed_order_for_self()
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.get(f'/orders/{order.order_id}/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can view the order')


class OrderPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.order = factories.create_pending_order_for_self()
        cls.url = f'/orders/{cls.order.order_id}/payment/'

    def test_stripe_success(self):
        self.client.force_login(self.order.purchaser)
        with utils.patched_charge_creation_success():
            rsp = self.client.post(
                self.url,
                {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
                follow=True,
            )
        self.assertContains(rsp, 'Payment for this order has been received')
        self.assertContains(rsp, '<th>Date</th><td>21 May 2018</td>', html=True)
        self.assertNotContains(rsp, '<div id="stripe-form">')

    def test_stripe_failure(self):
        self.client.force_login(self.order.purchaser)
        with utils.patched_charge_creation_failure():
            rsp = self.client.post(
                self.url,
                {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
                follow=True,
            )
        self.assertContains(rsp, 'Payment for this order failed (Your card was declined.)')
        self.assertContains(rsp, '<th>Date</th><td>Unpaid</td>', html=True)
        self.assertContains(rsp, '<div id="stripe-form">')

    def test_when_already_has_ticket(self):
        factories.create_confirmed_order_for_self(self.order.purchaser)
        self.client.force_login(self.order.purchaser)
        rsp = self.client.post(
            self.url,
            {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
            follow=True,
        )
        self.assertRedirects(rsp, f'/tickets/orders/{self.order.order_id}/edit/')
        self.assertContains(rsp, 'You already have a ticket.  Please amend your order.  Your card has not been charged.')

    def test_when_already_paid(self):
        factories.confirm_order(self.order)
        self.client.force_login(self.order.purchaser)
        rsp = self.client.post(
            self.url,
            {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
            follow=True,
        )
        self.assertRedirects(rsp, f'/orders/{self.order.order_id}/')
        self.assertContains(rsp, 'This order has already been paid')

    def test_when_not_authenticated(self):
        rsp = self.client.post(
            self.url,
            {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
            follow=True,
        )
        self.assertRedirects(rsp, f'/accounts/login/?next={self.url}')

    def test_when_not_authorized(self):
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.post(
            self.url,
            {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
            follow=True,
        )
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can pay for the order')


class OrderReceiptTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.order = factories.create_confirmed_order_for_self_and_others()
        cls.url = f'/orders/{cls.order.order_id}/receipt/'

    def test_order_receipt(self):
        self.client.force_login(self.order.purchaser)
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, f'Receipt for PyCon UK 2018 order {self.order.order_id}')
        self.assertContains(rsp, '3 tickets for PyCon UK 2018')
        self.assertContains(rsp, '<th>Date</th><td>21 May 2018</td>', html=True)
        self.assertContains(rsp, '<th>Invoice number</th><td>S-2018-0001</td>', html=True)
        self.assertContains(rsp, '<th>Total (excl. VAT)</th><td>£255</td>', html=True)
        self.assertContains(rsp, '<th>VAT at 20%</th><td>£51</td>', html=True)
        self.assertContains(rsp, '<th>Total (incl. VAT)</th><td>£306</td>', html=True)
        self.assertContains(rsp, '''
            <tr>
                <td>2-day individual-rate ticket</td>
                <td>2</td>
                <td>£75</td>
                <td>£90</td>
                <td>£150</td>
                <td>£180</td>
            </tr>''', html=True)
        self.assertContains(rsp, '''
            <tr>
                <td>3-day individual-rate ticket</td>
                <td>1</td>
                <td>£105</td>
                <td>£126</td>
                <td>£105</td>
                <td>£126</td>
            </tr>''', html=True)
        self.assertContains(rsp, '''
            <tr>
                <th>Total</th>
                <th></th>
                <th></th>
                <th></th>
                <th>£255</th>
                <th>£306</th>
            </tr>''', html=True)

    def test_when_not_authenticated(self):
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next={self.url}')

    def test_when_not_authorized(self):
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can view the receipt')

    def test_when_not_paid(self):
        bob = factories.create_user('Bob')
        order = factories.create_pending_order_for_self(user=bob)
        self.client.force_login(bob)
        rsp = self.client.get(f'/orders/{order.order_id}/receipt/', follow=True)
        self.assertRedirects(rsp, f'/orders/{order.order_id}/')
        self.assertContains(rsp, 'This order has not been paid')


class RefundCreditNoteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.order = factories.create_confirmed_order_for_self_and_others()
        ticket = cls.order.all_tickets()[0]

        with utils.patched_refund_creation():
            actions.refund_item(ticket, 'Refund requested by user')

        cls.refund = cls.order.refunds.get()

        cls.url = f'/orders/{cls.order.order_id}/credit-note/{cls.refund.refund_id}/'

    def test_refund_credit_note(self):
        self.client.force_login(self.order.purchaser)
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, f'Credit note for PyCon UK 2018 order {self.order.order_id}')
        self.assertContains(rsp, '<th>Date</th><td>21 May 2018</td>', html=True)
        self.assertContains(rsp, '<th>Original invoice number</th><td>S-2018-0001</td>', html=True)
        self.assertContains(rsp, '<th>Credit note number</th><td>R-2018-0001-01</td>', html=True)
        self.assertContains(rsp, '<th>Total (excl. VAT)</th><td>£105</td>', html=True)
        self.assertContains(rsp, '<th>VAT at 20%</th><td>£21</td>', html=True)
        self.assertContains(rsp, '<th>Total (incl. VAT)</th><td>£126</td>', html=True)
        self.assertContains(rsp, '''
            <tr>
                <td>3-day individual-rate ticket</td>
                <td>1</td>
                <td>£105</td>
                <td>£126</td>
                <td>£105</td>
                <td>£126</td>
            </tr>''', html=True)
        self.assertContains(rsp, '''
            <tr>
                <th>Total</th>
                <th></th>
                <th></th>
                <th></th>
                <th>£105</th>
                <th>£126</th>
            </tr>''', html=True)

    def test_when_not_authenticated(self):
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next={self.url}')

    def test_when_not_authorized(self):
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can view a credit note')

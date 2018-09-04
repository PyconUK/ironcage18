from datetime import datetime, timedelta, timezone

from django.test import TestCase, override_settings

from . import factories
from extras.models import DINNERS


class NewChildrenTicketOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.url = '/extras/children/orders/new/'

    def test_get(self):
        self.client.force_login(self.alice)
        rsp = self.client.get(self.url)
        self.assertContains(rsp, '<p>Please note that only one ticket can be purchased at a time, but multiple orders can be placed.</p>', html=True)
        self.assertContains(rsp, '<form method="post" id="order-form">')
        self.assertNotContains(rsp, 'to buy a ticket')

    @override_settings(TICKET_SALES_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1))
    def test_get_when_ticket_sales_have_closed(self):
        self.client.force_login(self.alice)
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, 'ticket sales have closed')
        self.assertRedirects(rsp, '/')

    @override_settings(
        TICKET_SALES_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1),
        TICKET_DEADLINE_BYPASS_TOKEN='abc123',
    )
    def test_get_when_ticket_sales_have_closed_but_correct_token_is_provided(self):
        self.client.force_login(self.alice)
        rsp = self.client.get(f'{self.url}?deadline-bypass-token=abc123', follow=True)
        self.assertNotContains(rsp, 'ticket sales have closed')
        self.assertContains(rsp, '<form method="post" id="order-form">')

    @override_settings(
        TICKET_SALES_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1),
        TICKET_DEADLINE_BYPASS_TOKEN='abc123',
    )
    def test_get_when_ticket_sales_have_closed_and_incorrect_token_is_provided(self):
        self.client.force_login(self.alice)
        rsp = self.client.get(f'{self.url}?deadline-bypass-token=321cba', follow=True)
        self.assertContains(rsp, 'ticket sales have closed')
        self.assertRedirects(rsp, '/')

    def test_post(self):
        self.client.force_login(self.alice)
        form_data = {
            'adult_name': 'Puff The Elder',
            'adult_email_addr': 'puff@example.com',
            'adult_phone_number': '07700 900001',
            'name': 'Puff',
            'age': 10,
            'accessibility_reqs': 'Occasionally breathe fire',
            'dietary_reqs': 'Allergic to Welsh Cakes',
            'billing_name': 'Puff Dragon',
            'billing_addr': 'By The Sea, Honalee'
        }
        rsp = self.client.post(self.url, form_data, follow=True)
        self.assertContains(rsp, 'You are ordering 1 item')

    def test_get_when_not_authenticated(self):
        rsp = self.client.get(self.url)
        self.assertContains(rsp, '<p>Please note that only one ticket can be purchased at a time, but multiple orders can be placed.</p>', html=True)
        self.assertNotContains(rsp, '<form method="post" id="order-form">')
        self.assertContains(rsp, 'Please <a href="/accounts/register/?next=/extras/children/orders/new/">sign up</a> or <a href="/accounts/login/?next=/extras/children/orders/new/">sign in</a> to buy a ticket.', html=True)

    def test_post_when_not_authenticated(self):
        rsp = self.client.post(self.url, follow=True)
        self.assertRedirects(rsp, '/accounts/login/')


class ChildrenTicketOrderEditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.order = factories.create_pending_children_ticket_order()
        cls.url = f'/extras/children/orders/{cls.order.order_id}/edit/'

    def test_get(self):
        self.client.force_login(self.order.purchaser)
        rsp = self.client.get(self.url)
        self.assertContains(rsp, '<p>Please note that only one ticket can be purchased at a time, but multiple orders can be placed.</p>', html=True)
        self.assertContains(rsp, '<form method="post" id="order-form">')
        self.assertNotContains(rsp, 'Please create an account to buy a ticket.')

    def test_get_tickets_url_redirects(self):
        self.client.force_login(self.order.purchaser)
        rsp = self.client.get(f'/tickets/orders/{self.order.order_id}/edit/')

        self.assertRedirects(rsp, f'/extras/children/orders/{self.order.order_id}/edit/')

    def test_post_tickets_url_redirects(self):
        self.client.force_login(self.order.purchaser)
        rsp = self.client.post(f'/tickets/orders/{self.order.order_id}/edit/')

        self.assertRedirects(rsp, f'/extras/children/orders/{self.order.order_id}/edit/')

    def test_post(self):
        self.client.force_login(self.order.purchaser)
        form_data = {
            'adult_name': 'Puff The Elder',
            'adult_email_addr': 'puff@example.com',
            'adult_phone_number': '07700 900001',
            'name': 'Puff Jr',
            'age': 10,
            'accessibility_reqs': 'Occasionally breathe fire',
            'dietary_reqs': 'Allergic to Welsh Cakes',
            'billing_name': 'Puff Dragon',
            'billing_addr': 'By The Sea, Honalee'
        }
        rsp = self.client.post(self.url, form_data, follow=True)
        self.assertContains(rsp, 'You are ordering 1 item')

    def test_get_when_not_authenticated(self):
        rsp = self.client.get(self.url)
        self.assertRedirects(rsp, f'/accounts/login/?next={self.url}')

    def test_post_when_not_authenticated(self):
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next={self.url}')

    def test_get_when_not_authorized(self):
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can update the order')

    def test_post_when_not_authorized(self):
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.post(self.url, follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can update the order')

    def test_get_when_already_paid(self):
        factories.confirm_order(self.order)
        self.client.force_login(self.order.purchaser)
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, f'/orders/{self.order.order_id}/')
        self.assertContains(rsp, 'This order has already been paid')


class ChildrenTicketTests(TestCase):
    def test_ticket(self):
        ticket = factories.create_children_ticket()
        self.client.force_login(ticket.owner)
        rsp = self.client.get(f'/extras/children/tickets/', follow=True)
        self.assertContains(rsp, f"Young Coders' Day Ticket ({ticket.item_id})")
        self.assertContains(rsp, 'Cost (incl. VAT)')
        self.assertContains(rsp, 'Your profile is incomplete')
        self.assertContains(rsp, 'Update your profile')
        self.assertContains(rsp, '<p>If you need to change details, please drop an email to <a href="mailto:pyconuk@uk.python.org">pyconuk@uk.python.org</a></p>', html=True)
        self.assertNotContains(rsp, 'Update your ticket')

    def test_multiple_tickets(self):
        bob = factories.create_user('Bob')
        ticket_1 = factories.create_children_ticket(bob)
        ticket_2 = factories.create_children_ticket(bob)
        self.client.force_login(bob)
        rsp = self.client.get(f'/extras/children/tickets/', follow=True)
        self.assertContains(rsp, f"Young Coders' Day Ticket ({ticket_1.item_id})", html=True)
        self.assertContains(rsp, f"Young Coders' Day Ticket ({ticket_2.item_id})", html=True)
        self.assertContains(rsp, 'Cost (incl. VAT)')
        self.assertContains(rsp, 'Your profile is incomplete')
        self.assertContains(rsp, 'Update your profile')
        self.assertContains(rsp, '<p>If you need to change details, please drop an email to <a href="mailto:pyconuk@uk.python.org">pyconuk@uk.python.org</a></p>', html=True)
        self.assertNotContains(rsp, 'Update your ticket')

    def test_when_not_authenticated(self):
        factories.create_children_ticket()
        rsp = self.client.get(f'/extras/children/tickets/', follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next=/extras/children/tickets/')

    def test_when_not_authorized(self):
        factories.create_children_ticket()
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.get(f'/extras/children/tickets/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'You do not have any Young Coders&#39; Day tickets')


class NewDinnerTicketOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.url = '/extras/dinner/orders/new/CL'

    def test_get(self):
        self.client.force_login(self.alice)
        rsp = self.client.get(self.url)
        self.assertContains(rsp, '<p>Please note that only one ticket can be purchased at a time, but multiple orders can be placed.</p>', html=True)
        self.assertContains(rsp, '<form method="post" id="order-form">')
        self.assertNotContains(rsp, 'to buy a ticket')

    @override_settings(TICKET_SALES_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1))
    def test_get_when_ticket_sales_have_closed(self):
        self.client.force_login(self.alice)
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, 'ticket sales have closed')
        self.assertRedirects(rsp, '/')

    @override_settings(
        TICKET_SALES_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1),
        TICKET_DEADLINE_BYPASS_TOKEN='abc123',
    )
    def test_get_when_ticket_sales_have_closed_but_correct_token_is_provided(self):
        self.client.force_login(self.alice)
        rsp = self.client.get(f'{self.url}?deadline-bypass-token=abc123', follow=True)
        self.assertNotContains(rsp, 'ticket sales have closed')
        self.assertContains(rsp, '<form method="post" id="order-form">')

    @override_settings(
        TICKET_SALES_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1),
        TICKET_DEADLINE_BYPASS_TOKEN='abc123',
    )
    def test_get_when_ticket_sales_have_closed_and_incorrect_token_is_provided(self):
        self.client.force_login(self.alice)
        rsp = self.client.get(f'{self.url}?deadline-bypass-token=321cba', follow=True)
        self.assertContains(rsp, 'ticket sales have closed')
        self.assertRedirects(rsp, '/')

    def test_post(self):
        self.client.force_login(self.alice)
        form_data = {
            'dinner': 'CLSA',
            'starter': 'ESB',
            'main': 'EBS',
            'dessert': 'SBSS',
            'billing_name': 'Puff Dragon',
            'billing_addr': 'By The Sea, Honalee',
        }
        rsp = self.client.post(self.url, form_data, follow=True)

        self.assertContains(rsp, 'You are ordering 1 item')

    def test_get_when_not_authenticated(self):
        rsp = self.client.get(self.url)
        self.assertContains(rsp, '<p>Please note that only one ticket can be purchased at a time, but multiple orders can be placed.</p>', html=True)
        self.assertNotContains(rsp, '<form method="post" id="order-form">')
        self.assertContains(rsp, 'Please <a href="/accounts/register/?next=/extras/dinner/orders/new/CL">sign up</a> or <a href="/accounts/login/?next=/extras/dinner/orders/new/CL">sign in</a> to buy a ticket.', html=True)

    def test_post_when_not_authenticated(self):
        rsp = self.client.post(self.url, follow=True)
        self.assertRedirects(rsp, '/accounts/login/')

    def test_post_when_sold_out(self):
        # Arrange
        DINNERS['CLSA']['capacity'] = 5
        for i in range(5):
            factories.create_clink_dinner_ticket()

        self.client.force_login(self.alice)

        form_data = {
            'dinner': 'CLSA',
            'starter': 'ESB',
            'main': 'EBS',
            'dessert': 'SBSS',
            'billing_name': 'Puff Dragon',
            'billing_addr': 'By The Sea, Honalee',
        }

        # Act
        rsp = self.client.post(self.url, form_data, follow=True)

        # Assert
        self.assertContains(rsp, 'Dinner tickets are not available for the selected dinner')
        self.assertNotContains(rsp, 'You are ordering 1 item')

        DINNERS['CLSU']['capacity'] = 45

    def test_post_when_after_date(self):
        # Arrange
        DINNERS['CLSA']['date'] = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')

        self.client.force_login(self.alice)

        form_data = {
            'dinner': 'CLSA',
            'starter': 'ESB',
            'main': 'EBS',
            'dessert': 'SBSS',
            'billing_name': 'Puff Dragon',
            'billing_addr': 'By The Sea, Honalee',
        }

        # Act
        rsp = self.client.post(self.url, form_data, follow=True)

        # Assert
        self.assertContains(rsp, 'Dinner tickets are not available for the selected dinner')
        self.assertNotContains(rsp, 'You are ordering 1 item')

        DINNERS['CLSU']['date'] = '2018-09-16'


class DinnerTicketOrderEditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.order = factories.create_pending_dinner_ticket_order()
        cls.url = f'/extras/dinner/orders/{cls.order.order_id}/edit/'

    def test_get(self):
        self.client.force_login(self.order.purchaser)
        rsp = self.client.get(self.url)
        self.assertContains(rsp, '<p>Please note that only one ticket can be purchased at a time, but multiple orders can be placed.</p>', html=True)
        self.assertContains(rsp, '<form method="post" id="order-form">')
        self.assertNotContains(rsp, 'Please create an account to buy a ticket.')

    def test_get_tickets_url_redirects(self):
        self.client.force_login(self.order.purchaser)
        rsp = self.client.get(f'/tickets/orders/{self.order.order_id}/edit/')

        self.assertRedirects(rsp, f'/extras/dinner/orders/{self.order.order_id}/edit/')

    def test_post_tickets_url_redirects(self):
        self.client.force_login(self.order.purchaser)
        rsp = self.client.post(f'/tickets/orders/{self.order.order_id}/edit/')

        self.assertRedirects(rsp, f'/extras/dinner/orders/{self.order.order_id}/edit/')

    def test_post(self):
        self.client.force_login(self.order.purchaser)
        form_data = {
            'dinner': 'CLSU',
            'starter': 'ESB',
            'main': 'EBS',
            'dessert': 'SBSS',
            'billing_name': 'Puff Dragon',
            'billing_addr': 'By The Sea, Honalee',
        }
        rsp = self.client.post(self.url, form_data, follow=True)
        self.assertContains(rsp, 'You are ordering 1 item')

    def test_get_when_not_authenticated(self):
        rsp = self.client.get(self.url)
        self.assertRedirects(rsp, f'/accounts/login/?next={self.url}')

    def test_post_when_not_authenticated(self):
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next={self.url}')

    def test_get_when_not_authorized(self):
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can update the order')

    def test_post_when_not_authorized(self):
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.post(self.url, follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can update the order')

    def test_get_when_already_paid(self):
        factories.confirm_order(self.order)
        self.client.force_login(self.order.purchaser)
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, f'/orders/{self.order.order_id}/')
        self.assertContains(rsp, 'This order has already been paid')

    def test_post_when_sold_out(self):
        DINNERS['CLSU']['capacity'] = 0
        self.client.force_login(self.order.purchaser)
        form_data = {
            'dinner': 'CLSU',
            'starter': 'ESB',
            'main': 'EBS',
            'dessert': 'SBSS',
            'billing_name': 'Puff Dragon',
            'billing_addr': 'By The Sea, Honalee',
        }
        rsp = self.client.post(self.url, form_data, follow=True)
        self.assertContains(rsp, 'Dinner tickets are not available for the selected dinner')
        self.assertNotContains(rsp, 'You are ordering 1 item')
        DINNERS['CLSU']['capacity'] = 45

    def test_post_when_after_date(self):
        DINNERS['CLSU']['date'] = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
        self.client.force_login(self.order.purchaser)
        form_data = {
            'dinner': 'CLSU',
            'starter': 'ESB',
            'main': 'EBS',
            'dessert': 'SBSS',
            'billing_name': 'Puff Dragon',
            'billing_addr': 'By The Sea, Honalee',
        }
        rsp = self.client.post(self.url, form_data, follow=True)
        self.assertContains(rsp, 'Dinner tickets are not available for the selected dinner')
        self.assertNotContains(rsp, 'You are ordering 1 item')
        DINNERS['CLSU']['date'] = '2018-09-16'


class DinnerTicketTests(TestCase):
    def test_ticket(self):
        ticket = factories.create_dinner_ticket()
        self.client.force_login(ticket.owner)
        rsp = self.client.get(f'/extras/dinner/tickets/', follow=True)
        self.assertContains(rsp, f"Dinner Ticket ({ticket.item_id})")
        self.assertContains(rsp, 'Cost (incl. VAT)')
        self.assertContains(rsp, 'Your profile is incomplete')
        self.assertContains(rsp, 'Update your profile')
        self.assertNotContains(rsp, '<p>If you need to change details, please drop an email to <a href="mailto:pyconuk@uk.python.org">pyconuk@uk.python.org</a></p>', html=True)
        self.assertContains(rsp, 'Update your ticket')

    def test_multiple_tickets(self):
        bob = factories.create_user('Bob')
        ticket_1 = factories.create_dinner_ticket(bob)
        ticket_2 = factories.create_dinner_ticket(bob)
        self.client.force_login(bob)
        rsp = self.client.get(f'/extras/dinner/tickets/', follow=True)

        self.assertContains(rsp, f"Dinner Ticket ({ticket_1.item_id})", html=True)
        self.assertContains(rsp, f"Dinner Ticket ({ticket_2.item_id})", html=True)
        self.assertContains(rsp, 'Cost (incl. VAT)')
        self.assertContains(rsp, 'Your profile is incomplete')
        self.assertContains(rsp, 'Update your profile')
        self.assertNotContains(rsp, '<p>If you need to change details, please drop an email to <a href="mailto:pyconuk@uk.python.org">pyconuk@uk.python.org</a></p>', html=True)
        self.assertContains(rsp, 'Update your ticket')

    def test_when_not_authenticated(self):
        factories.create_dinner_ticket()
        rsp = self.client.get(f'/extras/dinner/tickets/', follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next=/extras/dinner/tickets/')

    def test_when_not_authorized(self):
        factories.create_dinner_ticket()
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.get(f'/extras/dinner/tickets/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'You do not have any dinner tickets')


class DinnerTicketEditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ticket = factories.create_dinner_ticket()
        cls.clink_ticket = factories.create_clink_dinner_ticket()
        cls.url = f'/extras/dinner/tickets/{cls.ticket.item_id}/edit/'
        cls.clink_url = f'/extras/dinner/tickets/{cls.clink_ticket.item_id}/edit/'

    def test_get(self):
        self.client.force_login(self.ticket.order.purchaser)
        rsp = self.client.get(self.url)
        self.assertContains(rsp, '<p>Please note that only one ticket can be purchased at a time, but multiple orders can be placed.</p>', html=True)
        self.assertContains(rsp, '<form method="post" id="order-form">')
        self.assertNotContains(rsp, 'Please create an account to buy a ticket.')

    def test_post(self):
        self.client.force_login(self.ticket.order.purchaser)
        form_data = {
            'dinner': 'CD',
            'starter': 'SSSE',
            'main': 'LTAC',
            'dessert': 'ESB',
        }
        rsp = self.client.post(self.url, form_data, follow=True)

        self.assertContains(rsp, 'Your dinner ticket has been updated.')

    def test_post_update_dinner_to_different_location(self):
        self.client.force_login(self.ticket.order.purchaser)
        form_data = {
            'dinner': 'CLSU',
            'starter': 'ESB',
            'main': 'EBS',
            'dessert': 'SBSS',
        }
        rsp = self.client.post(self.url, form_data, follow=True)

        self.assertContains(rsp, 'You cannot change location on your dinner ticket')

    def test_post_update_dinner_to_different_clink_day(self):
        self.client.force_login(self.clink_ticket.order.purchaser)
        form_data = {
            'dinner': 'CLSU',
            'starter': 'ESB',
            'main': 'EBS',
            'dessert': 'SBSS',
        }
        rsp = self.client.post(self.clink_url, form_data, follow=True)

        self.assertContains(rsp, 'Your dinner ticket has been updated.')

    def test_post_cant_have_clink_meal_at_city_hall(self):
        self.client.force_login(self.ticket.order.purchaser)
        form_data = {
            'dinner': 'CD',
            'starter': 'ESB',
            'main': 'LTAC',
            'dessert': 'ESB',
        }
        rsp = self.client.post(self.url, form_data, follow=True)

        self.assertContains(rsp, 'There was an error updating your dinner ticket.')

    def test_get_when_not_authenticated(self):
        rsp = self.client.get(self.url)
        self.assertRedirects(rsp, f'/accounts/login/?next={self.url}')

    def test_post_when_not_authenticated(self):
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next={self.url}')

    def test_get_when_not_authorized(self):
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can update the order')

    def test_post_when_not_authorized(self):
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.post(self.url, follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can update the order')

    def test_post_when_sold_out(self):
        # Arrange
        DINNERS['CLSU']['capacity'] = 0

        self.client.force_login(self.clink_ticket.order.purchaser)

        form_data = {
            'dinner': 'CLSU',
            'starter': 'ESB',
            'main': 'EBS',
            'dessert': 'SBSS',
            'billing_name': 'Puff Dragon',
            'billing_addr': 'By The Sea, Honalee',
        }

        # Act
        rsp = self.client.post(self.clink_url, form_data, follow=True)

        # Assert
        self.assertContains(rsp, 'Dinner tickets are not available for the selected dinner')
        self.assertNotContains(rsp, 'Your dinner ticket has been updated.')

        DINNERS['CLSU']['capacity'] = 45

    def test_post_when_after_date(self):
        # Arrange
        DINNERS['CLSU']['date'] = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')

        self.client.force_login(self.clink_ticket.order.purchaser)

        form_data = {
            'dinner': 'CLSU',
            'starter': 'ESB',
            'main': 'EBS',
            'dessert': 'SBSS',
            'billing_name': 'Puff Dragon',
            'billing_addr': 'By The Sea, Honalee',
        }

        # Act
        rsp = self.client.post(self.clink_url, form_data, follow=True)

        # Assert
        self.assertContains(rsp, 'Dinner tickets are not available for the selected dinner')
        self.assertNotContains(rsp, 'Your dinner ticket has been updated.')

        DINNERS['CLSU']['date'] = '2018-09-16'

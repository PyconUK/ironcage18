from django.test import TestCase

from accounts.models import User


class UserTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email_addr='alice@example.com',
            first_name='Alice',
            password='secret',
        )

        self.assertEqual(user.email_addr, 'alice@example.com')
        self.assertTrue(user.check_password('secret'))
        self.assertEqual(user.first_name, 'Alice')

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email_addr='alice@example.com',
            first_name='Alice',
            password='secret',
        )

        self.assertEqual(user.email_addr, 'alice@example.com')
        self.assertTrue(user.check_password('secret'))
        self.assertEqual(user.first_name, 'Alice')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

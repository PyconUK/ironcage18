from django.test import TestCase


class MiddlewareTests(TestCase):
    def test_trace(self):
        rsp = self.client.trace('/')
        self.assertEqual(rsp.status_code, 405)

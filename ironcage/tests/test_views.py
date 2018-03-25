from django.test import TestCase


class IndexTests(TestCase):
    def test_get_index(self):
        rsp = self.client.get('/')
        self.assertContains(rsp, 'Welcome to the PyCon UK 2018 conference HQ.', html=True)

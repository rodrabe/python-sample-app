
import unittest

from falcon.testing import helpers

from jumpgate import api


class TestRequest(unittest.TestCase):
    def test_sl_client(self):
        # Jumpgate request has an sl_client property.
        env = helpers.create_environ()
        r = api.Request(env)
        self.assertIsNone(r.sl_client)
        r.sl_client = 'fake_client'
        self.assertEqual('fake_client', r.sl_client)

    def test_sl_client_init(self):
        # The sl_client can be set on init.
        env = helpers.create_environ()
        r = api.Request(env, sl_client='fake_client')
        self.assertEqual('fake_client', r.sl_client)

    def test_get_user_id(self):
        env = helpers.create_environ()
        r = api.Request(env)
        r.env['auth'] = {'user_id': 'fake_user_id'}
        self.assertIs(r.env['auth']['user_id'], r.user_id)

    def test_set_user_id(self):
        env = helpers.create_environ()
        r = api.Request(env)
        r.user_id = 'fake_user_id'
        self.assertIs(r.env['auth']['user_id'], r.user_id)

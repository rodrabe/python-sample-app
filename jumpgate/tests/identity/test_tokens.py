
import datetime
import json
import os
import unittest

import falcon
from falcon.testing import helpers
import mock

from jumpgate import api
from jumpgate.common.sl import auth
from jumpgate.identity.drivers.sl import tokens


EXPIRES_RE = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'
ISSUED_AT_RE = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z'


class TestTokens(unittest.TestCase):
    @mock.patch('SoftLayer.Client')
    def test_issue_token_using_api_key(self, sl_client_constructor):
        # A user can get a token using v2 using an API key.

        user_id = 123456
        username = 'fake_username'
        account_id = 789012

        # Set up a mock of the SoftLayer.Client that simulates the response
        # when validating an API key and getting authorized user info.
        fake_sl_client = mock.MagicMock()
        fake_user = {
            'id': user_id,
            'username': username,
            'accountId': account_id
        }
        fake_sl_client['Account'].getCurrentUser.return_value = fake_user
        sl_client_constructor.return_value = fake_sl_client

        templates_filename = os.path.join(
            os.path.dirname(__file__), '../identity.templates')

        # password needs to be 64 chars to be interpreted as an API key
        fake_api_key = (
            '1234567891023456789202345678930234567894023456789502345678960234')

        # This is the normal identity v2 auth request body.
        post_data = {
            'auth': {
                'passwordCredentials': {
                    'username': username,
                    'password': fake_api_key,
                },
                'tenantId': str(account_id),
            },
        }

        env = helpers.create_environ(body=json.dumps(post_data))
        req = api.Request(env)
        resp = falcon.Response()
        tokens.TokensV2(templates_filename).on_post(req, resp)

        self.assertEqual(200, resp.status)

        self.assertRegexpMatches(
            resp.body['access']['token']['expires'], EXPIRES_RE)
        self.assertRegexpMatches(
            resp.body['access']['token']['issued_at'], ISSUED_AT_RE)

        epoch = datetime.datetime.utcfromtimestamp(0)

        issued_time = datetime.datetime.strptime(
            resp.body['access']['token']['issued_at'], '%Y-%m-%dT%H:%M:%S.%fZ')

        exp_expires_time = (
            issued_time + datetime.timedelta(seconds=auth.TOKEN_LIFETIME_SEC))
        exp_expires_time = (exp_expires_time - epoch).total_seconds()

        expires_time = datetime.datetime.strptime(
            resp.body['access']['token']['expires'], '%Y-%m-%dT%H:%M:%SZ')
        expires_time = (expires_time - epoch).total_seconds()

        self.assertAlmostEqual(expires_time, exp_expires_time, delta=1)

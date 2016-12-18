
import datetime
import json
import os.path
import unittest

import falcon
from falcon.testing import helpers
import mock
from mock import MagicMock
from mock import patch

from jumpgate.common.exceptions import InvalidTokenError
from jumpgate.common.exceptions import Unauthorized
from jumpgate.common.sl import auth
from jumpgate.identity.drivers.sl import auth_tokens_v3
from jumpgate.identity.drivers.sl.tokens import FakeTokenIdDriver
from jumpgate.identity.drivers.sl.tokens import NoAuthDriver
from jumpgate.identity.drivers.sl.tokens import SLAuthDriver


TOKEN_TIMESTAMP_RE = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z'


class TestAuthTokensV3(unittest.TestCase):
    @patch('SoftLayer.Client')
    def test_create_token_by_api_key(self, sl_client_constructor):
        user_id = 123456
        username = 'fake_username'
        account_id = 789012

        # Set up a mock of the SoftLayer.Client that simulates the response
        # when validating an API key and getting authorized user info.
        fake_sl_client = MagicMock()
        fake_user = {
            'id': user_id,
            'username': username,
            'accountId': account_id
        }
        fake_sl_client['Account'].getCurrentUser.return_value = fake_user
        sl_client_constructor.return_value = fake_sl_client

        # password needs to be 64 chars to be interpreted as an API key
        fake_api_key = (
            '1234567891023456789202345678930234567894023456789502345678960234')

        # This is the normal identity v3 auth request body.
        post_data = {
            'auth': {
                'identity': {
                    'methods': ['password'],
                    'password': {
                        'user': {
                            'name': username,
                            'domain': {'name': 'Default'},
                            'password': fake_api_key,
                        },
                    },
                },
                'scope': {
                    'project': {
                        'name': str(account_id),
                        'domain': {'name': 'Default'},
                    },
                },
            },
        }

        templates_filename = os.path.join(
            os.path.dirname(__file__), '../identity_v3.templates')
        env = helpers.create_environ(body=json.dumps(post_data))
        req = falcon.Request(env)
        resp = falcon.Response()
        auth_tokens_v3.AuthTokensV3(templates_filename).on_post(req, resp)

        # Ensure that SoftLayer.Client was called with the passed-in username
        # and api key as the api_key.
        sl_client_constructor.assert_called_once_with(
            username=username, api_key=fake_api_key, endpoint_url=mock.ANY,
            proxy=mock.ANY
        )

        self.assertEqual(201, resp.status)
        exp_user = {
            'name': username,
            'id': str(user_id),
            'links': [0],
            'domain': {
                'name': 'Default',
                'id': 'default',
                'links': [0],
            },
        }
        self.assertEqual(exp_user, resp.body['token']['user'])
        exp_project = {
            'name': str(account_id),
            'id': str(account_id),
            'links': [0],
            'domain': {
                'name': 'Default',
                'id': 'default',
                'links': [0],
            }
        }
        self.assertEqual(exp_project, resp.body['token']['project'])
        self.assertEqual(['password'], resp.body['token']['methods'])
        self.assertRegexpMatches(
            resp.body['token']['issued_at'], TOKEN_TIMESTAMP_RE)
        self.assertRegexpMatches(
            resp.body['token']['expires_at'], TOKEN_TIMESTAMP_RE)

        issued_time = datetime.datetime.strptime(
            resp.body['token']['issued_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        expires_time = datetime.datetime.strptime(
            resp.body['token']['expires_at'], '%Y-%m-%dT%H:%M:%S.%fZ')

        exp_expires_time = (
            issued_time + datetime.timedelta(seconds=auth.TOKEN_LIFETIME_SEC))
        self.assertEqual(expires_time, exp_expires_time)

    @patch('SoftLayer.Client')
    def _get_token(self, sl_client_constructor):
        # Gets a valid token.
        user_id = 123456
        username = 'fake_username'
        account_id = 789012

        # Set up a mock of the SoftLayer.Client that simulates the response
        # when validating an API key and getting authorized user info.
        fake_sl_client = MagicMock()
        fake_user = {
            'id': user_id,
            'username': username,
            'accountId': account_id
        }
        fake_sl_client['Account'].getCurrentUser.return_value = fake_user
        sl_client_constructor.return_value = fake_sl_client

        # password needs to be 64 chars to be interpreted as an API key
        fake_api_key = (
            '1234567891023456789202345678930234567894023456789502345678960234')

        # This is the normal identity v3 auth request body.
        post_data = {
            'auth': {
                'identity': {
                    'methods': ['password'],
                    'password': {
                        'user': {
                            'name': username,
                            'domain': {'name': 'Default'},
                            'password': fake_api_key,
                        },
                    },
                },
                'scope': {
                    'project': {
                        'name': str(account_id),
                        'domain': {'name': 'Default'},
                    },
                },
            },
        }

        templates_filename = os.path.join(
            os.path.dirname(__file__), '../identity_v3.templates')
        env = helpers.create_environ(body=json.dumps(post_data))
        req = falcon.Request(env)
        resp = falcon.Response()
        auth_tokens_v3.AuthTokensV3(templates_filename).on_post(req, resp)
        return resp.body['token']['id']

    def test_validate(self):
        # A user can get a token and validate that token.
        token_id = self._get_token()

        templates_filename = os.path.join(
            os.path.dirname(__file__), '../identity_v3.templates')
        headers = {
            'X-Auth-Token': token_id, 'X-Subject-Token': token_id,
        }
        env = helpers.create_environ(headers=headers)
        req = falcon.Request(env)
        resp = falcon.Response()
        auth_tokens_v3.AuthTokensV3(templates_filename).on_get(req, resp)
        self.assertEqual(200, resp.status)


class TestNoAuthDriver(unittest.TestCase):

    def setUp(self):
        self.creds = MagicMock()
        self.instance = NoAuthDriver()

    @patch('SoftLayer.Client')
    def test_authenticate(self, mockSLClient):
        mockAccount = MagicMock()
        mockAccount.getCurrentUser.return_value = 'testuser'
        mockSLClient.return_value = {'Account': mockAccount}

        result = self.instance.authenticate(self.creds)
        self.assertEqual(result['user'], 'testuser')


class TestFakeTokenIdDriver(unittest.TestCase):

    def setUp(self):
        self.token_id = MagicMock()
        self.instance = FakeTokenIdDriver()

    @patch('jumpgate.identity.drivers.core')
    def test_invalid_auth_driver(self, mockIdentity):
        mockIdentity.auth_driver.return_value = SLAuthDriver()
        with self.assertRaises(InvalidTokenError):
            self.instance.token_from_id(self.token_id)

    @patch('jumpgate.identity.drivers.core')
    @patch('jumpgate.identity.drivers.sl.tokens.NoAuthDriver')
    def test_auth_failed(self, mockIdentity, mockNoAuthDriver):
        mockIdentity.auth_driver.return_value = mockNoAuthDriver
        mockNoAuthDriver.authenticate.return_value = None
        with self.assertRaises(Unauthorized):
            self.instance.token_from_id(self.token_id)

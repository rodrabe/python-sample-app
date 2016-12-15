from falcon.testing import helpers
from mock import MagicMock
from mock import patch
import unittest

import jumpgate.api
from jumpgate.common.exceptions import InvalidTokenError
from jumpgate.common.hooks.admin_token import admin_token
from jumpgate.common.hooks.auth_token import validate_token
from jumpgate.common.hooks.core import hook_format
from jumpgate.common.hooks.core import hook_set_uuid
from jumpgate.common.hooks.log import log_request
from jumpgate.common.hooks.log import log_response


class TestHookFormat(unittest.TestCase):
    def test_format(self):
        req = MagicMock()
        resp = MagicMock()
        resp.body = {"example": "JSON"}
        resp.content_type = None

        hook_format(req, resp)

        resp.body = '{"example": "JSON"}'
        resp.content_type = 'application/json'

    def test_format_int_status(self):
        req = MagicMock()
        resp = MagicMock()
        resp.status = 200

        hook_format(req, resp)

        self.assertEqual(resp.status, '200 OK')

    def test_format_request_id(self):
        req = MagicMock()
        req.env = {'REQUEST_ID': '123456'}
        resp = MagicMock()

        hook_format(req, resp)

        resp.set_header.assert_called_with('X-Compute-Request-Id', '123456')


class TestHookLogRequest(unittest.TestCase):
    @patch('jumpgate.common.hooks.log.LOG')
    def test_log_request(self, log):
        req = MagicMock()
        req.method = 'GET'
        req.path = '/'
        req.query_string = 'something=value'
        req.env = {'REQUEST_ID': '123456'}
        resp = MagicMock()
        resp.status = '200 OK'
        log_request(req, resp, {'key': 'value'})

        log.info.assert_called_with(
            'REQ: %s %s %s %s [ReqId: %s]',
            'GET', '/', 'something=value', {'key': 'value'}, '123456')


class TestHookLogResponse(unittest.TestCase):
    @patch('jumpgate.common.hooks.log.LOG')
    def test_log_response(self, log):
        req = MagicMock()
        req.method = 'GET'
        req.path = '/'
        req.query_string = 'something=value'
        req.env = {'REQUEST_ID': '123456'}
        resp = MagicMock()
        resp.status = '200 OK'
        log_response(req, resp)

        log.info.assert_called_with(
            'RESP: %s %s %s %s [ReqId: %s]',
            'GET', '/', 'something=value', '200 OK', '123456')


class TestHookSetUUID(unittest.TestCase):
    def test_set_uuid(self):
        req = MagicMock()
        resp = MagicMock()
        req.env = {}

        hook_set_uuid(req, resp, {})

        self.assertEqual(len(req.env), 1)
        self.assertEqual(list(req.env.keys()), ['REQUEST_ID'])
        self.assertIsNotNone(req.env['REQUEST_ID'])
        self.assertTrue(req.env['REQUEST_ID'].startswith('req-'))


class TestHookAdminToken(unittest.TestCase):
    @patch('oslo_config.cfg')
    def test_admin_token(self, cfg):
        req = MagicMock()
        req.headers = {'X-AUTH-TOKEN': 'ADMIN'}
        resp = MagicMock()
        cfg.CONF = {'DEFAULT': {'admin_token': 'ADMIN'}}

        admin_token(req, resp, {})
        self.assertTrue(req.env['is_admin'])

        req.headers = {'X-AUTH-TOKEN': 'ABC'}
        req.env = {}
        admin_token(req, resp, {})
        self.assertIsNone(req.env.get('is_admin'))


class TestHookAuthToken(unittest.TestCase):

    def test_unprotected(self):
        for api in ['GET:/v2', 'GET:/v2/', 'GET:/v3.0', 'GET:/v3.0/',
                    'GET:/v10.22', 'POST:/v2.0/tokens', 'POST:/v2.1/tokens',
                    'GET:/v2/tokens/a8Vs7bS', 'GET:/v2.0/tokens/a8Vs7bS',
                    'POST:/v3/auth/tokens',
                    # Test listing compute API versions with and without a
                    # trailing slash on the endpoint URL.
                    'GET:/compute/',
                    'GET:/compute']:
            req = MagicMock()
            req.headers = {'X-AUTH-TOKEN': None}
            req.method = api.split(':')[0]
            req.path = api.split(':')[1]
            req.env = {}
            resp = MagicMock()
            validate_token(req, resp, {})
            self.assertIsNone(req.env.get('auth'))

    def test_upstream_admin(self):
        req = MagicMock()
        req.headers = {}
        req.method = 'GET'
        req.path = '/v2/servers'
        req.env = {'is_admin': True}
        resp = MagicMock()
        validate_token(req, resp, {})
        self.assertIsNone(req.env.get('auth'))

    def test_upstream_xauth(self):
        req = MagicMock()
        req.headers = {}
        req.method = 'GET'
        req.path = '/v2/servers'
        req.env = {'REMOTE_USER': 'jsmith'}
        resp = MagicMock()
        validate_token(req, resp, {})
        self.assertIsNone(req.env.get('auth'))

    def test_upstream_preauth(self):
        req = MagicMock()
        auth = {'user': 'jsmith'}
        req.headers = {}
        req.method = 'GET'
        req.path = '/v2/servers'
        req.env = {'auth': auth}
        resp = MagicMock()
        validate_token(req, resp, {})
        self.assertEqual(req.env.get('auth'), auth)

    def test_invalid_auth(self):
        req = MagicMock()
        req.headers = {'X-AUTH-TOKEN': 'IAMBAD'}
        req.method = 'GET'
        req.path = '/v2/servers'
        req.env = {}
        resp = MagicMock()
        with self.assertRaises(InvalidTokenError):
            validate_token(req, resp, {})
        self.assertIsNone(req.env.get('auth'))

    @patch('jumpgate.common.hooks.auth_token.identity')
    def test_valid_auth(self, identity):
        client = MagicMock()
        env = helpers.create_environ(headers={'X-AUTH-TOKEN': 'AUTHTOK',
                                              'X-AUTH-PROJECT-ID': 'public'})

        req = jumpgate.api.Request(env, sl_client=client)
        req.method = 'GET'
        req.path = '/v2/servers'
        resp = MagicMock()

        token = {
            'username': 'test-sl',
            'auth_type': 'api_key',
            'user_id': '1234567',
            'tenant_id': '123456',
            'expires': 1234567891.123456,
            'api_key': '123456789123456789123456789123456789123456789123456789'
        }

        def mock_validate(tok, tenant_id=None):
            self.assertEqual('AUTHTOK', tok)
            self.assertEqual('public', tenant_id)

        class MockIdDriver(object):
            def token_from_id(self, tok):
                return token

        identity.validate_token_id = mock_validate
        identity.token_id_driver.return_value = MockIdDriver()
        validate_token(req, resp, {'X-AUTH-PROJECT-ID': 'public'})
        self.assertEqual(req.env.get('auth'), token)
        self.assertEqual('1234567', req.user_id)

import base64
import datetime
import json
import logging

from jumpgate.common import aes
from jumpgate.common.sl import auth
from jumpgate.identity.drivers import core as identity

LOG = logging.getLogger(__name__)


def parse_templates(template_lines):
    o = {}
    for line in template_lines:
        if ' = ' not in line:
            continue

        k, v = line.strip().split(' = ')
        if not k.startswith('catalog.'):
            continue

        parts = k.split('.')

        region, service, key = parts[1:4]

        region_ref = o.get(region, {})
        service_ref = region_ref.get(service, {})
        service_ref[key] = v

        region_ref[service] = service_ref
        o[region] = region_ref

    return o


def get_access_v3(token_id, token_details, user_id, user_name):
    issued_at = token_details['expires'] - auth.TOKEN_LIFETIME_SEC
    return {
        'token': {
            'expires_at': datetime.datetime.fromtimestamp(
                token_details['expires']).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'issued_at': datetime.datetime.fromtimestamp(
                issued_at).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'methods': ['password'],
            'id': token_id,
            'project': {
                'id': token_details['tenant_id'],
                'links': [0],
                'name': token_details['tenant_id'],
                'domain': {
                    'id': 'default',
                    'links': [0],
                    'name': 'Default'}
            },
            'user': {
                'id': str(user_id),
                'links': [0],
                'name': user_name,
                'domain': {
                    'id': 'default',
                    'links': [0],
                    'name': 'Default'}
            }
        }
    }


class AuthTokensV3(object):
    def __init__(self, template_file):
        self._load_templates(template_file)

    def _load_templates(self, template_file):
        try:
            self.templates = parse_templates(open(os.path.join('/opt/app-root/src/jumpgate', template_file)))
        except IOError:
            LOG.critical('Unable to open template file %s', template_file)
            raise

    def _get_catalog(self, tenant_id, user_id):
        d = {'tenant_id': tenant_id, 'user_id': user_id}

        o = {}
        for region, region_ref in self.templates.items():
            o[region] = {}
            for service, service_ref in region_ref.items():
                o[region][service] = {}
                for k, v in service_ref.items():
                    o[region][service][k] = v.replace('$(', '%(') % d
        return o

    def _build_catalog(self, token_details, user_id):
        raw_catalog = self._get_catalog(token_details['tenant_id'], user_id)
        catalog = []
        for services in raw_catalog.values():
            for service_type, service in services.items():
                d = {
                    # 'id': "????"
                    'type': service_type,
                    'name': service.get('name', 'Unknown'),
                    'endpoints': [{
                        # 'id': "????"
                        'interface': "internal",
                        'region': service.get('region', 'RegionOne'),
                        'url': service.get('internalURL')
                    }, {
                        # 'id': "????"
                        'interface': "public",
                        'region': service.get('region', 'RegionOne'),
                        'url': service.get('publicURL')
                    }, {
                        # 'id': "????"
                        'interface': "admin",
                        'region': service.get('region', 'RegionOne'),
                        'url': service.get('adminURL'),
                    }]
                }
                catalog.append(d)
        return catalog

    def on_post(self, req, resp):
        body = req.stream.read().decode()
        credentials = json.loads(body)
        token_details, user = auth.get_new_token_v3(credentials)
        token_id = base64.b64encode(aes.encode_aes(json.dumps(token_details)))

        access = get_access_v3(token_id, token_details,
                               user['id'], user['username'])
        # Add catalog to the access data
        catalog = self._build_catalog(token_details, user['id'])
        access['token']['catalog'] = catalog

        resp.status = 201
        resp.set_header('X-Subject-Token', str(token_id))
        # V2 APIs return the body in 'access' keypair but V3 APIs do not
        # resp.body = {'access': access}
        resp.body = access

    def on_get(self, req, resp):
        toks = [req.get_header('X-Auth-Token'),  # the token who sent request
                req.get_header('X-Subject-Token')]  # the token to be validated
        token_id_driver = identity.token_id_driver()
        tokens = identity.token_driver()
        validated_tokens = []
        for token_id in toks:
            token = token_id_driver.token_from_id(token_id)
            tokens.validate_token(token)
            validated_tokens.append(token)

        access = get_access_v3(toks[1], validated_tokens[1],
                               tokens.user_id(validated_tokens[1]),
                               tokens.username(validated_tokens[1]))

        if 'nocatalog' not in req.query_string:
            # Add catalog to the access data
            catalog = self._build_catalog(validated_tokens[1],
                                          tokens.user_id(validated_tokens[1]))
            access['token']['catalog'] = catalog

        resp.status = 200
        resp.set_header('X-Auth-Token', toks[0])
        resp.set_header('X-Subject-Token', toks[1])
        # V2 APIs return the body in 'access' keypair but V3 APIs do not
        # resp.body = {'access': access}
        resp.body = access

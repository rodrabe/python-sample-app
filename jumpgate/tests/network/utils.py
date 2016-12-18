from falcon.testing import helpers


def get_env(client, tenant_id=999999, **kwargs):
    env = helpers.create_environ(**kwargs)
    env['auth'] = {'tenant_id': tenant_id}
    return env

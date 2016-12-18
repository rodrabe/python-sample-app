

class Index(object):
    def __init__(self, app):
        self.app = app

    def on_get(self, req, resp):
        versions = [{
            'id': 'v2.0',
            'links': [{
                'href': self.app.get_endpoint_url('network', req, 'v2_detail'),
                'rel': 'self'
            }],
            'status': 'CURRENT'
        }]

        resp.body = {'versions': versions}

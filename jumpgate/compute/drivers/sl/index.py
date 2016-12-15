

class IndexV2(object):
    def __init__(self, app):
        self.app = app

    def on_get(self, req, resp):
        versions = [{
            'id': 'v2.0',
            'links': [{
                'href': self.app.get_endpoint_url('compute', req, 'v2_detail'),
                'rel': 'self'
            }],
            'status': 'CURRENT',
            'media-types': [
                {
                    'base': 'application/json',
                    'type': 'application/vnd.openstack.compute.v1.0+json',
                }
            ],
            "updated": "2011-01-21T11:33:21Z",
        },
        ]

        resp.body = {'versions': versions}

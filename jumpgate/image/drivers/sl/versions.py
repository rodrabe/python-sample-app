"""
Defines handlers for the image endpoint version routes.
"""


class Index(object):
    def __init__(self, app):
        self.app = app

    def on_get(self, req, resp):
        # http://developer.openstack.org/api-ref/image/versions/index.html
        versions = [
            {
                "id": "v2.0",
                "links": [
                    {
                        "href": self.app.get_endpoint_url(
                            'image', req, 'v2_version'),
                        "rel": "self"
                    }
                ],
                "status": "CURRENT"
            },
            {
                "id": "v1.0",
                "links": [
                    {
                        "href": self.app.get_endpoint_url(
                            'image', req, 'v1_version'),
                        "rel": "self"
                    }
                ],
                "status": "SUPPORTED",
            },
        ]

        resp.body = {'versions': versions}

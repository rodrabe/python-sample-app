

class Index(object):
    def __init__(self, app):
        self.app = app

    # TODO(mriedem): we're going to drop the v1 API which is why it's not
    # listed here.
    def on_get(self, req, resp):
        versions = [{
            "status": "CURRENT",
            "links": [
                {
                    "href": self.app.get_endpoint_url(
                        'volume', req, 'v2_detail'),
                    "rel": "self"
                },
            ],
            "min_version": "",
            "version": "",
            "id": "v2.0"
        }
        ]

        resp.body = {'versions': versions}
